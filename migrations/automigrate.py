from alembic import command
from alembic.config import Config
import os


def run_migrations():
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "../alembic.ini"))
    command.upgrade(alembic_cfg, "head")
