"""
Routes pro modul Dokumentace
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from core import db
from .models import ChangeLog

docs_bp = Blueprint('docs', __name__, url_prefix='/dokumentace')


@docs_bp.route('/')
def index():
    """Hlavní stránka dokumentace"""
    return render_template('docs/index.html')


@docs_bp.route('/struktura')
def struktura():
    """Struktura systému"""
    return render_template('docs/struktura.html')


@docs_bp.route('/moduly')
def moduly():
    """Dokumentace modulů"""
    return render_template('docs/moduly.html')


@docs_bp.route('/api')
def api():
    """API dokumentace"""
    return render_template('docs/api.html')


@docs_bp.route('/databaze')
def databaze():
    """Dokumentace databáze - struktura tabulek a vztahů"""
    from sqlalchemy import inspect
    from core import db
    
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    # Získej informace o všech tabulkách
    tables_info = {}
    for table_name in sorted(tables):
        columns = inspector.get_columns(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)
        indexes = inspector.get_indexes(table_name)
        primary_keys = inspector.get_pk_constraint(table_name)
        unique_constraints = inspector.get_unique_constraints(table_name)
        
        tables_info[table_name] = {
            'columns': columns,
            'foreign_keys': foreign_keys,
            'indexes': indexes,
            'primary_keys': primary_keys.get('constrained_columns', []),
            'unique_constraints': unique_constraints
        }
    
    # Získej počet záznamů v každé tabulce
    from sqlalchemy import text
    table_counts = {}
    for table_name in tables:
        try:
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            table_counts[table_name] = result.scalar()
        except:
            table_counts[table_name] = 0
    
    # Seřaď názvy tabulek
    sorted_table_names = sorted(tables_info.keys())
    
    return render_template(
        'docs/databaze.html',
        tables_info=tables_info,
        table_counts=table_counts,
        sorted_table_names=sorted_table_names
    )


@docs_bp.route('/changelog')
def changelog():
    """Logy změn"""
    # Získej všechny aktivní logy změn, seřazené podle data (nejnovější první)
    logs = ChangeLog.query.filter_by(aktivni=True).order_by(ChangeLog.datum.desc()).all()
    
    # Seskup podle verze
    logs_by_version = {}
    for log in logs:
        verze = log.verze or 'Bez verze'
        if verze not in logs_by_version:
            logs_by_version[verze] = []
        logs_by_version[verze].append(log)
    
    return render_template('docs/changelog.html', logs=logs, logs_by_version=logs_by_version)


@docs_bp.route('/changelog/novy', methods=['GET', 'POST'])
def novy_changelog():
    """Vytvoření nového logu změny"""
    if request.method == 'POST':
        log = ChangeLog(
            verze=request.form.get('verze'),
            typ=request.form.get('typ', 'zmena'),
            modul=request.form.get('modul'),
            nadpis=request.form.get('nadpis'),
            popis=request.form.get('popis'),
            autor=request.form.get('autor')
        )
        
        db.session.add(log)
        db.session.commit()
        
        flash('Log změny byl přidán', 'success')
        return redirect(url_for('docs.changelog'))
    
    moduly_list = ['budget', 'projects', 'personnel', 'users', 'services', 'ai', 'core']
    typy = [
        ('zmena', 'Změna'),
        ('pridano', 'Přidáno'),
        ('oprava', 'Oprava'),
        ('odstraneno', 'Odstraněno'),
        ('vylepseni', 'Vylepšení')
    ]
    
    return render_template('docs/novy_changelog.html', moduly_list=moduly_list, typy=typy)


@docs_bp.route('/changelog/<int:log_id>/smazat', methods=['POST'])
def smazat_changelog(log_id):
    """Smazání logu změny"""
    log = ChangeLog.query.get_or_404(log_id)
    log.aktivni = False
    db.session.commit()
    
    flash('Log změny byl smazán', 'success')
    return redirect(url_for('docs.changelog'))
