"""
Modely pro modul Uživatelé
Propojení s personálním modulem, projekty a AI modulem
"""

from datetime import datetime
from core import db


class User(db.Model):
    """Uživatel - každý uživatel pochází z personálního modulu"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    personnel_id = db.Column(db.Integer, db.ForeignKey('zamestnanec_oon.id'), nullable=False, unique=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Pro budoucí autentizaci
    
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin', 'user', 'viewer'
    aktivni = db.Column(db.Boolean, default=True)
    slouzi_nedele = db.Column(db.Boolean, default=False)  # Slouží neděle
    slouzi_rotujici = db.Column(db.Boolean, default=False)  # Slouží rotující služby
    
    workspace_settings = db.Column(db.Text, nullable=True)  # JSON s nastavením workspace
    
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    datum_aktualizace = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    posledni_prihlaseni = db.Column(db.DateTime, nullable=True)
    
    # Relace
    personnel = db.relationship('ZamestnanecAOON', foreign_keys=[personnel_id], backref='user', lazy=True)
    projekty = db.relationship('UserProject', backref='user', lazy=True, cascade='all, delete-orphan')
    connections_as_user1 = db.relationship('UserConnection', foreign_keys='UserConnection.user1_id', backref='user1', lazy=True)
    connections_as_user2 = db.relationship('UserConnection', foreign_keys='UserConnection.user2_id', backref='user2', lazy=True)
    shared_chats_shared_by = db.relationship('SharedChat', foreign_keys='SharedChat.shared_by_user_id', backref='shared_by', lazy=True)
    shared_chats_shared_with = db.relationship('SharedChat', foreign_keys='SharedChat.shared_with_user_id', backref='shared_with', lazy=True)
    messages_sent = db.relationship('UserMessage', foreign_keys='UserMessage.from_user_id', backref='from_user', lazy=True)
    messages_received = db.relationship('UserMessage', foreign_keys='UserMessage.to_user_id', backref='to_user', lazy=True)
    notifications = db.relationship('UserNotification', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def jmeno_prijmeni(self):
        """Vrátí jméno a příjmení z personálního modulu"""
        try:
            # Zkus načíst personální data
            if hasattr(self, 'personnel') and self.personnel:
                return f"{self.personnel.jmeno} {self.personnel.prijmeni}"
            
            # Pokud relace není načtena, zkus načíst ručně
            if self.personnel_id:
                from ..personnel.models import ZamestnanecAOON
                personnel = ZamestnanecAOON.query.get(self.personnel_id)
                if personnel:
                    return f"{personnel.jmeno} {personnel.prijmeni}"
        except Exception:
            pass
        
        # Fallback na username
        return self.username
    
    @property
    def workspace_settings_dict(self):
        """Vrátí workspace settings jako dict"""
        import json
        if self.workspace_settings:
            try:
                return json.loads(self.workspace_settings)
            except:
                return {}
        return {}


class UserProject(db.Model):
    """Uživatel v projektu - propojení uživatele s projektem"""
    __tablename__ = 'user_project'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    projekt_id = db.Column(db.Integer, db.ForeignKey('projekt.id'), nullable=False)
    
    role = db.Column(db.String(20), nullable=False, default='member')  # 'owner', 'manager', 'member', 'viewer'
    aktivni = db.Column(db.Boolean, default=True)
    datum_pridani = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'projekt_id', name='unique_user_project'),
    )
    
    def __repr__(self):
        return f'<UserProject user={self.user_id} projekt={self.projekt_id} role={self.role}>'


class UserConnection(db.Model):
    """Propojení uživatelů - vztahy mezi uživateli"""
    __tablename__ = 'user_connection'
    
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    typ = db.Column(db.String(20), nullable=False, default='colleague')  # 'colleague', 'supervisor', 'subordinate', 'custom'
    popis = db.Column(db.String(200), nullable=True)
    aktivni = db.Column(db.Boolean, default=True)
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user1_id', 'user2_id', name='unique_user_connection'),
    )
    
    def __repr__(self):
        return f'<UserConnection {self.user1_id} <-> {self.user2_id} ({self.typ})>'


class SharedChat(db.Model):
    """Sdílený AI chat - propojení s AI modulem"""
    __tablename__ = 'shared_chat'
    
    id = db.Column(db.Integer, primary_key=True)
    ai_session_id = db.Column(db.Integer, db.ForeignKey('ai_session.id'), nullable=False)
    shared_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_with_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # null = veřejné
    
    poznamka = db.Column(db.Text, nullable=True)
    datum_sdileni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    aktivni = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        if self.shared_with_user_id:
            return f'<SharedChat session={self.ai_session_id} shared_by={self.shared_by_user_id} with={self.shared_with_user_id}>'
        return f'<SharedChat session={self.ai_session_id} shared_by={self.shared_by_user_id} (public)>'
    
    @property
    def is_public(self):
        """Je chat veřejný?"""
        return self.shared_with_user_id is None


class UserMessage(db.Model):
    """Zpráva mezi uživateli"""
    __tablename__ = 'user_message'
    
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # null = veřejné/všem
    
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    typ = db.Column(db.String(20), nullable=False, default='message')  # 'message', 'notification', 'system'
    
    precteno = db.Column(db.Boolean, default=False)
    datum_odeslani = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    datum_precteni = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<UserMessage from={self.from_user_id} to={self.to_user_id} subject={self.subject}>'
    
    @property
    def is_public(self):
        """Je zpráva veřejná?"""
        return self.to_user_id is None


class UserNotification(db.Model):
    """Notifikace pro uživatele"""
    __tablename__ = 'user_notification'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    typ = db.Column(db.String(30), nullable=False)  # 'project_update', 'message', 'task_assigned', 'budget_alert'
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=True)
    
    precteno = db.Column(db.Boolean, default=False)
    datum_vytvoreni = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    related_id = db.Column(db.Integer, nullable=True)  # ID souvisejícího záznamu
    related_type = db.Column(db.String(50), nullable=True)  # 'project', 'message', 'expense', atd.
    
    def __repr__(self):
        return f'<UserNotification user={self.user_id} typ={self.typ} title={self.title}>'




