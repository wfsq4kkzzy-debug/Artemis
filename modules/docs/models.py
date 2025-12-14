"""
Docs Models - Modely pro modul dokumentace a logy změn
"""

from datetime import datetime
from core import db


class ChangeLog(db.Model):
    """Model pro logy změn v systému"""
    __tablename__ = 'changelog'
    
    id = db.Column(db.Integer, primary_key=True)
    datum = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    verze = db.Column(db.String(20), nullable=True)  # Např. '0.76'
    typ = db.Column(db.String(20), nullable=False, default='zmena')  # 'zmena', 'oprava', 'pridano', 'odstraneno'
    modul = db.Column(db.String(50), nullable=True)  # 'budget', 'projects', 'services', atd.
    nadpis = db.Column(db.String(200), nullable=False)
    popis = db.Column(db.Text, nullable=False)
    autor = db.Column(db.String(100), nullable=True)
    aktivni = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<ChangeLog {self.verze} - {self.nadpis}>'
