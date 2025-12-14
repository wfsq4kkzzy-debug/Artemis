"""
Nové modely pro modul rozpočtu - flexibilní systém s více rozpočty
PŘEPRACOVÁVÁ SE - v této verzi pouze základní struktura
"""

from datetime import datetime
from decimal import Decimal
from core import db


class Budget(db.Model):
    """Rozpočet - může být hlavní, projektový, roční, měsíční"""
    __tablename__ = 'budget'
    
    id = db.Column(db.Integer, primary_key=True)
    nazev = db.Column(db.String(200), nullable=False)
    popis = db.Column(db.Text, nullable=True)
    typ = db.Column(db.String(20), nullable=False, default='hlavni')  # 'hlavni', 'projektovy', 'rocni', 'mesicni'
    rok = db.Column(db.Integer, nullable=False, default=2026)
    mesic = db.Column(db.Integer, nullable=True)  # 1-12 pro měsíční rozpočty
    castka_celkem = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    aktivni = db.Column(db.Boolean, default=True)
    hlavni = db.Column(db.Boolean, default=False)  # Pouze jeden může být hlavní
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    datum_aktualizace = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    
    # Relace
    polozky = db.relationship('BudgetItem', backref='budget', lazy=True, cascade='all, delete-orphan')
    vydaje = db.relationship('Expense', backref='budget', lazy=True, cascade='all, delete-orphan')
    mesicni_prehledy = db.relationship('MonthlyBudget', backref='budget', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Budget {self.nazev} - {self.typ}>'
    
    @property
    def castka_celkem_float(self):
        return float(self.castka_celkem) if self.castka_celkem else 0.0
    
    @property
    def celkove_vydaje(self):
        """Celkové výdaje v rozpočtu (do aktuálního data)"""
        if not self.vydaje:
            return 0.0
        dnes = datetime.utcnow()
        try:
            return sum(float(e.castka) if e.castka else 0.0 for e in self.vydaje if e.datum and e.datum <= dnes)
        except (TypeError, AttributeError):
            return 0.0
    
    @property
    def zbytek(self):
        """Zbývající rozpočet"""
        return self.castka_celkem_float - self.celkove_vydaje
    
    @property
    def procento_vycerpano(self):
        """Procento vyčerpání"""
        if self.castka_celkem_float == 0:
            return 0
        return min(100, (self.celkove_vydaje / self.castka_celkem_float) * 100)


class BudgetCategory(db.Model):
    """Kategorie rozpočtu - editovatelné kategorie"""
    __tablename__ = 'budget_category'
    
    id = db.Column(db.Integer, primary_key=True)
    nazev = db.Column(db.String(100), nullable=False, unique=True)
    kod = db.Column(db.String(20), nullable=True, unique=True)  # Kód kategorie
    popis = db.Column(db.Text, nullable=True)
    barva = db.Column(db.String(7), nullable=True, default='#007bff')  # Hex barva
    poradi = db.Column(db.Integer, nullable=False, default=0)
    aktivni = db.Column(db.Boolean, default=True)
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relace
    polozky = db.relationship('BudgetItem', backref='category', lazy=True)
    vydaje = db.relationship('Expense', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<BudgetCategory {self.nazev}>'


class BudgetItem(db.Model):
    """Rozpočtová položka - řádek v rozpočtu"""
    __tablename__ = 'budget_item'
    
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('budget_category.id'), nullable=False)
    nazev = db.Column(db.String(300), nullable=False)
    popis = db.Column(db.Text, nullable=True)
    castka = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    poradi = db.Column(db.Integer, nullable=False, default=0)
    aktivni = db.Column(db.Boolean, default=True)
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relace
    vydaje = db.relationship('Expense', backref='budget_item', lazy=True)
    
    def __repr__(self):
        return f'<BudgetItem {self.nazev} - {self.castka}>'
    
    @property
    def castka_float(self):
        return float(self.castka) if self.castka else 0.0
    
    @property
    def celkove_vydaje(self):
        """Celkové výdaje na tuto položku (do aktuálního data)"""
        if not self.vydaje:
            return 0.0
        dnes = datetime.utcnow()
        try:
            return sum(float(e.castka) if e.castka else 0.0 for e in self.vydaje if e.datum and e.datum <= dnes)
        except (TypeError, AttributeError):
            return 0.0
    
    @property
    def zbytek(self):
        """Zbývající částka"""
        return self.castka_float - self.celkove_vydaje


class Expense(db.Model):
    """Výdaj - univerzální výdaj (běžný, mzda, projektový)"""
    __tablename__ = 'expense'
    
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)  # Hlavní rozpočet
    budget_item_id = db.Column(db.Integer, db.ForeignKey('budget_item.id'), nullable=True)  # Volitelné
    category_id = db.Column(db.Integer, db.ForeignKey('budget_category.id'), nullable=False)
    projekt_id = db.Column(db.Integer, db.ForeignKey('projekt.id'), nullable=True)  # Pokud je k projektu
    
    castka = db.Column(db.Numeric(12, 2), nullable=False)
    datum = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    popis = db.Column(db.String(300), nullable=False)
    cis_faktury = db.Column(db.String(50), nullable=True)
    dodavatel = db.Column(db.String(200), nullable=True)
    poznamka = db.Column(db.Text, nullable=True)
    
    typ = db.Column(db.String(20), nullable=False, default='bezny')  # 'bezny', 'mzda', 'projektovy', 'provozni'
    mesic = db.Column(db.Integer, nullable=False)  # Měsíc výdaje (1-12)
    rok = db.Column(db.Integer, nullable=False)  # Rok výdaje
    
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Expense {self.popis} - {self.castka}>'
    
    @property
    def castka_float(self):
        return float(self.castka) if self.castka else 0.0


class MonthlyBudget(db.Model):
    """Měsíční přehled rozpočtu - pro hlídání po měsících"""
    __tablename__ = 'monthly_budget'
    
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)
    rok = db.Column(db.Integer, nullable=False)
    mesic = db.Column(db.Integer, nullable=False)  # 1-12
    
    planovano = db.Column(db.Numeric(12, 2), nullable=False, default=0)  # Plánovaná částka
    skutecne = db.Column(db.Numeric(12, 2), nullable=False, default=0)  # Skutečné výdaje
    odchylka = db.Column(db.Numeric(12, 2), nullable=False, default=0)  # Odchylka (skutecne - planovano)
    
    datum_aktualizace = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('budget_id', 'rok', 'mesic', name='unique_budget_month'),
    )
    
    def __repr__(self):
        return f'<MonthlyBudget {self.rok}-{self.mesic:02d}>'
    
    @property
    def planovano_float(self):
        return float(self.planovano) if self.planovano else 0.0
    
    @property
    def skutecne_float(self):
        return float(self.skutecne) if self.skutecne else 0.0
    
    @property
    def odchylka_float(self):
        return float(self.odchylka) if self.odchylka else 0.0
    
    @property
    def procento_vycerpano(self):
        """Procento vyčerpání měsíčního plánu"""
        if self.planovano_float == 0:
            return 0
        return min(100, (self.skutecne_float / self.planovano_float) * 100)


# Zastaralé modely - ponechány pro kompatibilitu (budou odstraněny)
class UctovaSkupina(db.Model):
    """ZASTARALÉ - bude odstraněno"""
    __tablename__ = 'uctova_skupina'
    id = db.Column(db.Integer, primary_key=True)
    ucet = db.Column(db.String(10), unique=True, nullable=False, index=True)
    nazev = db.Column(db.String(200), nullable=False)
    typ = db.Column(db.String(20), nullable=False)
    polozky = db.relationship('RozpoctovaPolozka', backref='uctova_skupina', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<UctovaSkupina {self.ucet} - {self.nazev}>'


class RozpoctovaPolozka(db.Model):
    """ZASTARALÉ - bude odstraněno"""
    __tablename__ = 'rozpoctova_polozka'
    id = db.Column(db.Integer, primary_key=True)
    rok = db.Column(db.Integer, nullable=False, default=2026, index=True)
    uctova_skupina_id = db.Column(db.Integer, db.ForeignKey('uctova_skupina.id'), nullable=False)
    analyticky_ucet = db.Column(db.String(10), nullable=False)
    nazev = db.Column(db.String(300), nullable=False)
    rozpocet = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    poznamka = db.Column(db.Text, nullable=True)
    vydaje = db.relationship('Vydaj', backref='polozka', lazy=True)
    
    def __repr__(self):
        return f'<RozpoctovaPolozka {self.nazev} - {self.rozpocet}>'
    
    @property
    def rozpocet_float(self):
        return float(self.rozpocet) if self.rozpocet else 0.0
    
    @property
    def celkove_vydaje_aktualni(self):
        dnes = datetime.utcnow()
        if not self.vydaje:
            return 0.0
        try:
            return sum(float(v.castka) if v.castka else 0.0 for v in self.vydaje if v.datum and v.datum <= dnes)
        except:
            return 0.0
    
    @property
    def zbytek_aktualni(self):
        return float(self.rozpocet) - self.celkove_vydaje_aktualni


class Vydaj(db.Model):
    """ZASTARALÉ - bude odstraněno"""
    __tablename__ = 'vydaj'
    id = db.Column(db.Integer, primary_key=True)
    rozpoctova_polozka_id = db.Column(db.Integer, db.ForeignKey('rozpoctova_polozka.id'), nullable=False)
    castka = db.Column(db.Numeric(12, 2), nullable=False)
    datum = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    popis = db.Column(db.String(300), nullable=True)
    cis_faktury = db.Column(db.String(50), nullable=True)
    dodavatel = db.Column(db.String(200), nullable=True)
    
    def __repr__(self):
        return f'<Vydaj {self.castka} Kč - {self.datum}>'
    
    @property
    def castka_float(self):
        return float(self.castka) if self.castka else 0.0
