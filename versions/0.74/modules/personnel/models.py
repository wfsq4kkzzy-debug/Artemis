"""
Personnel Models - Modely pro modul personální agendy
"""

from datetime import datetime
from core import db


class ZamestnanecAOON(db.Model):
    """Model pro zaměstnance a osoby vykonávající OON"""
    __tablename__ = 'zamestnanec_oon'
    
    id = db.Column(db.Integer, primary_key=True)
    jmeno = db.Column(db.String(100), nullable=False)
    prijmeni = db.Column(db.String(100), nullable=False)
    typ = db.Column(db.String(20), nullable=False)  # 'zamestnanec', 'brigadnik', 'oon'
    ic_dph = db.Column(db.String(20), nullable=True)
    pozice = db.Column(db.String(100), nullable=True)
    uvazek = db.Column(db.Numeric(5, 2), nullable=True, default=100)  # Úvazek v % (100% = plný)
    hodinova_sazba = db.Column(db.Numeric(10, 2), nullable=True)
    mesicni_plat = db.Column(db.Numeric(12, 2), nullable=True)
    datum_zapojeni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    datum_ukonceni = db.Column(db.DateTime, nullable=True)
    aktivni = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<ZamestnanecAOON {self.jmeno} {self.prijmeni} - {self.typ}>'
    
    @property
    def jmeno_plne(self):
        return f'{self.jmeno} {self.prijmeni}'
