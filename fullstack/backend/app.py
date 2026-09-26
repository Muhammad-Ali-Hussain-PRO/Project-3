"""ChronosAI v2 API. Run on loopback or behind TLS; no external calendar access."""
from datetime import datetime, timezone
from pathlib import Path
from contextlib import asynccontextmanager
import hashlib
import os
import re
import time
import logging
from fastapi import FastAPI, HTTPException, Header, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, AwareDatetime, field_validator, model_validator
from .store import Store, BookingConflict
from .engine import first_available

class Booking(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    start: AwareDatetime
    end: AwareDatetime
    request_key: str = Field(min_length=16, max_length=100, pattern=r'^[A-Za-z0-9_-]+$')

    @field_validator('title')
    @classmethod
    def clean_title(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Give this event a title.')
        return value

    @model_validator(mode='after')
    def valid_interval(self):
        minutes = (self.end - self.start).total_seconds() / 60
        if not 5 <= minutes <= 480:
            raise ValueError('Events must last between 5 minutes and 8 hours.')
        return self

class SearchWindow(BaseModel):
    earliest: AwareDatetime
    latest: AwareDatetime
    duration_minutes: int = Field(ge=5, le=480)

    @model_validator(mode='after')
    def valid_window(self):
        seconds = (self.latest - self.earliest).total_seconds()
        if seconds <= 0 or seconds > 7 * 86400:
            raise ValueError('Choose a search window between one minute and seven days.')
        return self


def ms(value):
    return int(value.astimezone(timezone.utc).timestamp() * 1000)

def workspace(authorization: str | None):
    if not authorization or not re.fullmatch(r'Bearer [A-Za-z0-9_-]{32,128}', authorization):
        raise HTTPException(401, 'A workspace token is required.')
    return hashlib.sha256(authorization[7:].encode()).hexdigest()


def create_app(database_url=None, static_dir=None):
    url = database_url or os.getenv('DATABASE_URL', 'sqlite:///data/chronos.db')
    @asynccontextmanager
    async def lifespan(app):
        app.state.store = Store(url)
        yield
    app = FastAPI(title='ChronosAI Workspace', version='2.0.0', lifespan=lifespan)

    @app.middleware('http')
    async def request_timing(request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        response.headers['Server-Timing'] = f'app;dur={(time.perf_counter()-started)*1000:.2f}'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        if request.url.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/api/health')
    def health():
        return {'status':'ok','storage':'postgresql' if app.state.store.postgres else 'sqlite','version':'2.0.0'}

    @app.get('/api/events')
    def events(authorization: str | None = Header(default=None)):
        return {'events':app.state.store.list_events(workspace(authorization))}

    @app.post('/api/suggestions')
    def suggest(data: SearchWindow, authorization: str | None = Header(default=None)):
        events = app.state.store.list_events(workspace(authorization))
        slot = first_available(ms(data.earliest),ms(data.latest),data.duration_minutes,events)
        if not slot:
            raise HTTPException(409,'No free slot fits this window. Extend the window or shorten the event.')
        return {'start':slot.start,'end':slot.end,'conflicts':slot.conflicts,'requires_confirmation':True}

    @app.post('/api/events', status_code=201)
    def book(data: Booking, response: Response, authorization: str | None = Header(default=None)):
        try:
            event, replay = app.state.store.book(workspace(authorization),data.title,ms(data.start),ms(data.end),data.request_key)
            response.status_code = 200 if replay else 201
            return {'event':event,'replayed':replay}
        except BookingConflict as exc:
            raise HTTPException(409,str(exc)) from exc

    @app.delete('/api/events/{event_id}', status_code=204)
    def delete(event_id: str, authorization: str | None = Header(default=None)):
        if not app.state.store.delete(workspace(authorization),event_id):
            raise HTTPException(404,'Event not found in this workspace.')
        return Response(status_code=204)

    directory = Path(static_dir or os.getenv('STATIC_DIR', str(Path(__file__).resolve().parents[1] / 'frontend/dist')))
    if directory.is_dir():
        app.mount('/',StaticFiles(directory=str(directory),html=True),name='web')
    return app

app = create_app()
