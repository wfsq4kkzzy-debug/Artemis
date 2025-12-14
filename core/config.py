import os

basedir = os.path.abspath(os.path.dirname(__file__))
# Jdi o úroveň výš (z core/ do root)
rootdir = os.path.abspath(os.path.join(basedir, '..'))

class Config:
    """Základní konfigurace"""
    # Databáze v root adresáři projektu (ne v core/)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(rootdir, 'library_budget.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'dev-secret-key-zmenit-na-produkcni'
    
class DevelopmentConfig(Config):
    """Vývojová konfigurace"""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testovací konfigurace"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    """Produkční konfigurace"""
    DEBUG = False
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
