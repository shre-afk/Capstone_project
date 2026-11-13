"""Read local database credentials without storing passwords in source code."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name('.env'))

MYSQL_SETTINGS = {
    'host': os.environ.get('ADVISOR_DB_HOST', '127.0.0.1'),
    'port': int(os.environ.get('ADVISOR_DB_PORT', '3306')),
    'user': os.environ.get('ADVISOR_DB_USER', 'advisor_app'),
    'password': os.environ.get('ADVISOR_DB_PASSWORD', ''),
    'database': os.environ.get('ADVISOR_DB_NAME', 'energy_advisor'),
}
