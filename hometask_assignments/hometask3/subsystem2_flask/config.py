"""Settings - Database login comes from environment variables, so no password ends up on GitHub"""
 
import os
 
MYSQL_SETTINGS = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "energy_app"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DATABASE", "energy_hometask"),
}
 
# the same assumptions as capstone's config.toml
EUR_PER_KWH = 0.30
CO2_KG_PER_KWH = 0.38