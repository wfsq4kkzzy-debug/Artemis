"""
Modely pro modul rozpočtu - flexibilní struktura s kategoriemi a podkategoriemi
"""

from datetime import datetime
from decimal import Decimal
from typing import List
from core import db


class Budget(db.Model):
    """Rozpočet - hlavní nebo podrozpočet"""
    __tablename__ = 'budget'
    
    id = db.Column(db.Integer, primary_key=True)
    nazev = db.Column(db.String(200), nullable=False)
    popis = db.Column(db.Text, nullable=True)
    typ = db.Column(db.String(20), nullable=False, default='hlavni')  # 'hlavni', 'podrozpocet'
    rok = db.Column(db.Integer, nullable=False, default=2026)
    castka_celkem = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    aktivni = db.Column(db.Boolean, default=True)
    hlavni = db.Column(db.Boolean, default=False)  # Pouze jeden může být hlavní
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    datum_aktualizace = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    
    # Relace
    kategorie = db.relationship('BudgetCategory', backref='budget', lazy=True, cascade='all, delete-orphan')
    polozky = db.relationship('BudgetItem', backref='budget', lazy=True, cascade='all, delete-orphan')
    vydaje = db.relationship('Expense', backref='budget', lazy=True, cascade='all, delete-orphan')
    vynosy = db.relationship('Revenue', backref='budget', lazy=True, cascade='all, delete-orphan')
    
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
    
    @property
    def celkove_vynosy(self):
        """Celkové výnosy v rozpočtu (do aktuálního data)"""
        if not self.vynosy:
            return 0.0
        dnes = datetime.utcnow()
        try:
            # Jednorázové výnosy - skutečně přijaté
            jednorazove = sum(
                float(r.castka) if r.castka else 0.0 
                for r in self.vynosy 
                if r.typ == 'jednorazovy' and r.datum and r.datum <= dnes and r.skutecne_prijato
            )
            # Pravidelné výnosy - skutečně přijaté
            pravidelne = sum(
                float(r.castka) if r.castka else 0.0 
                for r in self.vynosy 
                if r.typ == 'pravidelny' and r.skutecne_prijato
            )
            return jednorazove + pravidelne
        except (TypeError, AttributeError):
            return 0.0
    
    @property
    def planovane_vynosy(self):
        """Naplánované výnosy (včetně budoucích)"""
        if not self.vynosy:
            return 0.0
        try:
            return sum(
                float(r.castka) if r.castka else 0.0 
                for r in self.vynosy 
                if r.naplanovano
            )
        except (TypeError, AttributeError):
            return 0.0
    
    @property
    def bilance(self):
        """Bilance (výnosy - výdaje)"""
        return self.celkove_vynosy - self.celkove_vydaje


class BudgetCategory(db.Model):
    """Kategorie rozpočtu - náklady/výnosy, mzdové/ostatní"""
    __tablename__ = 'budget_category'
    
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)
    typ = db.Column(db.String(30), nullable=False)  # 'naklad_mzdovy', 'naklad_ostatni', 'vynos'
    nazev = db.Column(db.String(100), nullable=False)
    kod = db.Column(db.String(20), nullable=True)
    popis = db.Column(db.Text, nullable=True)
    barva = db.Column(db.String(7), nullable=True, default='#007bff')
    poradi = db.Column(db.Integer, nullable=False, default=0)
    aktivni = db.Column(db.Boolean, default=True)
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relace
    podkategorie = db.relationship('BudgetSubCategory', backref='category', lazy=True, cascade='all, delete-orphan')
    polozky = db.relationship('BudgetItem', backref='category', lazy=True)
    vydaje = db.relationship('Expense', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<BudgetCategory {self.nazev} - {self.typ}>'
    
    @property
    def celkove_vydaje(self):
        """Celkové výdaje v kategorii"""
        if not self.vydaje:
            return 0.0
        dnes = datetime.utcnow()
        try:
            return sum(float(e.castka) if e.castka else 0.0 for e in self.vydaje if e.datum and e.datum <= dnes)
        except:
            return 0.0


class BudgetSubCategory(db.Model):
    """Podkategorie rozpočtu"""
    __tablename__ = 'budget_subcategory'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('budget_category.id'), nullable=False)
    nazev = db.Column(db.String(100), nullable=False)
    kod = db.Column(db.String(20), nullable=True)
    popis = db.Column(db.Text, nullable=True)
    poradi = db.Column(db.Integer, nullable=False, default=0)
    aktivni = db.Column(db.Boolean, default=True)
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relace
    polozky = db.relationship('BudgetItem', backref='subcategory', lazy=True)
    vydaje = db.relationship('Expense', backref='subcategory', lazy=True)
    
    def __repr__(self):
        return f'<BudgetSubCategory {self.nazev}>'
    
    @property
    def celkove_vydaje(self):
        """Celkové výdaje v podkategorii"""
        if not self.vydaje:
            return 0.0
        dnes = datetime.utcnow()
        try:
            return sum(float(e.castka) if e.castka else 0.0 for e in self.vydaje if e.datum and e.datum <= dnes)
        except:
            return 0.0


class BudgetItem(db.Model):
    """Rozpočtová položka - řádek v rozpočtu"""
    __tablename__ = 'budget_item'
    
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('budget_category.id'), nullable=True)  # Volitelné
    subcategory_id = db.Column(db.Integer, db.ForeignKey('budget_subcategory.id'), nullable=True)
    
    # Nová struktura - jednoduché položky
    ucet = db.Column(db.String(20), nullable=False)  # Účet
    poducet = db.Column(db.String(20), nullable=True)  # Podúčet (volitelné)
    popis = db.Column(db.String(300), nullable=False)  # Popis položky
    typ = db.Column(db.String(20), nullable=False, default='naklad')  # 'naklad' nebo 'vynos'
    castka = db.Column(db.Numeric(12, 2), nullable=False, default=0)  # Celkový rozpočet
    
    # Původní pole (pro kompatibilitu)
    nazev = db.Column(db.String(300), nullable=True)  # Nyní volitelné, používá se popis
    popis_old = db.Column(db.Text, nullable=True)  # Původní popis pro kompatibilitu
    
    poradi = db.Column(db.Integer, nullable=False, default=0)
    aktivni = db.Column(db.Boolean, default=True)
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relace
    vydaje = db.relationship('Expense', backref='budget_item', lazy=True)
    vynosy = db.relationship('Revenue', foreign_keys='Revenue.budget_item_id', backref='budget_item', lazy=True)
    
    def __repr__(self):
        return f'<BudgetItem {self.ucet} - {self.popis} - {self.castka}>'
    
    @property
    def castka_float(self):
        return float(self.castka) if self.castka else 0.0
    
    @property
    def aktualni_plneni(self):
        """Aktuální plnění - výdaje pro náklady, výnosy pro výnosy (včetně měsíčních aktualizací)"""
        dnes = datetime.utcnow()
        aktualni_mesic = dnes.month
        aktualni_rok = dnes.year
        
        if self.typ == 'naklad':
            # Pro náklady - součet výdajů
            vydaje_castka = 0.0
            if self.vydaje:
                try:
                    vydaje_castka = sum(float(e.castka) if e.castka else 0.0 for e in self.vydaje if e.datum and e.datum <= dnes)
                except:
                    vydaje_castka = 0.0
            
            # Použij aktuální stav z měsíčních aktualizací (pokud je zadán)
            if hasattr(self, 'mesicni_stavy') and self.mesicni_stavy:
                try:
                    # Najdi nejnovější měsíční stav do aktuálního měsíce
                    nejnovejsi_stav = None
                    for stav in self.mesicni_stavy:
                        if stav.rok < aktualni_rok or (stav.rok == aktualni_rok and stav.mesic <= aktualni_mesic):
                            if nejnovejsi_stav is None:
                                nejnovejsi_stav = stav
                            elif stav.rok > nejnovejsi_stav.rok or (stav.rok == nejnovejsi_stav.rok and stav.mesic > nejnovejsi_stav.mesic):
                                nejnovejsi_stav = stav
                    
                    # Pokud má nejnovější stav aktuální stav, použij ho
                    if nejnovejsi_stav and nejnovejsi_stav.aktualni_stav is not None:
                        return nejnovejsi_stav.aktualni_stav_float
                    
                    # Jinak použij souhrnné výdaje (zpětná kompatibilita)
                    souhrnne_vydaje = 0.0
                    for stav in self.mesicni_stavy:
                        if stav.rok < aktualni_rok or (stav.rok == aktualni_rok and stav.mesic <= aktualni_mesic):
                            souhrnne_vydaje += float(stav.souhrnne_vydaje) if stav.souhrnne_vydaje else 0.0
                    return vydaje_castka + souhrnne_vydaje
                except:
                    pass
            
            return vydaje_castka
        else:
            # Pro výnosy - součet výnosů
            if not self.vynosy:
                return 0.0
            try:
                return sum(float(r.castka) if r.castka else 0.0 for r in self.vynosy if r.skutecne_prijato)
            except:
                return 0.0
    
    @property
    def celkove_vydaje(self):
        """Celkové výdaje na tuto položku (kompatibilita)"""
        if self.typ == 'naklad':
            return self.aktualni_plneni
        return 0.0
    
    @property
    def procenta_vycerpani(self):
        """Procenta vyčerpání"""
        import json
        from datetime import datetime as dt
        
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"budget/models.py:236","message":"procenta_vycerpani called","data":{"item_id":self.id,"castka_float":self.castka_float},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        
        if self.castka_float == 0:
            return 0.0
        
        try:
            aktualni = self.aktualni_plneni
            result = min(100.0, (aktualni / self.castka_float) * 100.0)
            # #region agent log
            with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"budget/models.py:245","message":"procenta_vycerpani calculated","data":{"aktualni_plneni":aktualni,"result":result},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
            # #endregion
            return result
        except Exception as ex:
            # #region agent log
            with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"budget/models.py:249","message":"Exception in procenta_vycerpani","data":{"error":str(ex)},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
            # #endregion
            return 0.0
    
    @property
    def zbytek(self):
        """Zbývající částka"""
        return self.castka_float - self.aktualni_plneni


class Expense(db.Model):
    """Výdaj - univerzální výdaj s propojením na všechny moduly"""
    __tablename__ = 'expense'
    
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)
    budget_item_id = db.Column(db.Integer, db.ForeignKey('budget_item.id'), nullable=False)  # Povinné - každý výdaj musí být navázán na položku rozpočtu
    category_id = db.Column(db.Integer, db.ForeignKey('budget_category.id'), nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('budget_subcategory.id'), nullable=True)
    
    # Propojení s ostatními moduly
    personnel_id = db.Column(db.Integer, db.ForeignKey('zamestnanec_oon.id'), nullable=True)  # Pro mzdy
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Kdo přidal
    
    castka = db.Column(db.Numeric(12, 2), nullable=False)
    datum = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    popis = db.Column(db.String(300), nullable=False)
    cis_faktury = db.Column(db.String(50), nullable=True)
    dodavatel = db.Column(db.String(200), nullable=True)
    poznamka = db.Column(db.Text, nullable=True)
    
    typ = db.Column(db.String(20), nullable=False, default='bezny')  # 'bezny', 'mzda'
    mesic = db.Column(db.Integer, nullable=False)  # Měsíc výdaje (1-12)
    rok = db.Column(db.Integer, nullable=False)  # Rok výdaje
    
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Expense {self.popis} - {self.castka}>'
    
    @property
    def castka_float(self):
        return float(self.castka) if self.castka else 0.0


class MonthlyBudgetItem(db.Model):
    """Měsíční stav položky rozpočtu - pro aktualizace ke konci měsíce"""
    __tablename__ = 'monthly_budget_item'
    
    id = db.Column(db.Integer, primary_key=True)
    budget_item_id = db.Column(db.Integer, db.ForeignKey('budget_item.id'), nullable=False)
    mesic = db.Column(db.Integer, nullable=False)  # 1-12
    rok = db.Column(db.Integer, nullable=False)
    
    # Aktuální stav ke konci měsíce (celková částka utracená k danému datu)
    aktualni_stav = db.Column(db.Numeric(12, 2), nullable=True)  # NULL = není zadán
    
    # Souhrnné výdaje, které nejsou zadány ručně (pro zpětnou kompatibilitu)
    souhrnne_vydaje = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    
    # Poznámky k měsíční aktualizaci
    poznamka = db.Column(db.Text, nullable=True)
    
    # Kdo a kdy aktualizoval
    aktualizoval = db.Column(db.String(200), nullable=True)
    datum_aktualizace = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relace
    budget_item = db.relationship('BudgetItem', backref='mesicni_stavy')
    
    def __repr__(self):
        return f'<MonthlyBudgetItem {self.budget_item_id} - {self.rok}/{self.mesic:02d}>'
    
    @property
    def souhrnne_vydaje_float(self):
        return float(self.souhrnne_vydaje) if self.souhrnne_vydaje else 0.0
    
    @property
    def aktualni_stav_float(self):
        return float(self.aktualni_stav) if self.aktualni_stav is not None else None


class Revenue(db.Model):
    """Výnos - jednorázový nebo pravidelný výnos"""
    __tablename__ = 'revenue'
    
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)
    budget_item_id = db.Column(db.Integer, db.ForeignKey('budget_item.id'), nullable=True)  # Propojení s položkou rozpočtu
    category_id = db.Column(db.Integer, db.ForeignKey('budget_category.id'), nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('budget_subcategory.id'), nullable=True)
    
    nazev = db.Column(db.String(300), nullable=False)
    popis = db.Column(db.Text, nullable=True)
    castka = db.Column(db.Numeric(12, 2), nullable=False)
    
    typ = db.Column(db.String(20), nullable=False, default='jednorazovy')  # 'jednorazovy', 'pravidelny'
    
    # Pro jednorázové výnosy
    datum = db.Column(db.DateTime, nullable=True)  # Datum jednorázového výnosu
    mesic = db.Column(db.Integer, nullable=True)  # Měsíc (1-12) pro jednorázové
    rok = db.Column(db.Integer, nullable=False)  # Rok
    
    # Pro pravidelné výnosy
    datum_zacatku = db.Column(db.DateTime, nullable=True)  # Od kdy se opakuje
    datum_konce = db.Column(db.DateTime, nullable=True)  # Do kdy se opakuje (volitelné)
    frekvence = db.Column(db.String(20), nullable=True, default='mesicne')  # 'mesicne', 'ctvrtletne', 'rocne'
    mesice = db.Column(db.String(50), nullable=True)  # Které měsíce (např. "1,2,3" nebo "vse" pro všechny)
    
    # Plánování
    naplanovano = db.Column(db.Boolean, default=False)  # Zda je naplánováno dopředu
    skutecne_prijato = db.Column(db.Boolean, default=False)  # Zda bylo skutečně přijato
    
    cis_faktury = db.Column(db.String(50), nullable=True)
    odberatel = db.Column(db.String(200), nullable=True)  # Kdo platí
    poznamka = db.Column(db.Text, nullable=True)
    
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    datum_aktualizace = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Revenue {self.nazev} - {self.castka} ({self.typ})>'
    
    @property
    def castka_float(self):
        return float(self.castka) if self.castka else 0.0
    
    def get_planned_months(self) -> List[int]:
        """Vrátí seznam měsíců, kdy má být výnos přijat"""
        if self.typ == 'jednorazovy':
            if self.mesic:
                return [self.mesic]
            return []
        
        # Pravidelný výnos
        if self.mesice == 'vse' or not self.mesice:
            return list(range(1, 13))
        
        try:
            return [int(m.strip()) for m in self.mesice.split(',') if m.strip().isdigit()]
        except:
            return list(range(1, 13))


# Zastaralé modely - ponechány pro kompatibilitu
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




