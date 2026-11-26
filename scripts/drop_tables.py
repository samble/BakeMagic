"""Drop every table and enum type in the app's database (all data is lost).

Used by `make db-reset`, which re-runs the migrations afterwards. Asks for
confirmation unless --yes is passed.
"""

import sys

from sqlalchemy import MetaData, text

from app.db import engine


def main() -> int:
    target = engine.url.render_as_string(hide_password=True)
    if "--yes" not in sys.argv:
        answer = input(f"Drop ALL tables and data in {target}? Type 'yes' to continue: ")
        if answer.strip().lower() != "yes":
            print("Aborted; nothing was dropped.")
            return 1

    with engine.begin() as conn:
        metadata = MetaData()
        metadata.reflect(conn)  # includes alembic_version
        metadata.drop_all(conn)
        # Postgres keeps enum types (e.g. orderstatus) after their tables are dropped.
        enums = conn.execute(
            text(
                "SELECT t.typname FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace "
                "WHERE n.nspname = current_schema() AND t.typtype = 'e'"
            )
        ).scalars()
        for name in enums.all():
            conn.execute(text(f'DROP TYPE "{name}"'))

    print(f"Dropped {len(metadata.tables)} tables in {target}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
