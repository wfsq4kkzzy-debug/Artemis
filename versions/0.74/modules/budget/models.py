"""
Budget Models - Modely pro modul rozpočtu
"""

from datetime import datetime
from core import db


class UctovaSkupina(db.Model):
    """Model pro účtovou skupinu (kategorii)"""
    __tablename__ = 'uctova_skupina'
    
    id = db.Column(db.Integer, primary_key=True)
    ucet = db.Column(db.String(10), unique=True, nullable=False, index=True)
    nazev = db.Column(db.String(200), nullable=False)
    typ = db.Column(db.String(20), nullable=False)  # 'naklad' nebo 'vynos'
    
    # Relace
    polozky = db.relationship('RozpoctovaPolozka', backref='uctova_skupina', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<UctovaSkupina {self.ucet} - {self.nazev}>'
    
    def __str__(self):
        return f'{self.ucet} - {self.nazev}'


class RozpoctovaPolozka(db.Model):
    """Model pro rozpočtovou položku"""
    __tablename__ = 'rozpoctova_polozka'
    
    id = db.Column(db.Integer, primary_key=True)
    rok = db.Column(db.Integer, nullable=False, default=2026, index=True)
    uctova_skupina_id = db.Column(db.Integer, db.ForeignKey('uctova_skupina.id'), nullable=False)
    analyticky_ucet = db.Column(db.String(10), nullable=False)  # např. "30", "31"
    nazev = db.Column(db.String(300), nullable=False)
    rozpocet = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    poznamka = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<RozpoctovaPolozka {self.nazev} - {self.rozpocet}>'
    
    def __str__(self):
        return f'{self.nazev} ({self.rozpocet} Kč)'
    
    @property
    def rozpocet_float(self):
        """Vrátí rozpočet jako float"""
        return float(self.rozpocet) if self.rozpocet else 0.0
    
    def vydaje_k_datu(self, k_datu=None):
        """Vrátí výdaje do zadaného data (včetně). Pokud k_datu není zadáno, použije se aktuální datum."""
        from datetime import datetime, date
        if k_datu is None:
            k_datu = datetime.utcnow()
        elif isinstance(k_datu, date):
            k_datu = datetime.combine(k_datu, datetime.max.time())
        
        return [v for v in self.vydaje if v.datum <= k_datu]
    
    @property
    def vydaje_k_aktualnimu_datu(self):
        """Vrátí výdaje do aktuálního data (včetně)"""
        return self.vydaje_k_datu()
    
    @property
    def celkove_vydaje_k_datu(self, k_datu=None):
        """Vrátí celkové výdaje do zadaného data. Pokud k_datu není zadáno, použije se aktuální datum."""
        vydaje = self.vydaje_k_datu(k_datu)
        return sum(float(v.castka) for v in vydaje)
    
    @property
    def celkove_vydaje_aktualni(self):
        """Vrátí celkové výdaje do aktuálního data"""
        return self.celkove_vydaje_k_datu()
    
    @property
    def zbytek_aktualni(self):
        """Vrátí zbývající rozpočet k aktuálnímu datu"""
        return float(self.rozpocet) - self.celkove_vydaje_aktualni


class Vydaj(db.Model):
    """Model pro jednotlivý výdaj"""
    __tablename__ = 'vydaj'
    
    id = db.Column(db.Integer, primary_key=True)
    rozpoctova_polozka_id = db.Column(db.Integer, db.ForeignKey('rozpoctova_polozka.id'), nullable=False)
    castka = db.Column(db.Numeric(12, 2), nullable=False)
    datum = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    popis = db.Column(db.String(300), nullable=True)
    cis_faktury = db.Column(db.String(50), nullable=True)
    dodavatel = db.Column(db.String(200), nullable=True)
    
    # Relace
    polozka = db.relationship('RozpoctovaPolozka', backref='vydaje')
    
    def __repr__(self):
        return f'<Vydaj {self.castka} Kč - {self.datum}>'
    
    @property
    def castka_float(self):
        """Vrátí částku jako float"""
        return float(self.castka) if self.castka else 0.0
