"""Run from the repository root:

python -m hometask_assignments.hometask3.subsystem3_advisor.run
"""

from .app import create_app
from .config import MYSQL_SETTINGS
from .repository import EnergyRepository

app = create_app(EnergyRepository(MYSQL_SETTINGS))

if __name__ == '__main__':
    app.run(port=5002)
