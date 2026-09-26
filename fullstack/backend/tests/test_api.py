import os, uuid, random
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.store import Store, BookingConflict
from backend.engine import first_available

def payload(start='2026-10-01T14:00:00Z',end='2026-10-01T15:00:00Z',title='Focus',key=None):
 return {'title':title,'start':start,'end':end,'request_key':key or uuid.uuid4().hex}
@pytest.fixture
def database_url(tmp_path):return os.getenv('TEST_DATABASE_URL','sqlite:///'+str(tmp_path/'test.db'))
@pytest.fixture
def client(database_url):
 with TestClient(create_app(database_url)) as c:
  c.headers.update({'Authorization':'Bearer '+uuid.uuid4().hex+uuid.uuid4().hex});yield c

def test_health_and_timing(client):
 r=client.get('/api/health');assert r.status_code==200;assert 'app;dur=' in r.headers['server-timing'];assert r.json()['storage'] in ['sqlite','postgresql']
def test_create_list_delete(client):
 r=client.post('/api/events',json=payload());assert r.status_code==201
 e=r.json()['event'];assert client.get('/api/events').json()['events']==[e]
 assert client.delete('/api/events/'+e['id']).status_code==204
 assert client.get('/api/events').json()['events']==[]
def test_missing_auth(client):assert client.get('/api/events',headers={'Authorization':''}).status_code==401
def test_workspace_isolation(client):
 e=client.post('/api/events',json=payload()).json()['event'];other={'Authorization':'Bearer '+uuid.uuid4().hex+uuid.uuid4().hex}
 assert client.get('/api/events',headers=other).json()['events']==[]
 assert client.delete('/api/events/'+e['id'],headers=other).status_code==404
 assert len(client.get('/api/events').json()['events'])==1
def test_overlap_and_adjacent_boundary(client):
 assert client.post('/api/events',json=payload()).status_code==201
 assert client.post('/api/events',json=payload('2026-10-01T14:30:00Z','2026-10-01T15:30:00Z')).status_code==409
 assert client.post('/api/events',json=payload('2026-10-01T15:00:00Z','2026-10-01T15:30:00Z')).status_code==201
def test_retry_is_idempotent(client):
 data=payload();a=client.post('/api/events',json=data);b=client.post('/api/events',json=data)
 assert a.status_code==201 and b.status_code==200
 assert b.json()['replayed'] and a.json()['event']==b.json()['event']
 assert len(client.get('/api/events').json()['events'])==1
def test_reused_key_with_different_payload(client):
 data=payload();client.post('/api/events',json=data);data['title']='Different'
 assert client.post('/api/events',json=data).status_code==409
def test_preview_does_not_book(client):
 r=client.post('/api/suggestions',json={'earliest':'2026-10-01T14:00:00Z','latest':'2026-10-01T17:00:00Z','duration_minutes':60})
 assert r.status_code==200 and r.json()['requires_confirmation']
 assert client.get('/api/events').json()['events']==[]
def test_preview_explains_conflict(client):
 client.post('/api/events',json=payload())
 r=client.post('/api/suggestions',json={'earliest':'2026-10-01T14:30:00Z','latest':'2026-10-01T17:00:00Z','duration_minutes':30})
 assert r.status_code==200 and len(r.json()['conflicts'])==1
 assert r.json()['start']==int(datetime(2026,10,1,15,tzinfo=timezone.utc).timestamp()*1000)
def test_stale_preview_rechecked(client):
 body={'earliest':'2026-10-01T14:00:00Z','latest':'2026-10-01T17:00:00Z','duration_minutes':60}
 assert client.post('/api/suggestions',json=body).status_code==200
 client.post('/api/events',json=payload());assert client.post('/api/events',json=payload()).status_code==409
def test_full_window(client):
 client.post('/api/events',json=payload())
 assert client.post('/api/suggestions',json={'earliest':'2026-10-01T14:00:00Z','latest':'2026-10-01T15:00:00Z','duration_minutes':30}).status_code==409
@pytest.mark.parametrize('changes',[{'title':''},{'title':'   '},{'title':'a'*121},{'start':'2026-10-01T14:00:00'},{'end':'2026-10-01T13:00:00Z'},{'end':'2026-10-01T14:01:00Z'},{'end':'2026-10-02T15:00:00Z'},{'request_key':'bad'}])
def test_invalid_booking(client,changes):
 data=payload();data.update(changes);assert client.post('/api/events',json=data).status_code==422
@pytest.mark.parametrize('changes',[{'duration_minutes':0},{'duration_minutes':481},{'latest':'2026-09-30T14:00:00Z'},{'latest':'2026-10-15T14:00:00Z'},{'earliest':'2026-10-01T14:00:00'}])
def test_invalid_window(client,changes):
 data={'earliest':'2026-10-01T14:00:00Z','latest':'2026-10-01T17:00:00Z','duration_minutes':30};data.update(changes)
 assert client.post('/api/suggestions',json=data).status_code==422
def test_timezone_offsets(client):
 assert client.post('/api/events',json=payload('2026-10-01T09:00:00-05:00','2026-10-01T10:00:00-05:00')).status_code==201
 assert client.post('/api/events',json=payload()).status_code==409
def test_sql_metacharacters_are_literal(client):
 title="Planning'); DROP TABLE events; --"
 assert client.post('/api/events',json=payload(title=title)).status_code==201
 assert client.get('/api/events').json()['events'][0]['title']==title
def test_persists_after_restart(database_url):
 h={'Authorization':'Bearer '+uuid.uuid4().hex+uuid.uuid4().hex}
 with TestClient(create_app(database_url)) as c:assert c.post('/api/events',json=payload(),headers=h).status_code==201
 with TestClient(create_app(database_url)) as c:assert len(c.get('/api/events',headers=h).json()['events'])==1
def test_atomic_conflicting_bookings(database_url):
 store=Store(database_url);scope=uuid.uuid4().hex
 def submit(i):
  try:store.book(scope,'Focus',0,3600000,str(i));return 'booked'
  except BookingConflict:return 'conflict'
 with ThreadPoolExecutor(max_workers=5) as pool:results=list(pool.map(submit,range(5)))
 assert results.count('booked')==1 and results.count('conflict')==4
 assert len(store.list_events(scope))==1
def test_atomic_duplicate_retries(database_url):
 store=Store(database_url);scope=uuid.uuid4().hex
 def submit(_):return store.book(scope,'Focus',0,3600000,'same-key')
 with ThreadPoolExecutor(max_workers=5) as pool:results=list(pool.map(submit,range(5)))
 assert len({e['id'] for e,r in results})==1 and sum(not r for e,r in results)==1
def test_randomized_engine_against_minute_scan():
 rng=random.Random(17)
 for _ in range(200):
  events=[{'title':'Busy','start':(s:=rng.randrange(0,200))*60000,'end':(s+rng.randrange(1,60))*60000} for _ in range(10)]
  duration=rng.randrange(5,90);result=first_available(0,300*60000,duration,events)
  expected=next((s*60000 for s in range(301-duration) if all(not(s*60000<e['end'] and (s+duration)*60000>e['start']) for e in events)),None)
  assert (result.start if result else None)==expected
