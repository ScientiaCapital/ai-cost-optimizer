"""Database utilities package."""
# NOTE: There's a naming conflict - app/database.py (SQLite module) vs app/database/ (PostgreSQL package)
# We import CostTracker by accessing the module file directly using importlib
import importlib.util
import sys
from pathlib import Path

# Load database.py as a module to avoid circular import
db_module_path = Path(__file__).parent.parent / "database.py"
spec = importlib.util.spec_from_file_location("app.database_sqlite", db_module_path)
database_sqlite = importlib.util.module_from_spec(spec)
sys.modules["app.database_sqlite"] = database_sqlite
spec.loader.exec_module(database_sqlite)

# Re-export classes and functions from the SQLite module
CostTracker = database_sqlite.CostTracker
create_routing_metrics_table = database_sqlite.create_routing_metrics_table

__all__ = ['CostTracker', 'create_routing_metrics_table']
