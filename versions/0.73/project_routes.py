"""
Project Routes - Routy pro správu projektů
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from models import db, Projekt, BudgetProjektu, VydajProjektu, Termin, Zprava, Znalost
from project_executor import ProjectExecutor

project_bp = Blueprint('projects', __name__, url_prefix='/projekty')


# ============================================================================
# HLAVNÍ STRÁNKY
# ============================================================================

@project_bp.route('/')
def seznam():
    """Hlavní seznam projektů"""
    status_filter = request.args.get('status', '', type=str)
    
    query = Projekt.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    projekty = query.order_by(Projekt.datum_vytvoreni.desc()).all()
    
    return render_template(
        'projekty/seznam.html',
        projekty=projekty,
        status_filter=status_filter
    )


@project_bp.route('/novy', methods=['GET', 'POST'])
def novy():
    """Vytvoření nového projektu"""
    if request.method == 'POST':
        result = ProjectExecutor.create_project(
            nazev=request.form.get('nazev'),
            popis=request.form.get('popis'),
            vedouci=request.form.get('vedouci')
        )
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('projects.detail', projekt_id=result['project_id']))
        else:
            flash(f"Chyba: {result['error']}", 'danger')
    
    return render_template('projekty/novy.html')


@project_bp.route('/<int:projekt_id>')
def detail(projekt_id):
    """Detail projektu"""
    projekt = Projekt.query.get_or_404(projekt_id)
    
    budgets = ProjectExecutor.get_project_budgets(projekt_id)
    expenses = ProjectExecutor.get_project_expenses(projekt_id)
    milestones = ProjectExecutor.get_project_milestones(projekt_id)
    messages = ProjectExecutor.get_project_messages(projekt_id)
    knowledge = ProjectExecutor.get_project_knowledge(projekt_id)
    
    return render_template(
        'projekty/detail.html',
        projekt=projekt,
        budgets=budgets,
        expenses=expenses,
        milestones=milestones,
        messages=messages,
        knowledge=knowledge
    )


@project_bp.route('/<int:projekt_id>/upravit', methods=['GET', 'POST'])
def upravit(projekt_id):
    """Úprava projektu"""
    projekt = Projekt.query.get_or_404(projekt_id)
    
    if request.method == 'POST':
        result = ProjectExecutor.update_project(
            projekt_id,
            nazev=request.form.get('nazev'),
            popis=request.form.get('popis'),
            status=request.form.get('status'),
            vedouci=request.form.get('vedouci')
        )
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('projects.detail', projekt_id=projekt_id))
        else:
            flash(f"Chyba: {result['error']}", 'danger')
    
    return render_template('projekty/upravit.html', projekt=projekt)


# ============================================================================
# ROZPOČET
# ============================================================================

@project_bp.route('/<int:projekt_id>/rozpocet', methods=['GET', 'POST'])
def rozpocet(projekt_id):
    """Správa rozpočtu projektu"""
    projekt = Projekt.query.get_or_404(projekt_id)
    
    if request.method == 'POST':
        result = ProjectExecutor.add_budget_item(
            projekt_id,
            kategorie=request.form.get('kategorie'),
            popis=request.form.get('popis'),
            castka=float(request.form.get('castka')),
            poznamka=request.form.get('poznamka')
        )
        
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(f"Chyba: {result['error']}", 'danger')
        
        return redirect(url_for('projects.rozpocet', projekt_id=projekt_id))
    
    budgets = ProjectExecutor.get_project_budgets(projekt_id)
    
    return render_template(
        'projekty/rozpocet.html',
        projekt=projekt,
        budgets=budgets
    )


# ============================================================================
# VÝDAJE
# ============================================================================

@project_bp.route('/<int:projekt_id>/vydaje', methods=['GET', 'POST'])
def vydaje(projekt_id):
    """Správa výdajů projektu"""
    projekt = Projekt.query.get_or_404(projekt_id)
    
    if request.method == 'POST':
        result = ProjectExecutor.add_expense(
            projekt_id,
            kategorie=request.form.get('kategorie'),
            popis=request.form.get('popis'),
            castka=float(request.form.get('castka')),
            cis_faktury=request.form.get('cis_faktury'),
            dodavatel=request.form.get('dodavatel')
        )
        
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(f"Chyba: {result['error']}", 'danger')
        
        return redirect(url_for('projects.vydaje', projekt_id=projekt_id))
    
    expenses = ProjectExecutor.get_project_expenses(projekt_id)
    budgets = ProjectExecutor.get_project_budgets(projekt_id)
    
    return render_template(
        'projekty/vydaje.html',
        projekt=projekt,
        expenses=expenses,
        budgets=budgets
    )


# ============================================================================
# TERMÍNY
# ============================================================================

@project_bp.route('/<int:projekt_id>/terminy', methods=['GET', 'POST'])
def terminy(projekt_id):
    """Správa termínů/milestones"""
    projekt = Projekt.query.get_or_404(projekt_id)
    
    if request.method == 'POST':
        result = ProjectExecutor.add_milestone(
            projekt_id,
            nazev=request.form.get('nazev'),
            datum_planovane=request.form.get('datum_planovane'),
            popis=request.form.get('popis'),
            zodpovedny=request.form.get('zodpovedny')
        )
        
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(f"Chyba: {result['error']}", 'danger')
        
        return redirect(url_for('projects.terminy', projekt_id=projekt_id))
    
    milestones = ProjectExecutor.get_project_milestones(projekt_id)
    
    return render_template(
        'projekty/terminy.html',
        projekt=projekt,
        milestones=milestones
    )


# ============================================================================
# API ENDPOINTY PRO AI ASISTENTA
# ============================================================================

@project_bp.route('/api/<int:projekt_id>/info')
def api_info(projekt_id):
    """API - Info o projektu"""
    result = ProjectExecutor.get_project_detail(projekt_id)
    return jsonify(result)


@project_bp.route('/api/<int:projekt_id>/rozpocet')
def api_rozpocet(projekt_id):
    """API - Rozpočet projektu"""
    budgets = ProjectExecutor.get_project_budgets(projekt_id)
    return jsonify({"success": True, "budgets": budgets})


@project_bp.route('/api/<int:projekt_id>/vydaje')
def api_vydaje(projekt_id):
    """API - Výdaje projektu"""
    expenses = ProjectExecutor.get_project_expenses(projekt_id)
    return jsonify({"success": True, "expenses": expenses})


@project_bp.route('/api/<int:projekt_id>/terminy')
def api_terminy(projekt_id):
    """API - Termíny projektu"""
    milestones = ProjectExecutor.get_project_milestones(projekt_id)
    return jsonify({"success": True, "milestones": milestones})


@project_bp.route('/api/<int:projekt_id>/zpravy')
def api_zpravy(projekt_id):
    """API - Zprávy projektu"""
    messages = ProjectExecutor.get_project_messages(projekt_id, limit=100)
    return jsonify({"success": True, "messages": messages})


@project_bp.route('/api/<int:projekt_id>/znalosti')
def api_znalosti(projekt_id):
    """API - Znalosti projektu"""
    knowledge = ProjectExecutor.get_project_knowledge(projekt_id)
    return jsonify({"success": True, "knowledge": knowledge})
