"""
Flask Application Hub - Modulární architektura
Hlavní aplikace, která registruje všechny moduly
"""

from flask import Flask, render_template
from datetime import datetime
from dotenv import load_dotenv

# Načti .env soubor
load_dotenv()

# Import core
from core import db
from core.config import config

# Vytvoření Flask aplikace
app = Flask(__name__)
app.config.from_object(config['development'])

# Inicializace databáze
db.init_app(app)

# Custom Jinja2 filtry
def nl2br_filter(value):
    """Převádí nové řádky na HTML <br> tagy"""
    if value is None:
        return ''
    return str(value).replace('\n', '<br>\n')

app.jinja_env.filters['nl2br'] = nl2br_filter

# Import a registrace modulů
import json
from datetime import datetime as dt

# #region agent log
with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"app.py:24","message":"Before importing blueprints","data":{},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
# #endregion

try:
    from modules.budget.routes import budget_bp
    # #region agent log
    with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"app.py:29","message":"budget_bp imported","data":{},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
    # #endregion
except Exception as e:
    # #region agent log
    with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"app.py:32","message":"budget_bp import failed","data":{"error":str(e)},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
    # #endregion
    raise

from modules.projects.routes import project_bp
from modules.personnel.routes import personnel_bp
from modules.ai.routes import ai_bp
from modules.services.routes import services_bp
from modules.docs.routes import docs_bp

# Registrace blueprintů
# #region agent log
with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"app.py:42","message":"Before registering blueprints","data":{},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
# #endregion

app.register_blueprint(budget_bp)
app.register_blueprint(project_bp)
app.register_blueprint(personnel_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(services_bp)
app.register_blueprint(docs_bp)

# #region agent log
with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"app.py:50","message":"Main blueprints registered","data":{"blueprints":list(app.blueprints.keys())},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
# #endregion

# Import a registrace modulu users
from modules.users.routes import users_bp
app.register_blueprint(users_bp)

# #region agent log
with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"app.py:56","message":"All blueprints registered","data":{"blueprints":list(app.blueprints.keys())},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
# #endregion

# Kontextové procesory
@app.context_processor
def inject_globals():
    """Globální proměnné pro šablony"""
    from flask import session, has_request_context
    # Zkontroluj, zda je modul users zaregistrovaný
    has_users_module = 'users' in [bp.name for bp in app.blueprints.values()]
    
    # Zjisti aktuálního uživatele
    current_user_id = None
    current_user = None
    is_admin = False
    
    if has_request_context():
        current_user_id = session.get('current_user_id')
        
        # Načti aktuálního uživatele, pokud je nastaven
        if current_user_id and has_users_module:
            try:
                from modules.users.models import User
                current_user = User.query.get(current_user_id)
                if current_user:
                    is_admin = current_user.role == 'admin'
            except:
                pass
    
    # Načti seznam uživatelů pro dropdown (pouze pokud je admin)
    uzivatele = []
    if is_admin and has_users_module:
        try:
            from modules.users.models import User
            uzivatele = User.query.filter_by(aktivni=True).order_by(User.username).all()
        except:
            pass
    
    return {
        'now': datetime.utcnow(),
        'site_name': 'Artemis',
        'app_version': '0.75',
        'min': min,
        'max': max,
        'has_users_module': has_users_module,
        'current_user_id': current_user_id,
        'current_user': current_user,
        'is_admin': is_admin,
        'uzivatele': uzivatele,
    }

# ============================================================================
# ZÁKLADNÍ ROUTES (Hub)
# ============================================================================

@app.route('/')
def index():
    """Hlavní rozcestník - přesměruje na osobní dashboard pokud je uživatel přihlášen"""
    from flask import session, redirect, url_for
    
    # Načti seznam aktivních uživatelů pro výběr
    uzivatele = []
    try:
        from modules.users.models import User
        uzivatele = User.query.filter_by(aktivni=True).order_by(User.username).all()
    except:
        pass
    
    # Pokud je uživatel přihlášen, přesměruj na jeho dashboard
    current_user_id = session.get('current_user_id')
    if current_user_id:
        # Zkontroluj, zda uživatel stále existuje
        try:
            from modules.users.models import User
            user = User.query.get(current_user_id)
            if user and user.aktivni:
                return redirect(url_for('osobni_dashboard'))
            else:
                # Uživatel neexistuje nebo není aktivní, zruš session
                session.pop('current_user_id', None)
        except:
            session.pop('current_user_id', None)
    
    # Jinak zobraz hlavní stránku s výběrem uživatele
    return render_template('index.html', uzivatele=uzivatele)


@app.route('/dashboard')
def osobni_dashboard():
    """Osobní dashboard uživatele - zobrazí všechny jeho informace z databází"""
    from flask import session, redirect, url_for, flash
    from modules.projects.models import Projekt
    from modules.projects.executor import ProjectExecutor
    from modules.services.executor import ServicesExecutor
    from modules.services.models import SluzbaVynimka, SluzbaVymena
    from modules.budget.executor import BudgetExecutor
    
    # Získej aktuálního uživatele
    current_user_id = session.get('current_user_id')
    if not current_user_id:
        flash('Musíte být přihlášeni', 'warning')
        return redirect(url_for('index'))
    
    from modules.users.models import User
    user = User.query.get(current_user_id)
    if not user:
        flash('Uživatel neexistuje', 'danger')
        return redirect(url_for('index'))
    
    # Načti projekty uživatele
    try:
        all_projekty = Projekt.query.filter(
            Projekt.status.in_(['planovani', 'rozpracovani'])
        ).order_by(Projekt.datum_vytvoreni.desc()).all()
        
        # Filtruj projekty podle přístupu
        accessible_projects = []
        for projekt in all_projekty:
            access = ProjectExecutor.can_user_access_project(current_user_id, projekt.id)
            if access.get('can_access', False):
                accessible_projects.append(projekt)
        
        projekty = accessible_projects
        celkem_projektu = len(projekty)
        celkem_rozpocet = sum(p.rozpocet_float for p in projekty)
        celkem_vydaje = sum(p.celkove_vydaje for p in projekty)
        projekty_planovani = [p for p in projekty if p.status == 'planovani']
        projekty_rozpracovani = [p for p in projekty if p.status == 'rozpracovani']
    except Exception as e:
        projekty = []
        celkem_projektu = 0
        celkem_rozpocet = 0
        celkem_vydaje = 0
        projekty_planovani = []
        projekty_rozpracovani = []
    
    # Načti služby uživatele (pokud má personální záznam)
    statistiky_sluzeb = None
    sluzby = []
    vynimky = []
    vymeny = []
    if user.personnel_id:
        try:
            from datetime import date
            dnes = date.today()
            aktualni_rok = dnes.year
            nasledujici_rok = aktualni_rok + 1
            
            # Načti statistiky služeb pro aktuální rok i následující rok a sečti je
            statistiky_aktualni = ServicesExecutor.get_statistiky_zamestnance(user.personnel_id, aktualni_rok)
            statistiky_nasledujici = ServicesExecutor.get_statistiky_zamestnance(user.personnel_id, nasledujici_rok)
            
            # Slouč statistiky z obou let
            if statistiky_aktualni and statistiky_nasledujici:
                statistiky_sluzeb = {
                    'fixni': {
                        'tyden': statistiky_aktualni.get('fixni', {}).get('tyden', 0) + statistiky_nasledujici.get('fixni', {}).get('tyden', 0),
                        'mesic': statistiky_aktualni.get('fixni', {}).get('mesic', 0) + statistiky_nasledujici.get('fixni', {}).get('mesic', 0),
                        'rok': statistiky_aktualni.get('fixni', {}).get('rok', 0) + statistiky_nasledujici.get('fixni', {}).get('rok', 0)
                    },
                    'rotujici': {
                        'tyden': statistiky_aktualni.get('rotujici', {}).get('tyden', 0) + statistiky_nasledujici.get('rotujici', {}).get('tyden', 0),
                        'mesic': statistiky_aktualni.get('rotujici', {}).get('mesic', 0) + statistiky_nasledujici.get('rotujici', {}).get('mesic', 0),
                        'rok': statistiky_aktualni.get('rotujici', {}).get('rok', 0) + statistiky_nasledujici.get('rotujici', {}).get('rok', 0)
                    },
                    'nedele': {
                        'tyden': statistiky_aktualni.get('nedele', {}).get('tyden', 0) + statistiky_nasledujici.get('nedele', {}).get('tyden', 0),
                        'mesic': statistiky_aktualni.get('nedele', {}).get('mesic', 0) + statistiky_nasledujici.get('nedele', {}).get('mesic', 0),
                        'rok': statistiky_aktualni.get('nedele', {}).get('rok', 0) + statistiky_nasledujici.get('nedele', {}).get('rok', 0)
                    },
                    'celkem': {
                        'tyden': statistiky_aktualni.get('celkem', {}).get('tyden', 0) + statistiky_nasledujici.get('celkem', {}).get('tyden', 0),
                        'mesic': statistiky_aktualni.get('celkem', {}).get('mesic', 0) + statistiky_nasledujici.get('celkem', {}).get('mesic', 0),
                        'rok': statistiky_aktualni.get('celkem', {}).get('rok', 0) + statistiky_nasledujici.get('celkem', {}).get('rok', 0)
                    }
                }
            elif statistiky_aktualni:
                statistiky_sluzeb = statistiky_aktualni
            elif statistiky_nasledujici:
                statistiky_sluzeb = statistiky_nasledujici
            
            # Načti služby zaměstnance pro aktuální rok i následující rok
            vsechny_sluzby = []
            vsechny_sluzby.extend(ServicesExecutor.get_sluzby_pro_zamestnance(user.personnel_id, aktualni_rok))
            vsechny_sluzby.extend(ServicesExecutor.get_sluzby_pro_zamestnance(user.personnel_id, nasledujici_rok))
            
            # Filtruj pouze budoucí služby a seřaď podle data
            sluzby = []
            for s in vsechny_sluzby:
                if isinstance(s, dict):
                    datum_str = s.get('datum', '')
                    if datum_str and datum_str >= dnes.isoformat():
                        sluzby.append(s)
            sluzby.sort(key=lambda x: x.get('datum', ''))
            
            # Načti výjimky a výměny vytvořené uživatelem
            vynimky = SluzbaVynimka.query.filter_by(
                vytvoril_user_id=current_user_id,
                aktivni=True
            ).order_by(SluzbaVynimka.datum.desc()).limit(10).all()
            vymeny = SluzbaVymena.query.filter_by(
                vytvoril_user_id=current_user_id,
                aktivni=True
            ).order_by(SluzbaVymena.datum_vytvoreni.desc()).limit(10).all()
        except Exception as e:
            # Log chybu pro debugging
            import traceback
            print(f"Chyba při načítání služeb: {e}")
            traceback.print_exc()
            pass
    
    # Načti přehled rozpočtu (pokud je admin)
    budget_overview = None
    if user.role == 'admin':
        try:
            hlavni_rozpocet = BudgetExecutor.get_or_create_main_budget()
            overview = BudgetExecutor.get_budget_overview(hlavni_rozpocet.id)
            budget_overview = {
                'success': True,
                'budget': {
                    'nazev': hlavni_rozpocet.nazev,
                    'rok': hlavni_rozpocet.rok,
                    'castka_celkem': hlavni_rozpocet.castka_celkem_float,
                    'celkove_vydaje': hlavni_rozpocet.celkove_vydaje,
                    'celkove_vynosy': hlavni_rozpocet.celkove_vynosy,
                    'bilance': hlavni_rozpocet.bilance,
                    'zbytek': hlavni_rozpocet.zbytek,
                    'procento_vycerpano': hlavni_rozpocet.procento_vycerpano
                }
            }
        except:
            pass
    
    return render_template(
        'osobni_dashboard.html',
        user=user,
        projekty=projekty,
        celkem_projektu=celkem_projektu,
        celkem_rozpocet=celkem_rozpocet,
        celkem_vydaje=celkem_vydaje,
        projekty_planovani=projekty_planovani,
        projekty_rozpracovani=projekty_rozpracovani,
        statistiky_sluzeb=statistiky_sluzeb,
        sluzby=sluzby[:10],  # Posledních 10 služeb
        vynimky=vynimky,
        vymeny=vymeny,
        budget_overview=budget_overview
    )


@app.route('/switch-user', methods=['POST'])
def switch_user():
    """Přepne na jiného uživatele (pouze pro admin)"""
    from flask import session, request, redirect, url_for, flash
    
    user_id = request.form.get('user_id')
    
    # Pokud se odhlašuje (prázdné user_id)
    if not user_id or user_id == '':
        session.pop('current_user_id', None)
        flash('Odhlášení dokončeno', 'info')
        return redirect(url_for('index'))
    
    # Zkontroluj, zda je aktuální uživatel admin (pokud je přihlášen)
    current_user_id = session.get('current_user_id')
    if current_user_id:
        from modules.users.models import User
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            flash('Pouze administrátoři mohou přepínat uživatele', 'warning')
            return redirect(url_for('osobni_dashboard') if current_user_id else url_for('index'))
    
    # Zkontroluj, zda uživatel existuje
    try:
        from modules.users.models import User
        user = User.query.get(int(user_id))
        if user and user.aktivni:
            session['current_user_id'] = user.id
            flash(f'Přepnuto na uživatele: {user.jmeno_prijmeni}', 'success')
            return redirect(url_for('osobni_dashboard'))
        else:
            flash('Uživatel neexistuje nebo není aktivní', 'error')
    except (ValueError, Exception) as e:
        flash(f'Chyba při přepínání uživatele: {str(e)}', 'error')
    
    return redirect(url_for('osobni_dashboard') if session.get('current_user_id') else url_for('index'))


@app.route('/dashboard-old')
def dashboard():
    """Hlavní dashboard - nový přehledný dashboard"""
    from flask import request
    from modules.budget.executor import BudgetExecutor
    from modules.budget.models import Budget, BudgetCategory, Expense
    from modules.projects.models import Projekt
    
    rok = request.args.get('rok', datetime.utcnow().year, type=int)
    
    # Hlavní rozpočet (vytvoří se automaticky pokud neexistuje)
    hlavni_rozpocet = BudgetExecutor.get_or_create_main_budget(rok)
    overview = BudgetExecutor.get_budget_overview(hlavni_rozpocet.id)
    
    # Pokud není hlavní rozpočet, použij starý systém pro kompatibilitu
    if not hlavni_rozpocet:
        from modules.budget.models import UctovaSkupina, RozpoctovaPolozka, Vydaj
        
        naklady_celkem = db.session.query(db.func.sum(RozpoctovaPolozka.rozpocet)).join(
            UctovaSkupina
        ).filter(
            (UctovaSkupina.typ == 'naklad') & (RozpoctovaPolozka.rok == rok)
        ).scalar() or 0
        
        vynos_celkem = db.session.query(db.func.sum(RozpoctovaPolozka.rozpocet)).join(
            UctovaSkupina
        ).filter(
            (UctovaSkupina.typ == 'vynos') & (RozpoctovaPolozka.rok == rok)
        ).scalar() or 0
        
        dnes = datetime.utcnow()
        naklady_vydaje = db.session.query(db.func.sum(Vydaj.castka)).join(
            RozpoctovaPolozka
        ).join(
            UctovaSkupina
        ).filter(
            (UctovaSkupina.typ == 'naklad') & 
            (RozpoctovaPolozka.rok == rok) &
            (Vydaj.datum <= dnes)
        ).scalar() or 0
        
        vynos_vydaje = db.session.query(db.func.sum(Vydaj.castka)).join(
            RozpoctovaPolozka
        ).join(
            UctovaSkupina
        ).filter(
            (UctovaSkupina.typ == 'vynos') & 
            (RozpoctovaPolozka.rok == rok) &
            (Vydaj.datum <= dnes)
        ).scalar() or 0
        
        skupiny_naklady = UctovaSkupina.query.filter_by(typ='naklad').order_by(UctovaSkupina.ucet).all()
        skupiny_vynos = UctovaSkupina.query.filter_by(typ='vynos').order_by(UctovaSkupina.ucet).all()
        
        return render_template(
            'dashboard.html',
            rok=rok,
            naklady_celkem=float(naklady_celkem),
            vynos_celkem=float(vynos_celkem),
            naklady_vydaje=float(naklady_vydaje),
            vynos_vydaje=float(vynos_vydaje),
            bilance=float(vynos_celkem - naklady_celkem),
            skupiny_naklady=skupiny_naklady,
            skupiny_vynos=skupiny_vynos,
            dnes=dnes,
            hlavni_rozpocet=None
        )
    
    # Nový systém - hlavní rozpočet existuje
    dnes = datetime.utcnow()
    
    # Měsíční přehledy (výdaje i výnosy)
    mesicni = BudgetExecutor.get_monthly_overview(hlavni_rozpocet.id, rok)
    
    # Poslední výdaje
    posledni_vydaje = Expense.query.filter_by(
        budget_id=hlavni_rozpocet.id
    ).order_by(Expense.datum.desc()).limit(10).all()
    
    # Projekty - všechny aktivní
    from modules.projects.models import Projekt
    projekty = Projekt.query.filter(
        Projekt.status.in_(['planovani', 'rozpracovani'])
    ).all()
    
    return render_template(
        'dashboard_new.html',
        hlavni_rozpocet=hlavni_rozpocet,
        overview=overview,
        mesicni=mesicni,
        posledni_vydaje=posledni_vydaje,
        projekty=projekty,
        rok=rok,
        dnes=dnes
    )


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Chyba 404"""
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Chyba 500"""
    db.session.rollback()
    return render_template('errors/500.html'), 500


@app.shell_context_processor
def make_shell_context():
    """Pro Flask shell"""
    from modules.budget.models import UctovaSkupina, RozpoctovaPolozka, Vydaj
    from modules.personnel.models import ZamestnanecAOON
    
    return {
        'db': db,
        'UctovaSkupina': UctovaSkupina,
        'RozpoctovaPolozka': RozpoctovaPolozka,
        'Vydaj': Vydaj,
        'ZamestnanecAOON': ZamestnanecAOON,
    }


if __name__ == '__main__':
    with app.app_context():
        # Importuj všechny modely a vytvoř tabulky
        from modules.budget.models import UctovaSkupina, RozpoctovaPolozka, Vydaj, Budget, BudgetCategory, BudgetItem, Expense, Revenue, MonthlyBudgetItem
        from modules.projects.models import Projekt, BudgetProjektu, VydajProjektu, Termin, Zprava, Znalost
        from modules.personnel.models import ZamestnanecAOON
        from modules.ai.models import Employee, AISession, Message, KnowledgeEntry, ServiceRecord, AssistantMemory
        from modules.users.models import User, UserProject, UserConnection, SharedChat, UserMessage, UserNotification
        
        db.create_all()
        
        # Projekty a rozpočty jsou zcela oddělené - žádné propojení
    
    app.run(debug=True, host='0.0.0.0', port=5001)
