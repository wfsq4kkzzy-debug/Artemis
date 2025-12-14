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

# Import a registrace modulů
from modules.budget.routes import budget_bp
from modules.projects.routes import project_bp
from modules.personnel.routes import personnel_bp
from modules.ai.routes import ai_bp

# Registrace blueprintů
app.register_blueprint(budget_bp)
app.register_blueprint(project_bp)
app.register_blueprint(personnel_bp)
app.register_blueprint(ai_bp)

# Kontextové procesory
@app.context_processor
def inject_globals():
    """Globální proměnné pro šablony"""
    return {
        'now': datetime.utcnow(),
        'site_name': 'Správa rozpočtu Knihovny Polička',
        'min': min,
        'max': max,
    }

# ============================================================================
# ZÁKLADNÍ ROUTES (Hub)
# ============================================================================

@app.route('/')
def index():
    """Hlavní rozcestník"""
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    """Hlavní dashboard"""
    from flask import request
    from modules.budget.models import UctovaSkupina, RozpoctovaPolozka, Vydaj
    
    rok = request.args.get('rok', 2026, type=int)
    
    # Souhrny
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
    
    # Výdaje pouze do aktuálního data
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
    
    # Skupiny
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
        from modules.budget.models import UctovaSkupina, RozpoctovaPolozka, Vydaj
        from modules.projects.models import Projekt, BudgetProjektu, VydajProjektu, Termin, Zprava, Znalost
        from modules.personnel.models import ZamestnanecAOON
        from modules.ai.models import Employee, AISession, Message, KnowledgeEntry, ServiceRecord, AssistantMemory
        
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
