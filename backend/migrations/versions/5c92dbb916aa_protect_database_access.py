"""Block direct browser / Supabase Data API access to application tables.

Only the server database owner may bypass RLS. Identity is enforced in FastAPI.
"""

from alembic import op

revision = "5c92dbb916aa"
down_revision = "3177dba797e8"
branch_labels = None
depends_on = None
TABLES = (
    "inventory_users",
    "inventory_sessions",
    "inventory_login_attempts",
    "inventory_products",
    "inventory_observations",
    "inventory_movements",
)


def upgrade():
    if op.get_bind().dialect.name != "postgresql":
        return
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"REVOKE ALL ON TABLE {table} FROM PUBLIC")
        for role in ("anon", "authenticated"):
            op.execute(f"""DO $$ BEGIN
              IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{role}') THEN
                EXECUTE 'REVOKE ALL ON TABLE {table} FROM {role}';
              END IF;
            END $$""")


def downgrade():
    if op.get_bind().dialect.name == "postgresql":
        for table in TABLES:
            op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
