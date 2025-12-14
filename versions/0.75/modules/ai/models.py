"""
AI Models - Modely pro modul AI asistenta
"""

from datetime import datetime
from core import db


class Employee(db.Model):
    """Model zaměstnance"""
    __tablename__ = 'ai_employee'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'librarian', 'admin', 'manager'
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relace
    sessions = db.relationship('AISession', backref='employee', lazy=True, cascade='all, delete-orphan')
    knowledge_entries = db.relationship('KnowledgeEntry', backref='created_by_user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Employee {self.name}>'


class AISession(db.Model):
    """Jedna konverzační relace s AI asistentem"""
    __tablename__ = 'ai_session'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('ai_employee.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False, default='Nová konverzace')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_archived = db.Column(db.Boolean, default=False)
    context = db.Column(db.Text, nullable=True)  # Dodatečný kontext pro session
    
    # Relace
    messages = db.relationship('Message', backref='session', lazy=True, cascade='all, delete-orphan')
    service_records = db.relationship('ServiceRecord', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<AISession {self.id} - {self.title}>'


class Message(db.Model):
    """Jednotlivá zpráva v konverzaci"""
    __tablename__ = 'ai_message'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('ai_session.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' nebo 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    tokens_used = db.Column(db.Integer, nullable=True)  # Pro sledování API nákladů
    
    def __repr__(self):
        return f'<Message {self.id} - {self.role}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }


class KnowledgeEntry(db.Model):
    """Položka znalostní databáze"""
    __tablename__ = 'ai_knowledge'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=True)  # např. 'procedures', 'contacts', 'resources'
    tags = db.Column(db.String(500), nullable=True)  # comma-separated
    created_by_id = db.Column(db.Integer, db.ForeignKey('ai_employee.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=True)  # Viditelné pro asistenta
    
    def __repr__(self):
        return f'<KnowledgeEntry {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'tags': self.tags.split(',') if self.tags else []
        }


class ServiceRecord(db.Model):
    """Záznam poskytnuté služby/akce"""
    __tablename__ = 'ai_service'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('ai_session.id'), nullable=False, index=True)
    service_type = db.Column(db.String(100), nullable=False)  # typ služby
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')  # pending, completed, cancelled
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<ServiceRecord {self.service_type} - {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'service_type': self.service_type,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class AssistantMemory(db.Model):
    """Paměť AI - co si asistent "pamatuje" o zaměstnanci/situaci"""
    __tablename__ = 'ai_memory'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('ai_employee.id'), nullable=False, index=True)
    key = db.Column(db.String(100), nullable=False)  # identifikátor paměti
    value = db.Column(db.Text, nullable=False)  # JSON obsah
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'key', name='unique_emp_key'),
    )
    
    def __repr__(self):
        return f'<AssistantMemory {self.employee_id} - {self.key}>'
