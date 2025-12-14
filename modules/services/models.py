"""
Services Models - Modely pro modul služeb
"""

from datetime import datetime, date
from core import db

# Import User modelu pro relace (lazy import, aby se předešlo circular import)
def get_user_model():
    """Lazy import User modelu"""
    from modules.users.models import User
    return User


class SluzbaTemplate(db.Model):
    """Šablona služby - definuje pravidla pro služby"""
    __tablename__ = 'sluzba_template'
    
    id = db.Column(db.Integer, primary_key=True)
    nazev = db.Column(db.String(200), nullable=False)
    typ = db.Column(db.String(20), nullable=False)  # 'fixni', 'rotujici', 'nedele'
    oddeleni = db.Column(db.String(20), nullable=False)  # 'detske' nebo 'dospělé'
    den_v_tydnu = db.Column(db.Integer, nullable=True)  # 0=pondělí, 1=úterý (zavřeno), 2=středa, ..., 6=neděle
    hodina_od = db.Column(db.String(10), nullable=False, default='08:00')  # Formát HH:MM, např. "09:00"
    hodina_do = db.Column(db.String(10), nullable=False, default='16:00')  # Formát HH:MM, např. "17:00"
    zamestnanec_id = db.Column(db.Integer, db.ForeignKey('zamestnanec_oon.id'), nullable=True)  # Pro fixní službu (původní, pro kompatibilitu)
    aktivni = db.Column(db.Boolean, default=True)
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    poznamka = db.Column(db.Text, nullable=True)
    
    # Pro rotující službu - seznam zaměstnanců v pořadí
    rotujici_seznam = db.Column(db.Text, nullable=True)  # JSON seznam ID zaměstnanců
    
    # Pro fixní službu s více zaměstnanci - seznam zaměstnanců s časy
    # Formát: [{"zamestnanec_id": 1, "hodina_od": "08:00", "hodina_do": "12:00"}, ...]
    fixni_zamestnanci = db.Column(db.Text, nullable=True)  # JSON seznam zaměstnanců s časy
    
    # Relace
    zamestnanec = db.relationship('ZamestnanecAOON', foreign_keys=[zamestnanec_id], backref='fixni_sluzby', lazy=True)
    
    def __repr__(self):
        return f'<SluzbaTemplate {self.nazev} - {self.typ}>'
    
    @property
    def rotujici_seznam_ids(self):
        """Vrátí seznam ID zaměstnanců pro rotující službu"""
        import json
        if self.rotujici_seznam:
            try:
                return json.loads(self.rotujici_seznam)
            except:
                return []
        return []
    
    @property
    def fixni_zamestnanci_list(self):
        """Vrátí seznam zaměstnanců s časy pro fixní službu"""
        import json
        if self.fixni_zamestnanci:
            try:
                return json.loads(self.fixni_zamestnanci)
            except:
                return []
        # Pro zpětnou kompatibilitu - pokud není fixni_zamestnanci, použij zamestnanec_id
        if self.zamestnanec_id:
            return [{
                'zamestnanec_id': self.zamestnanec_id,
                'hodina_od': self.hodina_od,
                'hodina_do': self.hodina_do
            }]
        return []


class Sluzba(db.Model):
    """Konkrétní služba v kalendáři"""
    __tablename__ = 'sluzba'
    
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('sluzba_template.id'), nullable=True)  # Odkaz na šablonu
    datum = db.Column(db.Date, nullable=False, index=True)
    den_v_tydnu = db.Column(db.Integer, nullable=False)  # 0=pondělí, 1=úterý, ..., 6=neděle
    oddeleni = db.Column(db.String(20), nullable=False)  # 'detske' nebo 'dospělé'
    hodina_od = db.Column(db.String(10), nullable=False, default='08:00')  # Formát HH:MM
    hodina_do = db.Column(db.String(10), nullable=False, default='16:00')  # Formát HH:MM
    zamestnanec_id = db.Column(db.Integer, db.ForeignKey('zamestnanec_oon.id'), nullable=False)
    typ = db.Column(db.String(20), nullable=False)  # 'fixni', 'rotujici', 'nedele'
    poznamka = db.Column(db.Text, nullable=True)
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relace
    template = db.relationship('SluzbaTemplate', foreign_keys=[template_id], backref='sluzby', lazy=True)
    zamestnanec = db.relationship('ZamestnanecAOON', foreign_keys=[zamestnanec_id], backref='sluzby', lazy=True)
    
    # Odstraněn UniqueConstraint - umožňuje více služeb na jeden den/oddělení (různí zaměstnanci, různé časy)
    
    def __repr__(self):
        return f'<Sluzba {self.datum} - {self.oddeleni} - {self.zamestnanec_id}>'
    
    @property
    def den_nazev(self):
        """Vrátí název dne v týdnu"""
        dny = ['Pondělí', 'Úterý', 'Středa', 'Čtvrtek', 'Pátek', 'Sobota', 'Neděle']
        return dny[self.den_v_tydnu] if 0 <= self.den_v_tydnu < 7 else 'Neznámý'
    
    # Flag pro označení, že služba byla změněna výjimkou nebo výměnou
    je_vynimka = db.Column(db.Boolean, default=False)
    je_vymena = db.Column(db.Boolean, default=False)


class SluzbaVynimka(db.Model):
    """Výjimka v službě - dočasná změna zaměstnance nebo času"""
    __tablename__ = 'sluzba_vynimka'
    
    id = db.Column(db.Integer, primary_key=True)
    sluzba_id = db.Column(db.Integer, db.ForeignKey('sluzba.id'), nullable=False)
    datum = db.Column(db.Date, nullable=False, index=True)
    oddeleni = db.Column(db.String(20), nullable=False)
    hodina_od = db.Column(db.String(10), nullable=False)  # Nový čas od
    hodina_do = db.Column(db.String(10), nullable=False)  # Nový čas do
    zamestnanec_id = db.Column(db.Integer, db.ForeignKey('zamestnanec_oon.id'), nullable=False)  # Nový zaměstnanec
    poznamka = db.Column(db.Text, nullable=True)
    vytvoril_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    aktivni = db.Column(db.Boolean, default=True)
    
    # Relace
    sluzba = db.relationship('Sluzba', foreign_keys=[sluzba_id], backref='vynimky', lazy=True)
    zamestnanec = db.relationship('ZamestnanecAOON', foreign_keys=[zamestnanec_id], backref='vynimky_sluzeb', lazy=True)
    # User model se načte lazy, aby se předešlo circular import
    vytvoril_user = db.relationship('User', foreign_keys=[vytvoril_user_id], backref='vytvorene_vynimky', lazy=True)
    
    def __repr__(self):
        return f'<SluzbaVynimka {self.datum} - {self.oddeleni} - {self.zamestnanec_id}>'


class SluzbaVymena(db.Model):
    """Výměna služeb mezi dvěma zaměstnanci"""
    __tablename__ = 'sluzba_vymena'
    
    id = db.Column(db.Integer, primary_key=True)
    sluzba1_id = db.Column(db.Integer, db.ForeignKey('sluzba.id'), nullable=False)  # První služba
    sluzba2_id = db.Column(db.Integer, db.ForeignKey('sluzba.id'), nullable=False)  # Druhá služba
    zamestnanec1_id = db.Column(db.Integer, db.ForeignKey('zamestnanec_oon.id'), nullable=False)  # Původní zaměstnanec služby 1
    zamestnanec2_id = db.Column(db.Integer, db.ForeignKey('zamestnanec_oon.id'), nullable=False)  # Původní zaměstnanec služby 2
    poznamka = db.Column(db.Text, nullable=True)
    vytvoril_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    schvaleno = db.Column(db.Boolean, default=False)  # Zda byla výměna schválena
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    aktivni = db.Column(db.Boolean, default=True)
    
    # Relace
    sluzba1 = db.relationship('Sluzba', foreign_keys=[sluzba1_id], backref='vymeny_jako_sluzba1', lazy=True)
    sluzba2 = db.relationship('Sluzba', foreign_keys=[sluzba2_id], backref='vymeny_jako_sluzba2', lazy=True)
    zamestnanec1 = db.relationship('ZamestnanecAOON', foreign_keys=[zamestnanec1_id], backref='vymeny_jako_zam1', lazy=True)
    zamestnanec2 = db.relationship('ZamestnanecAOON', foreign_keys=[zamestnanec2_id], backref='vymeny_jako_zam2', lazy=True)
    # User model se načte lazy, aby se předešlo circular import
    vytvoril_user = db.relationship('User', foreign_keys=[vytvoril_user_id], backref='vytvorene_vymeny', lazy=True)
    
    def __repr__(self):
        return f'<SluzbaVymena {self.sluzba1_id} <-> {self.sluzba2_id}>'
