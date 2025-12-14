"""
Project Routes - Routy pro správu projektů
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from core import db
from .models import Projekt, BudgetProjektu, VydajProjektu, Termin, Zprava, ProjectShare
from .executor import ProjectExecutor

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
        created_by_user_id = request.form.get('created_by_user_id')
        created_by_personnel_id = request.form.get('created_by_personnel_id')
        
        # Zpracuj created_by_user_id
        final_created_by_user_id = None
        if created_by_user_id:
            try:
                final_created_by_user_id = int(created_by_user_id)
            except (ValueError, TypeError):
                pass
        
        # Personální agendu necháme volitelnou (může být None)
        final_created_by_personnel_id = None
        if created_by_personnel_id:
            try:
                final_created_by_personnel_id = int(created_by_personnel_id)
            except (ValueError, TypeError):
                pass
        
        result = ProjectExecutor.create_project(
            nazev=request.form.get('nazev'),
            popis=request.form.get('popis'),
            created_by_user_id=final_created_by_user_id,
            created_by_personnel_id=final_created_by_personnel_id
        )
        
        if result['success']:
            projekt_id = result['project_id']
            # Volitelně nastavit rozpočet při vytvoření
            rozpocet = request.form.get('rozpocet')
            if rozpocet:
                try:
                    ProjectExecutor.set_project_budget(projekt_id, float(rozpocet))
                except:
                    pass  # Pokud se nepodaří, projekt se vytvoří bez rozpočtu
            
            flash(result['message'], 'success')
            return redirect(url_for('projects.detail', projekt_id=projekt_id))
        else:
            flash(f"Chyba: {result['error']}", 'danger')
    
    # Načti seznam uživatelů a personální agendy pro výběr
    from modules.users.models import User
    from modules.personnel.models import ZamestnanecAOON
    
    uzivatele = User.query.filter_by(aktivni=True).all()
    zamestnanci = ZamestnanecAOON.query.filter_by(aktivni=True).all()
    
    return render_template('projekty/novy.html', uzivatele=uzivatele, zamestnanci=zamestnanci)


@project_bp.route('/<int:projekt_id>/sdilet', methods=['GET', 'POST'])
def sdilet_projekt(projekt_id):
    """Sdílení projektu s jinými uživateli"""
    projekt = Projekt.query.get_or_404(projekt_id)
    
    if request.method == 'POST':
        shared_with_user_id = request.form.get('shared_with_user_id')
        permission = request.form.get('permission', 'read')
        poznamka = request.form.get('poznamka')
        
        if not shared_with_user_id:
            flash('Musíte vybrat uživatele', 'danger')
            return redirect(url_for('projects.sdilet_projekt', projekt_id=projekt_id))
        
        # Získej uživatele, který pozývá (vlastník projektu nebo první uživatel)
        from modules.users.models import User
        shared_by_user_id = projekt.created_by_user_id
        if not shared_by_user_id:
            # Pokud projekt nemá zakladatele, použij prvního aktivního uživatele
            first_user = User.query.filter_by(aktivni=True).first()
            if first_user:
                shared_by_user_id = first_user.id
            else:
                flash('Nelze pozvat uživatele - projekt nemá zakladatele', 'danger')
                return redirect(url_for('projects.sdilet_projekt', projekt_id=projekt_id))
        
        # Zkontroluj, zda uživatel existuje
        try:
            shared_with_user = User.query.get(int(shared_with_user_id))
            if not shared_with_user:
                flash('Vybraný uživatel neexistuje', 'danger')
                return redirect(url_for('projects.sdilet_projekt', projekt_id=projekt_id))
        except (ValueError, TypeError):
            flash('Neplatný uživatel', 'danger')
            return redirect(url_for('projects.sdilet_projekt', projekt_id=projekt_id))
        
        result = ProjectExecutor.share_project(
            projekt_id=projekt_id,
            shared_with_user_id=int(shared_with_user_id),
            shared_by_user_id=shared_by_user_id,
            permission=permission,
            poznamka=poznamka
        )
        
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(f"Chyba: {result['error']}", 'danger')
        
        return redirect(url_for('projects.sdilet_projekt', projekt_id=projekt_id))
    
    # Načti seznam uživatelů a aktuální sdílení
    from modules.users.models import User
    uzivatele = User.query.filter_by(aktivni=True).all()
    shares = ProjectExecutor.get_project_shares(projekt_id)
    
    return render_template(
        'projekty/sdilet.html',
        projekt=projekt,
        uzivatele=uzivatele,
        shares=shares
    )


@project_bp.route('/<int:projekt_id>/vzkaz', methods=['POST'])
def pridat_vzkaz(projekt_id):
    """Přidat vzkaz na nástěnku projektu"""
    from flask import session
    projekt = Projekt.query.get_or_404(projekt_id)
    
    obsah = request.form.get('obsah', '').strip()
    
    if not obsah:
        flash('Vzkaz nemůže být prázdný', 'danger')
        return redirect(url_for('projects.detail', projekt_id=projekt_id))
    
    # Získej aktuálně přihlášeného uživatele z session
    current_user_id = session.get('current_user_id')
    autor = 'Neznámý uživatel'
    created_by_initials = None
    
    if current_user_id:
        try:
            from modules.users.models import User
            user = User.query.get(current_user_id)
            if user:
                autor = user.jmeno_prijmeni
                # Vytvoř iniciály z jména (první písmena jména a příjmení)
                try:
                    parts = autor.split()
                    if len(parts) >= 2:
                        created_by_initials = (parts[0][0] + parts[1][0]).upper()
                    elif len(parts) == 1:
                        created_by_initials = parts[0][0].upper()
                except:
                    pass
        except:
            pass
    
    # Získej příjemce zprávy (null = všem, jinak ID uživatele)
    to_user_id = request.form.get('to_user_id', '').strip()
    final_to_user_id = None
    if to_user_id:
        try:
            final_to_user_id = int(to_user_id)
        except (ValueError, TypeError):
            pass
    
    # Všechny konverzace se ukládají do databáze pro pozdější dohledání
    result = ProjectExecutor.add_message(
        projekt_id=projekt_id,
        obsah=obsah,
        autor=autor,
        typ='poznamka',
        created_by_initials=created_by_initials,
        to_user_id=final_to_user_id
    )
    
    if result['success']:
        flash('Vzkaz byl přidán', 'success')
    else:
        flash(f"Chyba: {result['error']}", 'danger')
    
    return redirect(url_for('projects.detail', projekt_id=projekt_id))


@project_bp.route('/<int:projekt_id>/sdilet/<int:share_id>/zrusit', methods=['POST'])
def zrusit_sdileni(projekt_id, share_id):
    """Zruší sdílení projektu"""
    share = ProjectShare.query.get_or_404(share_id)
    
    if share.projekt_id != projekt_id:
        flash("Neplatné sdílení", 'danger')
        return redirect(url_for('projects.detail', projekt_id=projekt_id))
    
    result = ProjectExecutor.unshare_project(projekt_id, share.shared_with_user_id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f"Chyba: {result['error']}", 'danger')
    
    return redirect(url_for('projects.sdilet_projekt', projekt_id=projekt_id))


@project_bp.route('/<int:projekt_id>')
def detail(projekt_id):
    """Detail projektu"""
    projekt = Projekt.query.get_or_404(projekt_id)
    
    # NOVÁ LOGIKA - nepoužíváme budgets, jen rozpočet projektu
    expenses = ProjectExecutor.get_project_expenses(projekt_id)
    milestones = ProjectExecutor.get_project_milestones(projekt_id)
    
    # Získej aktuálně přihlášeného uživatele pro filtrování zpráv
    from flask import session
    current_user_id = session.get('current_user_id')
    messages = ProjectExecutor.get_project_messages(projekt_id, current_user_id=current_user_id)
    budget_info = ProjectExecutor.get_project_budget(projekt_id)
    
    # Načti seznam uživatelů pro výběr příjemce vzkazu
    from modules.users.models import User
    uzivatele_projektu = []
    try:
        # Získej uživatele, kteří mají přístup k projektu (zakladatel + sdílení)
        all_users = User.query.filter_by(aktivni=True).all()
        for user in all_users:
            # Zkontroluj, zda má uživatel přístup k projektu
            if projekt.created_by_user_id == user.id:
                uzivatele_projektu.append(user)
            else:
                access = ProjectExecutor.can_user_access_project(user.id, projekt_id)
                if access.get('can_access', False):
                    uzivatele_projektu.append(user)
    except:
        pass
    
    # Načti historii AI konverzace pro zobrazení v chatu
    from models import Zprava
    chat_history = Zprava.query.filter_by(
        projekt_id=projekt_id
    ).order_by(Zprava.datum.asc()).limit(50).all()  # Posledních 50 zpráv
    
    # Načti sdílení projektu
    shares = ProjectExecutor.get_project_shares(projekt_id)
    
    return render_template(
        'projekty/detail.html',
        projekt=projekt,
        expenses=expenses,
        milestones=milestones,
        messages=messages,
        budget_info=budget_info,
        chat_history=chat_history,
        shares=shares,
        uzivatele_projektu=uzivatele_projektu
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
            status=request.form.get('status')
        )
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('projects.detail', projekt_id=projekt_id))
        else:
            flash(f"Chyba: {result['error']}", 'danger')
    
    return render_template('projekty/upravit.html', projekt=projekt)


@project_bp.route('/<int:projekt_id>/smazat', methods=['POST'])
def smazat(projekt_id):
    """Smazání projektu"""
    projekt = Projekt.query.get_or_404(projekt_id)
    
    result = ProjectExecutor.delete_project(projekt_id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f"Chyba: {result['error']}", 'danger')
    
    return redirect(url_for('projects.seznam'))


# ============================================================================
# ROZPOČET - NOVÁ LOGIKA
# ============================================================================

@project_bp.route('/<int:projekt_id>/rozpocet', methods=['GET', 'POST'])
def rozpocet(projekt_id):
    """Správa rozpočtu projektu - nastavení celkového rozpočtu"""
    projekt = Projekt.query.get_or_404(projekt_id)
    
    if request.method == 'POST':
        try:
            rozpocet = float(request.form.get('rozpocet', 0))
            result = ProjectExecutor.set_project_budget(projekt_id, rozpocet)
            
            if result['success']:
                flash(result['message'], 'success')
            else:
                flash(f"Chyba: {result['error']}", 'danger')
        except ValueError:
            flash('Neplatná hodnota rozpočtu', 'danger')
        
        return redirect(url_for('projects.rozpocet', projekt_id=projekt_id))
    
    budget_info = ProjectExecutor.get_project_budget(projekt_id)
    
    return render_template(
        'projekty/rozpocet.html',
        projekt=projekt,
        budget_info=budget_info
    )


# ============================================================================
# VÝDAJE
# ============================================================================

@project_bp.route('/<int:projekt_id>/vydaje', methods=['GET', 'POST'])
def vydaje(projekt_id):
    """Správa výdajů projektu"""
    projekt = Projekt.query.get_or_404(projekt_id)
    
    if request.method == 'POST':
        try:
            # Získej iniciály z formuláře
            created_by_initials = request.form.get('created_by_initials', '').strip()[:10] if request.form.get('created_by_initials') else None
            
            result = ProjectExecutor.add_expense(
                projekt_id,
                popis=request.form.get('popis', '').strip(),
                castka=float(request.form.get('castka', 0)),
                cis_faktury=request.form.get('cis_faktury'),
                dodavatel=request.form.get('dodavatel'),
                poznamka=request.form.get('poznamka'),
                datum=request.form.get('datum'),  # Volitelné datum
                created_by_initials=created_by_initials
            )
            
            if result['success']:
                flash(result['message'], 'success')
                if result.get('warning'):
                    flash(result['warning'], 'warning')
            else:
                flash(f"Chyba: {result['error']}", 'danger')
        except ValueError:
            flash('Neplatná hodnota částky', 'danger')
        
        return redirect(url_for('projects.vydaje', projekt_id=projekt_id))
    
    expenses = ProjectExecutor.get_project_expenses(projekt_id)
    budget_info = ProjectExecutor.get_project_budget(projekt_id)
    
    return render_template(
        'projekty/vydaje.html',
        projekt=projekt,
        expenses=expenses,
        budget_info=budget_info
    )


@project_bp.route('/<int:projekt_id>/vydaj/<int:vydaj_id>/upravit', methods=['GET', 'POST'])
def upravit_vydaj(projekt_id, vydaj_id):
    """Upravit výdaj projektu"""
    projekt = Projekt.query.get_or_404(projekt_id)
    vydaj_detail = ProjectExecutor.get_expense_detail(vydaj_id)
    
    if not vydaj_detail.get('success') or vydaj_detail.get('projekt_id') != projekt_id:
        flash('Výdaj nenalezen', 'danger')
        return redirect(url_for('projects.vydaje', projekt_id=projekt_id))
    
    if request.method == 'POST':
        try:
            result = ProjectExecutor.update_expense(
                vydaj_id,
                popis=request.form.get('popis', '').strip(),
                castka=float(request.form.get('castka', 0)),
                cis_faktury=request.form.get('cis_faktury'),
                dodavatel=request.form.get('dodavatel'),
                poznamka=request.form.get('poznamka'),
                datum=request.form.get('datum')
            )
            
            if result['success']:
                flash(result['message'], 'success')
                return redirect(url_for('projects.vydaje', projekt_id=projekt_id))
            else:
                flash(f"Chyba: {result['error']}", 'danger')
        except ValueError:
            flash('Neplatná hodnota částky', 'danger')
    
    return render_template(
        'projekty/upravit_vydaj.html',
        projekt=projekt,
        vydaj=vydaj_detail
    )


@project_bp.route('/<int:projekt_id>/vydaj/<int:vydaj_id>/smazat', methods=['POST'])
def smazat_vydaj(projekt_id, vydaj_id):
    """Smazat výdaj projektu"""
    result = ProjectExecutor.delete_expense(vydaj_id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f"Chyba: {result['error']}", 'danger')
    
    return redirect(url_for('projects.vydaje', projekt_id=projekt_id))


# ============================================================================
# TERMÍNY
# ============================================================================

@project_bp.route('/<int:projekt_id>/terminy', methods=['GET', 'POST'])
def terminy(projekt_id):
    """Správa termínů/milestones"""
    projekt = Projekt.query.get_or_404(projekt_id)
    
    if request.method == 'POST':
        # Získej iniciály z formuláře
        created_by_initials = request.form.get('created_by_initials', '').strip()[:10] if request.form.get('created_by_initials') else None
        
        result = ProjectExecutor.add_milestone(
            projekt_id,
            nazev=request.form.get('nazev'),
            datum_planovane=request.form.get('datum_planovane'),
            popis=request.form.get('popis'),
            zodpovedny=request.form.get('zodpovedny'),
            created_by_initials=created_by_initials
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


