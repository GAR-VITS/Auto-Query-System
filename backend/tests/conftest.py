import sys
from pathlib import Path
import pytest

# Ensure backend and app directory are on sys.path
backend_dir = Path(__file__).resolve().parent.parent
app_dir = backend_dir / "app"
for d in [str(backend_dir), str(app_dir)]:
    if d not in sys.path:
        sys.path.insert(0, d)

from app.config import get_settings
from app.db.session import init_database

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_database()
