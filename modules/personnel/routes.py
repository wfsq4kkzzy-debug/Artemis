"""
Personnel Routes - Routy pro modul personální agendy
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from core import db
from .models import ZamestnanecAOON
import sys
import os
# Přidání root adresáře do path pro import forms
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from forms import PridatZamestnanceForm

personnel_bp = Blueprint('personnel', __name__, url_prefix='/personalni-agenda')


@personnel_bp.route('/')
def seznam():
    """Seznam zaměstnanců a brigádníků - rozděleno do sekcí"""
    typ_filter = request.args.get('typ', '', type=str)
    
    query = ZamestnanecAOON.query.filter_by(aktivni=True)
    
    if typ_filter:
        query = query.filter_by(typ=typ_filter)
    
    vsechny = query.order_by(ZamestnanecAOON.prijmeni, ZamestnanecAOON.jmeno).all()
    
    # Rozděl na zaměstnance (důležitější) a brigádníky
    zamestnanci = [p for p in vsechny if p.typ == 'zamestnanec']
    brigadnici = [p for p in vsechny if p.typ in ['brigadnik', 'oon']]
    
    return render_template(
        'personalni/seznam.html',
        zamestnanci=zamestnanci,
        brigadnici=brigadnici,
        typ_filter=typ_filter
    )


@personnel_bp.route('/pridat', methods=['GET', 'POST'])
def pridat():
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
            return redirect(url_for('personnel.seznam'))
        except Exception as e:
            db.session.rollback()
            flash(f'Chyba při ukládání: {str(e)}', 'danger')
    
    return render_template('personalni/pridat.html', form=form)


@personnel_bp.route('/upravit/<int:zamestnanec_id>', methods=['GET', 'POST'])
def upravit(zamestnanec_id):
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
            return redirect(url_for('personnel.seznam'))
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


@personnel_bp.route('/<int:zamestnanec_id>/smazat', methods=['POST'])
def smazat(zamestnanec_id):
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
    
    return redirect(url_for('personnel.seznam'))




