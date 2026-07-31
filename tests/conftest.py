import os
import sys
import tempfile
import pytest

# Ensure root project directory is in sys.path for test discovery
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database.db as db_module

@pytest.fixture(autouse=True)
def use_test_db(tmp_path):
    """Isolates each test by pointing db_module.DB_PATH to a temporary database file."""
    test_db_path = str(tmp_path / "test_spendly.db")
    original_db_path = db_module.DB_PATH
    db_module.DB_PATH = test_db_path
    
    # Initialize and seed fresh test DB
    db_module.init_db()
    db_module.seed_db()
    
    yield test_db_path
    
    db_module.DB_PATH = original_db_path

