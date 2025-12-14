"""
Projects Models - Modely pro modul projektů
"""

from datetime import datetime
from core import db

# Import pro vztahy (lazy import, aby se předešlo circular imports)
# User a ZamestnanecAOON budou importovány pomocí string referencí v relationship


class Projekt(db.Model):
    """Model pro projekt - nová logika: projekt má celkový rozpočet a výdaje"""
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
    
    # NOVÉ: Celkový rozpočet projektu (jedno číslo)
    rozpocet = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    
    # NOVÉ: Kdo projekt založil - vztah k uživateli
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    # NOVÉ: Vztah k personální agendě (přímý odkaz na zaměstnance)
    created_by_personnel_id = db.Column(db.Integer, db.ForeignKey('zamestnanec_oon.id'), nullable=True)
    
    # Relace
    budgets = db.relationship('BudgetProjektu', backref='projekt', lazy=True, cascade='all, delete-orphan')  # Zastaralé, ale ponecháno pro kompatibilitu
    vydaje = db.relationship('VydajProjektu', backref='projekt', lazy=True, cascade='all, delete-orphan')
    terminy = db.relationship('Termin', backref='projekt', lazy=True, cascade='all, delete-orphan')
    zpravy = db.relationship('Zprava', backref='projekt', lazy=True, cascade='all, delete-orphan')
    znalosti = db.relationship('Znalost', backref='projekt', lazy=True, cascade='all, delete-orphan')
    
    # NOVÉ: Vztah k uživateli, který projekt založil
    created_by_user = db.relationship('User', foreign_keys=[created_by_user_id], backref='created_projects', lazy=True)
    # NOVÉ: Vztah k personální agendě
    created_by_personnel = db.relationship('ZamestnanecAOON', foreign_keys=[created_by_personnel_id], backref='created_projects', lazy=True)
    # NOVÉ: Sdílení projektu
    shares = db.relationship('ProjectShare', backref='projekt', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Projekt {self.nazev}>'
    
    @property
    def rozpocet_float(self):
        """Vrátí rozpočet jako float"""
        return float(self.rozpocet) if self.rozpocet else 0.0
    
    @property
    def celkovy_rozpocet(self):
        """Vrátí celkový rozpočet projektu (z pole rozpocet)"""
        return self.rozpocet_float
    
    @property
    def celkove_vydaje(self):
        """Vrátí celkové výdaje projektu (pouze do aktuálního data)"""
        if not self.vydaje:
            return 0.0
        dnes = datetime.utcnow()
        try:
            return sum(float(v.castka) if v.castka else 0.0 for v in self.vydaje if v.datum and v.datum <= dnes)
        except (TypeError, AttributeError):
            return 0.0
    
    @property
    def celkove_vydaje_vse(self):
        """Vrátí všechny výdaje projektu (včetně budoucích)"""
        if not self.vydaje:
            return 0.0
        try:
            return sum(float(v.castka) if v.castka else 0.0 for v in self.vydaje)
        except (TypeError, AttributeError):
            return 0.0
    
    @property
    def zbytek(self):
        """Vrátí zbývající rozpočet (k aktuálnímu datu)"""
        return self.celkovy_rozpocet - self.celkove_vydaje
    
    @property
    def procento_vycerpano(self):
        """Vrátí procento vyčerpání rozpočtu"""
        if self.celkovy_rozpocet == 0:
            return 0
        return min(100, (self.celkove_vydaje / self.celkovy_rozpocet) * 100)


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
    """Model pro výdaj v projektu - bez kategorií, jen výdaj k projektu"""
    __tablename__ = 'vydaj_projektu'
    
    id = db.Column(db.Integer, primary_key=True)
    projekt_id = db.Column(db.Integer, db.ForeignKey('projekt.id'), nullable=False)
    popis = db.Column(db.String(300), nullable=False)
    castka = db.Column(db.Numeric(12, 2), nullable=False)
    datum = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    cis_faktury = db.Column(db.String(50), nullable=True)
    dodavatel = db.Column(db.String(200), nullable=True)
    poznamka = db.Column(db.Text, nullable=True)  # Nové pole pro poznámky
    
    # NOVÉ: Kdo přidal výdaj (iniciály)
    created_by_initials = db.Column(db.String(10), nullable=True)
    
    # Zastaralé pole kategorie - ponecháno pro kompatibilitu, ale nepoužívá se
    kategorie = db.Column(db.String(100), nullable=True, default='')
    
    def __repr__(self):
        return f'<VydajProjektu {self.popis} - {self.castka}>'
    
    @property
    def castka_float(self):
        """Vrátí částku jako float"""
        return float(self.castka) if self.castka else 0.0


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
    
    # NOVÉ: Kdo přidal termín (iniciály)
    created_by_initials = db.Column(db.String(10), nullable=True)
    
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
    
    # NOVÉ: Kdo přidal zprávu (iniciály) - pokud není vyplněno, použije se autor
    created_by_initials = db.Column(db.String(10), nullable=True)
    
    # NOVÉ: Komu je zpráva určena (null = všem, jinak ID uživatele)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relace
    to_user = db.relationship('User', foreign_keys=[to_user_id], backref='received_messages', lazy=True)
    
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
    
    # NOVÉ: Kdo přidal znalost (iniciály) - pokud není vyplněno, použije se autor
    created_by_initials = db.Column(db.String(10), nullable=True)
    
    def __repr__(self):
        return f'<Znalost {self.nazev}>'


class ProjectShare(db.Model):
    """Model pro sdílení projektu mezi uživateli"""
    __tablename__ = 'project_share'
    
    id = db.Column(db.Integer, primary_key=True)
    projekt_id = db.Column(db.Integer, db.ForeignKey('projekt.id'), nullable=False)
    shared_with_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Kdo sdílel
    
    # Oprávnění: 'read' = jen zobrazení, 'write' = může upravovat
    permission = db.Column(db.String(20), nullable=False, default='read')  # 'read', 'write'
    
    datum_sdileni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    poznamka = db.Column(db.Text, nullable=True)
    aktivni = db.Column(db.Boolean, default=True)
    
    # Relace
    shared_with_user = db.relationship('User', foreign_keys=[shared_with_user_id], backref='shared_projects', lazy=True)
    shared_by_user = db.relationship('User', foreign_keys=[shared_by_user_id], backref='shared_projects_by_me', lazy=True)
    
    __table_args__ = (
        db.UniqueConstraint('projekt_id', 'shared_with_user_id', name='unique_project_share'),
    )
    
    def __repr__(self):
        return f'<ProjectShare projekt={self.projekt_id} with_user={self.shared_with_user_id} permission={self.permission}>'
    
    @property
    def can_edit(self):
        """Může uživatel upravovat projekt?"""
        return self.permission == 'write'




