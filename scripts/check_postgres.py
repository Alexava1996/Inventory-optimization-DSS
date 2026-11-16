"""Read-only verification after migrations, intended for PostgreSQL CI."""
from sqlalchemy import text
from app.db import engine
with engine.connect() as db:
    tables = db.execute(text("SELECT relname, relrowsecurity FROM pg_class WHERE relname LIKE 'inventory_%' AND relkind='r' ORDER BY relname")).all()
    assert len(tables) == 6 and all(row[1] for row in tables), tables
    for role in ('anon', 'authenticated'):
        exists = db.scalar(text('SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=:role)'), {'role': role})
        if exists:
            for table, _ in tables:
                assert not db.scalar(text("SELECT has_table_privilege(:role, :table, 'SELECT')"), {'role': role, 'table': table})
print('PostgreSQL: RLS attiva su 6 tabelle; nessuna lettura concessa ai ruoli browser presenti.')
