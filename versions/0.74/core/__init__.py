"""
Core - Základní funkce aplikace
Obsahuje konfiguraci, databázi a společné utility
"""

from flask_sqlalchemy import SQLAlchemy

# Globální instance databáze
db = SQLAlchemy()
