"""Start the server with:  python run.py    and then open http://127.0.0.1:5000"""
 
import os
 
from app import create_app
from config import MYSQL_SETTINGS
from repository import InMemoryRepository, MySQLRepository
 
if os.environ.get("USE_MEMORY_DB") == "1":
    repository = InMemoryRepository.with_sample_data()    # emergency mode, no MySQL needed
else:
    repository = MySQLRepository(**MYSQL_SETTINGS)
 
app = create_app(repository)
 
if __name__ == "__main__":
    app.run(debug=True)