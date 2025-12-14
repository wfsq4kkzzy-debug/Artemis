"""
Budget Routes - Routy pro modul rozpočtu
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from core import db
from .models import UctovaSkupina, RozpoctovaPolozka, Vydaj
from forms import (
    NovaRozpoctovaPolozkaBez, UpravitRozpocetPolozkuForm, 
    PridatVydajForm, FilterForm
)

budget_bp = Blueprint('budget', __name__, url_prefix='/rozpocet')


@budget_bp.route('/seznam')
def seznam():
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
    # Výdaje pouze do aktuálního data
    dnes = datetime.utcnow()
    total_vydaje = db.session.query(db.func.sum(Vydaj.castka)).filter(
        Vydaj.rozpoctova_polozka_id.in_([p.id for p in polozky]),
        Vydaj.datum <= dnes
    ).scalar() or 0
    
    # Pro každou položku předpočítat výdaje do aktuálního data
    polozky_s_vydaji = []
    for polozka in polozky:
        vydaje_aktualni = polozka.celkove_vydaje_aktualni
        polozky_s_vydaji.append({
            'polozka': polozka,
            'vydaje_aktualni': vydaje_aktualni,
            'zbytek_aktualni': polozka.zbytek_aktualni
        })
    
    return render_template(
        'rozpocet/seznam.html',
        polozky_s_vydaji=polozky_s_vydaji,
        polozky=polozky,  # Pro zpětnou kompatibilitu
        rok=rok,
        form=form,
        uctove_skupiny=uctove_skupiny,
        total_rozpocet=total_rozpocet,
        total_vydaje=float(total_vydaje),
        dnes=dnes
    )


@budget_bp.route('/nova-polozka', methods=['GET', 'POST'])
def nova_polozka():
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
            return redirect(url_for('budget.seznam'))
        except Exception as e:
            db.session.rollback()
            flash(f'Chyba při ukládání: {str(e)}', 'danger')
    
    return render_template('rozpocet/nova_polozka.html', form=form)


@budget_bp.route('/upravit/<int:polozka_id>', methods=['GET', 'POST'])
def upravit_polozku(polozka_id):
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
            return redirect(url_for('budget.seznam'))
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


@budget_bp.route('/smazat/<int:polozka_id>', methods=['POST'])
def smazat_polozku(polozka_id):
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
    
    return redirect(url_for('budget.seznam'))


@budget_bp.route('/polozka/<int:polozka_id>')
def detail_polozky(polozka_id):
    """Detail rozpočtové položky s výdaji"""
    polozka = RozpoctovaPolozka.query.get_or_404(polozka_id)
    
    # Výdaje pouze do aktuálního data
    dnes = datetime.utcnow()
    vydaje = Vydaj.query.filter_by(rozpoctova_polozka_id=polozka_id).filter(
        Vydaj.datum <= dnes
    ).order_by(Vydaj.datum.desc()).all()
    
    # Všechny výdaje pro referenci
    vydaje_vse = Vydaj.query.filter_by(rozpoctova_polozka_id=polozka_id).order_by(Vydaj.datum.desc()).all()
    
    return render_template(
        'rozpocet/detail_polozky.html',
        polozka=polozka,
        vydaje=vydaje,
        vydaje_vse=vydaje_vse,
        dnes=dnes
    )


@budget_bp.route('/polozka/<int:polozka_id>/vydaj/nova', methods=['GET', 'POST'])
def pridat_vydaj(polozka_id):
    """Přidat výdaj k rozpočtové položce"""
    polozka = RozpoctovaPolozka.query.get_or_404(polozka_id)
    form = PridatVydajForm()
    
    if form.validate_on_submit():
        try:
            vydaj = Vydaj(
                rozpoctova_polozka_id=polozka_id,
                castka=form.castka.data,
                datum=form.datum.data or datetime.utcnow(),
                popis=form.popis.data,
                cis_faktury=form.cis_faktury.data,
                dodavatel=form.dodavatel.data
            )
            db.session.add(vydaj)
            db.session.commit()
            
            flash(f'Výdaj {form.castka.data} Kč byl přidán!', 'success')
            return redirect(url_for('budget.detail_polozky', polozka_id=polozka_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Chyba při ukládání: {str(e)}', 'danger')
    
    return render_template('rozpocet/pridat_vydaj.html', form=form, polozka=polozka)


@budget_bp.route('/vydaj/<int:vydaj_id>/smazat', methods=['POST'])
def smazat_vydaj(vydaj_id):
    """Smazat výdaj"""
    vydaj = Vydaj.query.get_or_404(vydaj_id)
    polozka_id = vydaj.rozpoctova_polozka_id
    castka = vydaj.castka
    
    try:
        db.session.delete(vydaj)
        db.session.commit()
        
        flash(f'Výdaj {castka} Kč byl smazán!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Chyba při mazání: {str(e)}', 'danger')
    
    return redirect(url_for('budget.detail_polozky', polozka_id=polozka_id))
