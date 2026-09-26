"""Parameterized SQL, scoped workspaces, and atomic booking for SQLite/PostgreSQL."""
from contextlib import contextmanager
import hashlib
import sqlite3
import uuid
from pathlib import Path

SCHEMA = '''CREATE TABLE IF NOT EXISTS events (
 id TEXT PRIMARY KEY, workspace TEXT NOT NULL, title TEXT NOT NULL,
 start_ms BIGINT NOT NULL, end_ms BIGINT NOT NULL,
 request_key TEXT NOT NULL, fingerprint TEXT NOT NULL,
 CHECK (end_ms > start_ms), UNIQUE (workspace, request_key));'''

class BookingConflict(Exception):
    pass

class Store:
    def __init__(self, url: str):
        self.url = url
        self.postgres = url.startswith(('postgresql://', 'postgres://'))
        self.path = url.removeprefix('sqlite:///')
        if not self.postgres:
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            conn.execute(SCHEMA)
            conn.execute('CREATE INDEX IF NOT EXISTS events_workspace_start ON events(workspace, start_ms)')

    @contextmanager
    def connection(self):
        if self.postgres:
            import psycopg
            from psycopg.rows import dict_row
            conn = psycopg.connect(self.url, row_factory=dict_row)
        else:
            conn = sqlite3.connect(self.path, timeout=10)
            conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, conn, query, params=()):
        return conn.execute(query.replace('?', '%s') if self.postgres else query, params)

    def lock(self, conn, workspace):
        if self.postgres:
            lock_id = int.from_bytes(hashlib.sha256(workspace.encode()).digest()[:8], 'big', signed=True)
            conn.execute('SELECT pg_advisory_xact_lock(%s)', (lock_id,))
        else:
            conn.execute('BEGIN IMMEDIATE')

    @staticmethod
    def public(row):
        return {'id': row['id'], 'title': row['title'], 'start': row['start_ms'], 'end': row['end_ms']}

    def list_events(self, workspace):
        with self.connection() as conn:
            return [self.public(r) for r in self.execute(conn,
                'SELECT * FROM events WHERE workspace=? ORDER BY start_ms LIMIT 500', (workspace,))]

    def book(self, workspace, title, start, end, request_key):
        fingerprint = hashlib.sha256(f'{title}\0{start}\0{end}'.encode()).hexdigest()
        with self.connection() as conn:
            self.lock(conn, workspace)
            existing = self.execute(conn, 'SELECT * FROM events WHERE workspace=? AND request_key=?', (workspace, request_key)).fetchone()
            if existing:
                if existing['fingerprint'] != fingerprint:
                    raise BookingConflict('This request key was already used for a different booking.')
                return self.public(existing), True
            conflicts = self.execute(conn, 'SELECT id FROM events WHERE workspace=? AND start_ms<? AND end_ms>? LIMIT 1', (workspace, end, start)).fetchone()
            if conflicts:
                raise BookingConflict('That slot is no longer free. Find another time and try again.')
            count = self.execute(conn, 'SELECT COUNT(*) AS count FROM events WHERE workspace=?', (workspace,)).fetchone()['count']
            if count >= 500:
                raise BookingConflict('This workspace has reached its 500-event limit. Delete an event first.')
            row = {'id': str(uuid.uuid4()), 'title': title, 'start': start, 'end': end}
            self.execute(conn, 'INSERT INTO events (id,workspace,title,start_ms,end_ms,request_key,fingerprint) VALUES (?,?,?,?,?,?,?)', (row['id'],workspace,title,start,end,request_key,fingerprint))
            return row, False

    def delete(self, workspace, event_id):
        with self.connection() as conn:
            self.lock(conn, workspace)
            return self.execute(conn, 'DELETE FROM events WHERE workspace=? AND id=?', (workspace,event_id)).rowcount > 0
