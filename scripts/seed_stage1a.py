"""Seed the fixed PILOT-001 synthetic facts into local PostgreSQL."""

from app.config import get_settings
from app.infrastructure.database.simulator_seed import seed_simulator_facts
from sqlalchemy import create_engine


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    try:
        seed_simulator_facts(engine)
    finally:
        engine.dispose()
    print("stage1a_seed=pass organizations=2 devices=6 synthetic_only=true")


if __name__ == "__main__":
    main()
