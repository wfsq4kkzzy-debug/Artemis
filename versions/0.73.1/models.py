from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

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
            # Pokud je to date, převedeme na datetime na konec dne
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


# ============================================================================
# NOVÉ MODELY PRO PROJEKTOVÝ SYSTÉM
# ============================================================================

class Projekt(db.Model):
    """Model pro projekt"""
    __tablename__ = 'projekt'
    
    id = db.Column(db.Integer, primary_key=True)
    nazev = db.Column(db.String(300), nullable=False, index=True)
    popis = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='planovani')  # 'planovani', 'rozpracovani', 'ukonceny', 'pozastaveny'
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    datum_zahajeni = db.Column(db.DateTime, nullable=True)
    datum_ukonceni_planovane = db.Column(db.DateTime, nullable=True)
    datum_ukonceni_skutecne = db.Column(db.DateTime, nullable=True)
    vedouci = db.Column(db.String(200), nullable=True)
    poznamka = db.Column(db.Text, nullable=True)
    
    # Relace
    budgets = db.relationship('BudgetProjektu', backref='projekt', lazy=True, cascade='all, delete-orphan')
    vydaje = db.relationship('VydajProjektu', backref='projekt', lazy=True, cascade='all, delete-orphan')
    terminy = db.relationship('Termin', backref='projekt', lazy=True, cascade='all, delete-orphan')
    zpravy = db.relationship('Zprava', backref='projekt', lazy=True, cascade='all, delete-orphan')
    znalosti = db.relationship('Znalost', backref='projekt', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Projekt {self.nazev}>'
    
    @property
    def celkovy_rozpocet(self):
        """Vrátí celkový rozpočet projektu"""
        total = sum(float(b.castka) for b in self.budgets)
        return total
    
    @property
    def celkove_vydaje(self):
        """Vrátí celkové výdaje projektu"""
        total = sum(float(v.castka) for v in self.vydaje)
        return total
    
    @property
    def zbytek(self):
        """Vrátí zbývající rozpočet"""
        return self.celkovy_rozpocet - self.celkove_vydaje


class BudgetProjektu(db.Model):
    """Model pro rozpočtovou položku v projektu"""
    __tablename__ = 'budget_projektu'
    
    id = db.Column(db.Integer, primary_key=True)
    projekt_id = db.Column(db.Integer, db.ForeignKey('projekt.id'), nullable=False)
    kategorie = db.Column(db.String(100), nullable=False)  # např. 'personál', 'materiál', 'služby'
    popis = db.Column(db.String(300), nullable=False)
    castka = db.Column(db.Numeric(12, 2), nullable=False)
    poznamka = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<BudgetProjektu {self.popis} - {self.castka}>'


class VydajProjektu(db.Model):
    """Model pro výdaj v projektu"""
    __tablename__ = 'vydaj_projektu'
    
    id = db.Column(db.Integer, primary_key=True)
    projekt_id = db.Column(db.Integer, db.ForeignKey('projekt.id'), nullable=False)
    kategorie = db.Column(db.String(100), nullable=False)  # kategorie jako v BudgetProjektu
    popis = db.Column(db.String(300), nullable=False)
    castka = db.Column(db.Numeric(12, 2), nullable=False)
    datum = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    cis_faktury = db.Column(db.String(50), nullable=True)
    dodavatel = db.Column(db.String(200), nullable=True)
    
    def __repr__(self):
        return f'<VydajProjektu {self.popis} - {self.castka}>'


class Termin(db.Model):
    """Model pro termín/milestone v projektu"""
    __tablename__ = 'termin'
    
    id = db.Column(db.Integer, primary_key=True)
    projekt_id = db.Column(db.Integer, db.ForeignKey('projekt.id'), nullable=False)
    nazev = db.Column(db.String(300), nullable=False)
    datum_planovane = db.Column(db.DateTime, nullable=False)
    datum_skutecne = db.Column(db.DateTime, nullable=True)
    popis = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='planovano')  # 'planovano', 'probihajici', 'splneno', 'zmeska'
    zodpovedny = db.Column(db.String(200), nullable=True)
    
    def __repr__(self):
        return f'<Termin {self.nazev} - {self.datum_planovane}>'


class Zprava(db.Model):
    """Model pro zprávu/komunikaci v projektu"""
    __tablename__ = 'zprava'
    
    id = db.Column(db.Integer, primary_key=True)
    projekt_id = db.Column(db.Integer, db.ForeignKey('projekt.id'), nullable=False)
    autor = db.Column(db.String(200), nullable=False)
    obsah = db.Column(db.Text, nullable=False)
    datum = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    typ = db.Column(db.String(20), nullable=False, default='poznamka')  # 'poznamka', 'upozorneni', 'aktualizace'
    
    def __repr__(self):
        return f'<Zprava od {self.autor} - {self.datum}>'


class Znalost(db.Model):
    """Model pro znalostní položku/dokumentaci k projektu"""
    __tablename__ = 'znalost'
    
    id = db.Column(db.Integer, primary_key=True)
    projekt_id = db.Column(db.Integer, db.ForeignKey('projekt.id'), nullable=False)
    nazev = db.Column(db.String(300), nullable=False)
    obsah = db.Column(db.Text, nullable=False)
    kategorie = db.Column(db.String(100), nullable=True)  # např. 'procedura', 'pozadavek', 'poznatek'
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    autor = db.Column(db.String(200), nullable=True)
    
    def __repr__(self):
        return f'<Znalost {self.nazev}>'

