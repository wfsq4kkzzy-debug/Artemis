"""
AI Asistent pro správu projektů
- Komunikace přes Claude API
- Správa projektů, rozpočtů, výdajů, termínů
- Paměť konverzací
- Znalostní databáze
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from typing import List, Optional, Tuple, Dict
import json
import os
import re
from dotenv import load_dotenv

from models import db
from ai_executor import AIExecutor
from project_executor import ProjectExecutor

# Načti environment variables
load_dotenv()

# Vytvoř blueprint
ai_bp = Blueprint('ai_assistant', __name__, url_prefix='/ai', template_folder='templates', static_folder='static')

# ============================================================================
# MODELY PRO AI ASISTENTA
# ============================================================================

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


# ============================================================================
# AI ASISTENT SERVICE
# ============================================================================

class AIAssistantService:
    """Třída pro komunikaci s Claude API a správu AI asistenta"""
    
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.model = 'claude-sonnet-4-5-20250929'
        
        if not self.api_key:
            raise Exception("ANTHROPIC_API_KEY není nastaven v .env")
        
        # Inicializuj Anthropic client - bez httpx
        try:
            import anthropic
            # Přímý request bez httpx wrapper
            self.client = anthropic
            self.api_key_value = self.api_key
        except ImportError:
            raise Exception("Anthropic SDK není nainstalován. Spusť: pip install anthropic")
    
    def get_knowledge_base_context(self) -> str:
        """Vrátí celou znalostní databázi jako kontext"""
        entries = KnowledgeEntry.query.filter_by(is_public=True).all()
        
        if not entries:
            return "Znalostní databáze je prázdná."
        
        context = "=== ZNALOSTNÍ DATABÁZE ===\n\n"
        for entry in entries:
            context += f"### {entry.title}\n"
            context += f"Kategorie: {entry.category or 'Není zadána'}\n"
            context += f"Obsah:\n{entry.content}\n"
            if entry.tags:
                context += f"Tags: {entry.tags}\n"
            context += "\n---\n\n"
        
        return context
    
    def get_employee_memory(self, employee_id: int) -> str:
        """Vrátí paměť specifického zaměstnance"""
        memories = AssistantMemory.query.filter_by(employee_id=employee_id).all()
        
        if not memories:
            return ""
        
        memory_text = "=== PAMĚŤ O ZAMĚSTNANCI ===\n\n"
        for memory in memories:
            memory_text += f"**{memory.key}**: {memory.value}\n"
        
        return memory_text
    
    def build_system_prompt(self, employee: Employee, session: AISession, projekt_id: Optional[int] = None) -> str:
        """Vytvoří system prompt s kontextem"""
        
        knowledge_context = self.get_knowledge_base_context()
        employee_memory = self.get_employee_memory(employee.id)
        
        # Informace o projektu pokud existuje
        project_info = ""
        if projekt_id:
            project = ProjectExecutor.get_project_detail(projekt_id)
            if project.get("success"):
                project_info = f"""
=== AKTUÁLNÍ PROJEKT ===
Projekt: {project['nazev']}
Vedoucí: {project['vedouci'] or 'Není přiřazen'}
Status: {project['status']}
Rozpočet: {project['celkovy_rozpocet']} Kč
Vydaje: {project['celkove_vydaje']} Kč
Zbývá: {project['zbytek']} Kč
Termínů: {project['terminy']}
"""
        
        # Informace o aplikaci a jejích funkcích
        app_info = """
=== DOSTUPNÉ FUNKCE V APLIKACI ===

1. PROJEKTY:
   - Vytvořit projekt: "Vytvoř projekt s názvem X"
   - Zobrazit projekty: "Ukaž mi všechny projekty"
   - Detail projektu: "Ukaž detail projektu ID X"

2. ROZPOČET PROJEKTU:
   - Přidat rozpočet: "Přidej do rozpočtu категорию 'X' položku 'Y' s částkou Z Kč"
   - Zobrazit rozpočet: "Ukaž rozpočet projektu"
   - Stav rozpočtu: "Jaký je stav rozpočtu?"

3. VÝDAJE:
   - Přidat výdaj: "Přidej výdaj X Kč za 'popis' v kategorii 'Y'"
   - Zobrazit výdaje: "Ukaž všechny výdaje"
   - Zbývající rozpočet: "Kolik nám zbývá?"

4. TERMÍNY/MILESTONY:
   - Přidat termín: "Přidej termín 'název' na datum DD.MM.YYYY"
   - Zobrazit termíny: "Ukaž všechny termíny"
   - Status termínu: "Jaké jsou termíny projektu?"

5. KOMUNIKACE:
   - Přidat zprávu: "Zaznamenej poznámku: ..."
   - Zobrazit zprávy: "Ukaž všechny zprávy"

6. ZNALOSTI:
   - Přidat znalost: "Ulož znalost 'název' s obsahem '...'"
   - Zobrazit znalosti: "Jaké znalosti máme?"

KLÍČOVÉ POKYNY:
- Vždy si ujasni, který projekt řeším
- Když uživatel poprvé mluví, zeptej se, se kterým projektem chce pracovat
- Pokaždé, když provádíš akci, potvrď ji s výsledkem
- Komunikuj česky a buď přátelský
"""
        
        prompt = f"""Jsi AI asistent pro správu projektů v Knihovně Polička.

ZÁKLADNÍ INFORMACE:
- Jméno uživatele: {employee.name}
- Role: {employee.role}
- Aktuální čas: {datetime.utcnow().strftime('%d.%m.%Y %H:%M')}

{project_info}

{app_info}

{knowledge_context}

{employee_memory}

POKYNY:
1. Buď pomocný, profesionální a zdvořilý
2. Máš plný přístup ke všem projektům a jejich datům
3. Můžeš provádět všechny akce: vytvářet, upravovat, mazat
4. Vždy potvrď provedené akce s konkrétními výsledky
5. Když si nejsi jistý, zeptej se pro upřesnění
6. Komunikuj česky a přátelsky
7. Pomáhej uživateli spravovat projekty efektivně

Kontext relace: {session.context or 'Bez speciálního kontextu'}
"""
        return prompt
    
    def send_message(self, employee_id: int, session_id: int, user_message: str) -> Tuple[str, int]:
        """
        Odešle zprávu Claude a vrátí odpověď
        
        1. Nejdřív se pokusí rozpoznat příkazy z uživatelovy zprávy
        2. Pokud je příkaz, provede jej přes AIExecutor
        3. Pak pošle zprávu asistentovi s výsledky
        
        Returns:
            tuple: (odpověď asistenta, počet tokenů)
        """
        import requests
        
        # Získej zaměstnance a relaci
        employee = Employee.query.get(employee_id)
        session = AISession.query.get(session_id)
        
        if not employee or not session:
            raise ValueError("Zaměstnanec nebo relace nenalezeny")
        
        # Pokus se detekovat a provést příkazy
        execution_results = self._detect_and_execute_commands(user_message, session_id)
        
        # Přidej kontakt s výsledky do zprávy pro AI
        enhanced_message = user_message
        if execution_results:
            enhanced_message += "\n\n[VÝSLEDKY PROVEDENÝCH AKCÍ]\n"
            enhanced_message += json.dumps(execution_results, ensure_ascii=False, indent=2)
        
        # Urči si všechny zprávy v konverzaci
        messages = Message.query.filter_by(session_id=session_id).order_by(Message.created_at).all()
        
        # Přeformátuj pro API
        conversation = []
        for msg in messages:
            conversation.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Přidej novou zprávu s eventuálními výsledky akcí
        conversation.append({
            "role": "user",
            "content": enhanced_message
        })
        
        # Zavolej Claude API
        system_prompt = self.build_system_prompt(employee, session)
        
        headers = {
            "x-api-key": self.api_key_value,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": self.model,
            "max_tokens": 2048,
            "system": system_prompt,
            "messages": conversation
        }
        
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                json=data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            assistant_message = result['content'][0]['text']
            tokens_used = result.get('usage', {}).get('input_tokens', 0) + result.get('usage', {}).get('output_tokens', 0)
            
            return assistant_message, tokens_used
        except Exception as e:
            raise Exception(f"Chyba při komunikaci s Claude API: {str(e)}")
    
    def _detect_and_execute_commands(self, user_message: str, session_id: int) -> Optional[Dict]:
        """
        Detekuje příkazy v uživatelově zprávě a provádí je
        
        Příklady:
        - "Ukaž mi rozpočet" -> seznam položek
        - "Přidej nový výdaj 5000 Kč" -> add_expense
        """
        
        results = []
        keywords_query = ['rozpočet', 'polozka', 'položka', 'seznam', 'ukaž', 'ukaz', 'jaký', 'jaky', 'kolik', 'jak']
        keywords_employees = ['zaměstnanec', 'zamestnanec', 'osoba', 'pracovník', 'pracovnic', 'pracovníka', 'lidé', 'lide']
        keywords_status = ['stav', 'jak je', 'kolik', 'zbývá', 'zbyva', 'bilance', 'vydali', 'spálili', 'spali', 'vydaje']
        
        lower_msg = user_message.lower()
        
        # Detekce stavu rozpočtu (priorita)
        if any(k in lower_msg for k in keywords_status):
            try:
                result = AIExecutor.execute_command('get_budget_status')
                results.append({
                    "action": "get_budget_status",
                    "data": result.get('result', {})
                })
                
                summary = AIExecutor.execute_command('get_budget_summary')
                results.append({
                    "action": "get_budget_summary",
                    "data": summary.get('result', {})
                })
            except:
                pass
        
        # Detekce dotazů na rozpočet
        elif any(k in lower_msg for k in keywords_query):
            try:
                result = AIExecutor.execute_command('list_budget_items')
                results.append({
                    "action": "list_budget_items",
                    "data": result.get('result', [])[:10]  # Limit na prvních 10
                })
            except:
                pass
        
        # Detekce dotazů na zaměstnance
        elif any(k in lower_msg for k in keywords_employees):
            try:
                result = AIExecutor.execute_command('get_employees')
                results.append({
                    "action": "get_employees",
                    "data": result.get('result', [])
                })
            except:
                pass
        
        # Detekce přidávání výdajů (parsování čísla)
        elif 'přidej' in lower_msg or 'pridej' in lower_msg:
            try:
                import re
                numbers = re.findall(r'\d+(?:,\d+)?', user_message)
                if numbers and ('výdaj' in lower_msg or 'vydaj' in lower_msg or 'kč' in lower_msg):
                    # Pokus se detekovat ID položky a částku
                    castka = None
                    polozka_id = None
                    
                    # Hledej "ID XXX" nebo "položka XXX"
                    id_match = re.search(r'ID\s+(\d+)', user_message, re.IGNORECASE)
                    if id_match:
                        polozka_id = int(id_match.group(1))
                    
                    # Hledej "XXXX Kč" nebo jen první číslo
                    if numbers:
                        castka = float(numbers[0].replace(',', '.'))
                    
                    if castka and polozka_id:
                        result = AIExecutor.execute_command('add_expense', {
                            'polozka_id': polozka_id,
                            'castka': castka,
                            'popis': 'Přidáno AI asistentem'
                        })
                        results.append({
                            "action": "add_expense",
                            "result": result
                        })
            except:
                pass
        
        return results if results else None
    
    def save_message_pair(self, session_id: int, user_message: str, assistant_message: str, tokens_used: int):
        """Ulož pár zpráv do databáze"""
        
        user_msg = Message(
            session_id=session_id,
            role='user',
            content=user_message
        )
        
        asst_msg = Message(
            session_id=session_id,
            role='assistant',
            content=assistant_message,
            tokens_used=tokens_used
        )
        
        db.session.add(user_msg)
        db.session.add(asst_msg)
        db.session.commit()


# ============================================================================
# ROUTES - AI ASISTENT
# ============================================================================

@ai_bp.route('/')
def index():
    """Hlavní stránka - chat s AI"""
    # Kontrola API klíče
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key or api_key.startswith('sk-ant-your'):
        return render_template('ai/setup.html')
    
    # Získej nebo vytvoř defaultního uživatele
    user = Employee.query.filter_by(email='user@library.local').first()
    if not user:
        user = Employee(name='Ja', email='user@library.local', role='admin', active=True)
        db.session.add(user)
        db.session.commit()
    
    # Získej aktuální session (poslední aktivení)
    session = AISession.query.filter_by(
        employee_id=user.id, 
        is_archived=False
    ).order_by(AISession.updated_at.desc()).first()
    
    if not session:
        session = AISession(
            employee_id=user.id,
            title='Moje konverzace'
        )
        db.session.add(session)
        db.session.commit()
    
    return render_template('ai/index.html', session=session, user=user)


@ai_bp.route('/setup', methods=['POST'])
def setup():
    """Ulož API klíč"""
    data = request.get_json()
    api_key = data.get('api_key', '').strip()
    
    if not api_key:
        return jsonify({'error': 'API klíč nemůže být prázdný'}), 400
    
    if not api_key.startswith('sk-ant-'):
        return jsonify({'error': 'Neplatný formát API klíče. Měl by začínat na sk-ant-'}), 400
    
    # Ulož do .env souboru
    try:
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        
        # Přečti existující obsah
        content = ''
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                content = f.read()
        
        # Nahraď nebo přidej API klíč
        if 'ANTHROPIC_API_KEY=' in content:
            content = re.sub(r'ANTHROPIC_API_KEY=.*', f'ANTHROPIC_API_KEY={api_key}', content)
        else:
            if content and not content.endswith('\n'):
                content += '\n'
            content += f'ANTHROPIC_API_KEY={api_key}\n'
        
        # Ulož zpět
        with open(env_file, 'w') as f:
            f.write(content)
        
        # Aktualizuj v paměti aplikace
        os.environ['ANTHROPIC_API_KEY'] = api_key
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': f'Chyba při ukládání: {str(e)}'}), 500


def send_claude_message(system_prompt: str, user_message: str) -> Dict:
    """Pošle zprávu do Claude API"""
    import requests
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return {"error": "API klíč není konfigurován"}
    
    try:
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            },
            json={
                'model': 'claude-sonnet-4-5-20250929',
                'max_tokens': 1024,
                'system': system_prompt,
                'messages': [
                    {
                        'role': 'user',
                        'content': user_message
                    }
                ]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'content': data.get('content', [{}])[0].get('text', 'Chyba odpovědi'),
                'usage': data.get('usage', {})
            }
        else:
            return {'error': f'API error: {response.status_code}'}
    except Exception as e:
        return {'error': str(e)}


@ai_bp.route('/send-message', methods=['POST'])
def send_message():
    """Odeslání zprávy AI"""
    data = request.get_json()
    message_text = data.get('message', '').strip()
    session_id = data.get('session_id')
    projekt_id = data.get('projekt_id')
    
    if not message_text:
        return jsonify({'error': 'Zpráva je prázdná'}), 400
    
    # Dvě možnosti: project kontext nebo AI session
    if projekt_id:
        # Projekt kontexst - jednoduchý režim pro chat v projektu
        from models import Projekt, Zprava
        
        projekt = Projekt.query.get_or_404(projekt_id)
        
        try:
            # Vytvořit system prompt s project kontextem
            budgets = ProjectExecutor.get_project_budgets(projekt_id)
            expenses = ProjectExecutor.get_project_expenses(projekt_id)
            milestones = ProjectExecutor.get_project_milestones(projekt_id)
            
            # Formátuj rozpočet informace
            budget_lines = ""
            if budgets:
                budget_lines = "Rozpočet položky:\n"
                for b in budgets:
                    budget_lines += f"  - {b['kategorie']}: {b['popis']} = {b['castka']} Kč\n"
            else:
                budget_lines = "Zatím žádné rozpočtové položky"
            
            expense_lines = ""
            if expenses:
                expense_lines = "\nVydaje:\n"
                total_exp = sum([e['castka'] for e in expenses])
                for e in expenses:
                    expense_lines += f"  - {e['kategorie']}: {e['popis']} = {e['castka']} Kč\n"
                expense_lines += f"Celkem vydajů: {total_exp} Kč"
            else:
                expense_lines = "Zatím žádné zaznamenané výdaje"
            
            milestone_lines = ""
            if milestones:
                milestone_lines = "\nTermíny a milestony:\n"
                for m in milestones:
                    milestone_lines += f"  - {m['nazev']}: {m['datum_planovane'][:10]} (Status: {m['status']}, Zodpovědný: {m.get('zodpovedny', 'N/A')})\n"
            else:
                milestone_lines = "Zatím žádné termíny"
            
            system_prompt = f"""Jsi AI asistent pro správu projektů.

=== AKTUÁLNÍ PROJEKT ===
Projekt: {projekt.nazev}
Popis: {projekt.popis or 'Není popsán'}
Vedoucí: {projekt.vedouci or 'Není přiřazen'}
Status: {projekt.status}

=== ROZPOČET INFORMACE ===
{budget_lines}
{expense_lines}
{milestone_lines}

Odpovídej česky a buď přátelský. Poskytuj konkrétní informace o rozpočtu."""
            
            # Poslat zprávu do Claude API
            response = send_claude_message(
                system_prompt=system_prompt,
                user_message=message_text
            )
            
            if 'error' in response:
                return jsonify({'error': response['error']}), 500
            
            # Uložit zprávu do Zprava tabulky
            zprava = Zprava(
                projekt_id=projekt_id,
                autor='uživatel',
                obsah=message_text,
                typ='dotaz'
            )
            db.session.add(zprava)
            
            # Uložit odpověď AI
            odpoved = Zprava(
                projekt_id=projekt_id,
                autor='AI Asistent',
                obsah=response.get('content', 'Chyba odpovědi'),
                typ='odpověď'
            )
            db.session.add(odpoved)
            db.session.commit()
            
            return jsonify({
                'assistant_message': response.get('content', 'Chyba odpovědi'),
                'tokens_used': response.get('usage', {}).get('output_tokens', 0)
            })
        except Exception as e:
            return jsonify({'error': f'Project chat error: {str(e)}'}), 500
    
    elif session_id:
        # Klasická AI session
        session = AISession.query.get_or_404(session_id)
        user = session.employee
        
        try:
            service = AIAssistantService()
            assistant_response, tokens = service.send_message(user.id, session_id, message_text)
            
            # Ulož zprávy
            service.save_message_pair(session_id, message_text, assistant_response, tokens)
            
            return jsonify({
                'assistant_message': assistant_response,
                'tokens_used': tokens
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    else:
        return jsonify({'error': 'Projekt ID nebo Session ID chybí'}), 400


@ai_bp.route('/knowledge-base', methods=['GET', 'POST'])
def knowledge_base():
    """Správa znalostní databáze - pro administraci"""
    
    if request.method == 'POST':
        data = request.get_json()
        
        # Získej aktuálního uživatele
        user = Employee.query.filter_by(email='user@library.local').first()
        if not user:
            return jsonify({'error': 'Uživatel nenalezen'}), 404
        
        entry = KnowledgeEntry(
            title=data.get('title'),
            content=data.get('content'),
            category=data.get('category'),
            tags=data.get('tags'),
            created_by_id=user.id
        )
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({'success': True, 'id': entry.id})
    
    # GET - vrátí všechny záznamy
    entries = KnowledgeEntry.query.filter_by(is_public=True).order_by(KnowledgeEntry.updated_at.desc()).all()
    categories = db.session.query(KnowledgeEntry.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('ai/knowledge_base.html', entries=entries, categories=categories)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@ai_bp.route('/api/session/<int:session_id>/messages', methods=['GET'])
def api_session_messages(session_id: int):
    """Vrátí všechny zprávy ze relace"""
    messages = Message.query.filter_by(session_id=session_id).order_by(Message.created_at).all()
    return jsonify([msg.to_dict() for msg in messages])


@ai_bp.route('/api/knowledge', methods=['GET'])
def api_knowledge():
    """Vrátí všechny znalostní záznamy"""
    entries = KnowledgeEntry.query.filter_by(is_public=True).all()
    return jsonify([e.to_dict() for e in entries])
