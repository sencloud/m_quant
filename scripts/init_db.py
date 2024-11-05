import sys
import os

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from backend.database.schema import init_db

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
