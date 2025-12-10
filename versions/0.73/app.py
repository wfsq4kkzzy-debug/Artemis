from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from decimal import Decimal
from datetime import datetime
import os
from dotenv import load_dotenv

# Načti .env soubor
load_dotenv()

from config import config
from models import (
    db, UctovaSkupina, RozpoctovaPolozka, Vydaj, ZamestnanecAOON,
    Projekt, BudgetProjektu, VydajProjektu, Termin, Zprava, Znalost
)
from forms import (
    NovaRozpoctovaPolozkaBez, UpravitRozpocetPolozkuForm, 
    PridatVydajForm, FilterForm, PridatZamestnanceForm
)

# Vytvoření Flask aplikace
app = Flask(__name__)
app.config.from_object(config['development'])

# Inicializace databáze
db.init_app(app)

# Import a registrace blueprintů
from ai_assistant import ai_bp
from project_routes import project_bp
app.register_blueprint(ai_bp)
app.register_blueprint(project_bp)

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
# ROZPOČET - ROUTES
# ============================================================================

@app.route('/')
@app.route('/dashboard')
def dashboard():
    """Hlavní dashboard"""
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
    
    # Skupiny
    skupiny_naklady = UctovaSkupina.query.filter_by(typ='naklad').order_by(UctovaSkupina.ucet).all()
    skupiny_vynos = UctovaSkupina.query.filter_by(typ='vynos').order_by(UctovaSkupina.ucet).all()
    
    return render_template(
        'dashboard.html',
        rok=rok,
        naklady_celkem=float(naklady_celkem),
        vynos_celkem=float(vynos_celkem),
        bilance=float(vynos_celkem - naklady_celkem),
        skupiny_naklady=skupiny_naklady,
        skupiny_vynos=skupiny_vynos
    )


@app.route('/rozpocet/seznam')
def seznam_rozpoctu():
    """Seznam všech rozpočtových položek"""
    rok = request.args.get('rok', 2026, type=int)
    uctova_skupina_id = request.args.get('uctova_skupina', 0, type=int)
    typ_filter = request.args.get('typ', '', type=str)
    
    # Základní query
    query = RozpoctovaPolozka.query.join(UctovaSkupina).filter(
        RozpoctovaPolozka.rok == rok
    )
    
    # Filtry
    if uctova_skupina_id:
        query = query.filter(RozpoctovaPolozka.uctova_skupina_id == uctova_skupina_id)
    
    if typ_filter:
        query = query.filter(UctovaSkupina.typ == typ_filter)
    
    polozky = query.order_by(
        UctovaSkupina.ucet,
        RozpoctovaPolozka.analyticky_ucet,
        RozpoctovaPolozka.nazev
    ).all()
    
    # Formulář pro filtrování
    form = FilterForm()
    
    # Získat všechny účtové skupiny pro výběr
    uctove_skupiny = UctovaSkupina.query.order_by(UctovaSkupina.ucet).all()
    
    # Souhrny
    total_rozpocet = sum(float(p.rozpocet) for p in polozky)
    total_vydaje = db.session.query(db.func.sum(Vydaj.castka)).filter(
        Vydaj.rozpoctova_polozka_id.in_([p.id for p in polozky])
    ).scalar() or 0
    
    return render_template(
        'rozpocet/seznam.html',
        polozky=polozky,
        rok=rok,
        form=form,
        uctove_skupiny=uctove_skupiny,
        total_rozpocet=total_rozpocet,
        total_vydaje=float(total_vydaje)
    )


@app.route('/rozpocet/nova-polozka', methods=['GET', 'POST'])
def nova_rozpoctova_polozka():
    """Přidat novou rozpočtovou položku"""
    form = NovaRozpoctovaPolozkaBez()
    
    if form.validate_on_submit():
        try:
            polozka = RozpoctovaPolozka(
                rok=2026,
                uctova_skupina_id=form.uctova_skupina.data,
                analyticky_ucet=form.analyticky_ucet.data,
                nazev=form.nazev.data,
                rozpocet=form.rozpocet.data,
                poznamka=form.poznamka.data
            )
            db.session.add(polozka)
            db.session.commit()
            
            flash(f'Položka "{polozka.nazev}" byla přidána!', 'success')
            return redirect(url_for('seznam_rozpoctu'))
        except Exception as e:
            db.session.rollback()
            flash(f'Chyba při ukládání: {str(e)}', 'danger')
    
    return render_template('rozpocet/nova_polozka.html', form=form)


@app.route('/rozpocet/upravit/<int:polozka_id>', methods=['GET', 'POST'])
def upravit_rozpoctovou_polozku(polozka_id):
    """Upravit rozpočtovou položku"""
    polozka = RozpoctovaPolozka.query.get_or_404(polozka_id)
    form = UpravitRozpocetPolozkuForm()
    
    if form.validate_on_submit():
        try:
            polozka.nazev = form.nazev.data
            polozka.rozpocet = form.rozpocet.data
            polozka.poznamka = form.poznamka.data
            db.session.commit()
            
            flash(f'Položka "{polozka.nazev}" byla aktualizována!', 'success')
            return redirect(url_for('seznam_rozpoctu'))
        except Exception as e:
            db.session.rollback()
            flash(f'Chyba při ukládání: {str(e)}', 'danger')
    
    elif request.method == 'GET':
        form.nazev.data = polozka.nazev
        form.rozpocet.data = polozka.rozpocet
        form.poznamka.data = polozka.poznamka
    
    return render_template(
        'rozpocet/upravit_polozku.html',
        form=form,
        polozka=polozka
    )


@app.route('/rozpocet/smazat/<int:polozka_id>', methods=['POST'])
def smazat_rozpoctovou_polozku(polozka_id):
    """Smazat rozpočtovou položku"""
    polozka = RozpoctovaPolozka.query.get_or_404(polozka_id)
    nazev = polozka.nazev
    
    try:
        # Smazat všechny přidružené výdaje
        Vydaj.query.filter_by(rozpoctova_polozka_id=polozka_id).delete()
        db.session.delete(polozka)
        db.session.commit()
        
        flash(f'Položka "{nazev}" byla smazána!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Chyba při mazání: {str(e)}', 'danger')
    
    return redirect(url_for('seznam_rozpoctu'))


@app.route('/rozpocet/polozka/<int:polozka_id>')
def detail_rozpoctove_polozky(polozka_id):
    """Detail rozpočtové položky s výdaji"""
    polozka = RozpoctovaPolozka.query.get_or_404(polozka_id)
    
    # Výdaje pro tuto položku
    vydaje = Vydaj.query.filter_by(
        rozpoctova_polozka_id=polozka_id
    ).order_by(Vydaj.datum.desc()).all()
    
    total_vydaje = sum(float(v.castka) for v in vydaje)
    zbytek = float(polozka.rozpocet) - total_vydaje
    
    return render_template(
        'rozpocet/detail_polozky.html',
        polozka=polozka,
        vydaje=vydaje,
        total_vydaje=total_vydaje,
        zbytek=zbytek
    )


@app.route('/rozpocet/polozka/<int:polozka_id>/vydaj/nova', methods=['GET', 'POST'])
def pridat_vydaj(polozka_id):
    """Přidat nový výdaj pro položku"""
    polozka = RozpoctovaPolozka.query.get_or_404(polozka_id)
    form = PridatVydajForm()
    
    if form.validate_on_submit():
        try:
            vydaj = Vydaj(
                rozpoctova_polozka_id=polozka_id,
                castka=form.castka.data,
                popis=form.popis.data,
                cis_faktury=form.cis_faktury.data,
                dodavatel=form.dodavatel.data,
                datum=datetime.utcnow()
            )
            db.session.add(vydaj)
            db.session.commit()
            
            flash(f'Výdaj {form.castka.data} Kč byl přidán!', 'success')
            return redirect(url_for('detail_rozpoctove_polozky', polozka_id=polozka_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Chyba při ukládání: {str(e)}', 'danger')
    
    return render_template(
        'rozpocet/pridat_vydaj.html',
        form=form,
        polozka=polozka
    )


@app.route('/rozpocet/vydaj/<int:vydaj_id>/smazat', methods=['POST'])
def smazat_vydaj(vydaj_id):
    """Smazat výdaj"""
    vydaj = Vydaj.query.get_or_404(vydaj_id)
    polozka_id = vydaj.rozpoctova_polozka_id
    
    try:
        db.session.delete(vydaj)
        db.session.commit()
        flash('Výdaj byl smazán!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Chyba při mazání: {str(e)}', 'danger')
    
    return redirect(url_for('detail_rozpoctove_polozky', polozka_id=polozka_id))


# ============================================================================
# PERSONÁLNÍ AGENDA - ROUTES
# ============================================================================

@app.route('/personalni-agenda')
def seznam_lidi():
    """Seznam zaměstnanců a OON"""
    typ_filter = request.args.get('typ', '', type=str)
    
    query = ZamestnanecAOON.query.filter_by(aktivni=True)
    
    if typ_filter:
        query = query.filter_by(typ=typ_filter)
    
    lide = query.order_by(ZamestnanecAOON.prijmeni, ZamestnanecAOON.jmeno).all()
    
    return render_template(
        'personalni/seznam.html',
        lide=lide,
        typ_filter=typ_filter
    )


@app.route('/personalni-agenda/pridat', methods=['GET', 'POST'])
def pridat_cloveka():
    """Přidat zaměstnance nebo OON"""
    form = PridatZamestnanceForm()
    
    if form.validate_on_submit():
        try:
            clovek = ZamestnanecAOON(
                jmeno=form.jmeno.data,
                prijmeni=form.prijmeni.data,
                typ=form.typ.data,
                ic_dph=form.ic_dph.data,
                pozice=form.pozice.data,
                uvazek=form.uvazek.data or 100,
                hodinova_sazba=form.hodinova_sazba.data or None,
                mesicni_plat=form.mesicni_plat.data or None
            )
            db.session.add(clovek)
            db.session.commit()
            
            flash(f'{clovek.jmeno_plne} byl/a přidán/a!', 'success')
            return redirect(url_for('seznam_lidi'))
        except Exception as e:
            db.session.rollback()
            flash(f'Chyba při ukládání: {str(e)}', 'danger')
    
    return render_template('personalni/pridat.html', form=form)


@app.route('/personalni-agenda/upravit/<int:zamestnanec_id>', methods=['GET', 'POST'])
def upravit_cloveka(zamestnanec_id):
    """Upravit zaměstnance nebo OON"""
    clovek = ZamestnanecAOON.query.get_or_404(zamestnanec_id)
    form = PridatZamestnanceForm()
    
    if form.validate_on_submit():
        try:
            clovek.jmeno = form.jmeno.data
            clovek.prijmeni = form.prijmeni.data
            clovek.typ = form.typ.data
            clovek.ic_dph = form.ic_dph.data
            clovek.pozice = form.pozice.data
            clovek.uvazek = form.uvazek.data or 100
            clovek.hodinova_sazba = form.hodinova_sazba.data or None
            clovek.mesicni_plat = form.mesicni_plat.data or None
            
            db.session.commit()
            flash(f'{clovek.jmeno_plne} byl/a upraven/a!', 'success')
            return redirect(url_for('seznam_lidi'))
        except Exception as e:
            db.session.rollback()
            flash(f'Chyba při ukládání: {str(e)}', 'danger')
    elif request.method == 'GET':
        form.jmeno.data = clovek.jmeno
        form.prijmeni.data = clovek.prijmeni
        form.typ.data = clovek.typ
        form.ic_dph.data = clovek.ic_dph
        form.pozice.data = clovek.pozice
        form.uvazek.data = float(clovek.uvazek) if clovek.uvazek else 100
        form.hodinova_sazba.data = float(clovek.hodinova_sazba) if clovek.hodinova_sazba else None
        form.mesicni_plat.data = float(clovek.mesicni_plat) if clovek.mesicni_plat else None
    
    return render_template('personalni/upravit.html', form=form, clovek=clovek)


@app.route('/personalni-agenda/<int:zamestnanec_id>/smazat', methods=['POST'])
def smazat_cloveka(zamestnanec_id):
    """Smazat zaměstnance nebo OON"""
    clovek = ZamestnanecAOON.query.get_or_404(zamestnanec_id)
    jmeno = clovek.jmeno_plne
    
    try:
        clovek.aktivni = False
        db.session.commit()
        flash(f'{jmeno} byl/a deaktivován/a!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Chyba při mazání: {str(e)}', 'danger')
    
    return redirect(url_for('seznam_lidi'))


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
    return {
        'db': db,
        'UctovaSkupina': UctovaSkupina,
        'RozpoctovaPolozka': RozpoctovaPolozka,
        'Vydaj': Vydaj,
        'ZamestnanecAOON': ZamestnanecAOON,
    }


if __name__ == '__main__':
    with app.app_context():
        # Importuj AI modely a vytvoř tabulky
        from ai_assistant import Employee, AISession, Message, KnowledgeEntry, ServiceRecord, AssistantMemory
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
