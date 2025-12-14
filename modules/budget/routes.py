"""
Routes pro modul rozpočtu - kompletní implementace
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from core import db
from .models import Budget, BudgetCategory, BudgetSubCategory, BudgetItem, Expense, Revenue, MonthlyBudgetItem
from .executor import BudgetExecutor

budget_bp = Blueprint('budget', __name__, url_prefix='/rozpocet')


@budget_bp.route('/')
def index():
    """Hlavní stránka modulu rozpočtu - dashboard"""
    import json
    from datetime import datetime as dt
    
    # #region agent log
    with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"budget/routes.py:15","message":"budget index route called","data":{},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
    # #endregion
    
    try:
        hlavni_rozpocet = BudgetExecutor.get_or_create_main_budget()
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"budget/routes.py:20","message":"get_or_create_main_budget completed","data":{"budget_id":hlavni_rozpocet.id if hlavni_rozpocet else None},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        
        overview = BudgetExecutor.get_budget_overview(hlavni_rozpocet.id)
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"budget/routes.py:23","message":"get_budget_overview completed","data":{"overview_keys":list(overview.keys()) if overview else None},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"budget/routes.py:26","message":"Before render_template","data":{},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        
        return render_template(
            'budget/index.html',
            hlavni_rozpocet=hlavni_rozpocet,
            overview=overview
        )
    except Exception as e:
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"budget/routes.py:35","message":"Exception in budget index","data":{"error":str(e),"type":type(e).__name__},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        raise


@budget_bp.route('/kategorie/novy', methods=['GET', 'POST'])
def nova_kategorie():
    """Vytvořit novou kategorii"""
    hlavni_rozpocet = BudgetExecutor.get_or_create_main_budget()
    
    if request.method == 'POST':
        result = BudgetExecutor.create_category(
            budget_id=hlavni_rozpocet.id,
            typ=request.form.get('typ'),
            nazev=request.form.get('nazev'),
            kod=request.form.get('kod'),
            barva=request.form.get('barva', '#007bff'),
            popis=request.form.get('popis')
        )
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('budget.index'))
        else:
            flash(f"Chyba: {result['error']}", 'danger')
    
    return render_template('budget/nova_kategorie.html', budget=hlavni_rozpocet)


@budget_bp.route('/kategorie/<int:category_id>/podkategorie/novy', methods=['GET', 'POST'])
def nova_podkategorie(category_id):
    """Vytvořit novou podkategorii"""
    category = BudgetCategory.query.get_or_404(category_id)
    
    if request.method == 'POST':
        result = BudgetExecutor.create_subcategory(
            category_id=category_id,
            nazev=request.form.get('nazev'),
            kod=request.form.get('kod'),
            popis=request.form.get('popis')
        )
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('budget.index'))
        else:
            flash(f"Chyba: {result['error']}", 'danger')
    
    return render_template('budget/nova_podkategorie.html', category=category)


@budget_bp.route('/polozka/novy', methods=['GET', 'POST'])
def nova_polozka():
    """Přidat novou rozpočtovou položku"""
    hlavni_rozpocet = BudgetExecutor.get_or_create_main_budget()
    kategorie = BudgetExecutor.get_categories_by_type(hlavni_rozpocet.id)
    
    if request.method == 'POST':
        subcategory_id = int(request.form.get('subcategory_id')) if request.form.get('subcategory_id') else None
        
        result = BudgetExecutor.add_budget_item(
            budget_id=hlavni_rozpocet.id,
            category_id=int(request.form.get('category_id')),
            subcategory_id=subcategory_id,
            nazev=request.form.get('nazev'),
            castka=float(request.form.get('castka', 0)),
            popis=request.form.get('popis')
        )
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('budget.index'))
        else:
            flash(f"Chyba: {result['error']}", 'danger')
    
    return render_template('budget/nova_polozka.html', budget=hlavni_rozpocet, kategorie=kategorie)


@budget_bp.route('/vydaj/novy', methods=['GET', 'POST'])
def novy_vydaj():
    """Přidat nový výdaj"""
    hlavni_rozpocet = BudgetExecutor.get_or_create_main_budget()
    kategorie = BudgetExecutor.get_categories_by_type(hlavni_rozpocet.id)
    
    # Položky rozpočtu pro výběr (pouze aktivní)
    polozky_rozpoctu = BudgetItem.query.filter_by(
        budget_id=hlavni_rozpocet.id,
        aktivni=True
    ).order_by(BudgetItem.typ, BudgetItem.ucet, BudgetItem.poducet).all()
    
    
    # Personální záznamy pro mzdy
    from ..personnel.models import ZamestnanecAOON
    personnel = ZamestnanecAOON.query.filter_by(aktivni=True).all()
    
    if request.method == 'POST':
        budget_item_id = request.form.get('budget_item_id')
        if not budget_item_id:
            flash('Položka rozpočtu je povinná', 'danger')
        else:
            subcategory_id = int(request.form.get('subcategory_id')) if request.form.get('subcategory_id') else None
            personnel_id = int(request.form.get('personnel_id')) if request.form.get('personnel_id') else None
            
            result = BudgetExecutor.add_expense(
                budget_id=hlavni_rozpocet.id,
                budget_item_id=int(budget_item_id),
                category_id=int(request.form.get('category_id')),
                subcategory_id=subcategory_id,
                popis=request.form.get('popis'),
                castka=float(request.form.get('castka', 0)),
                personnel_id=personnel_id,
                cis_faktury=request.form.get('cis_faktury'),
                dodavatel=request.form.get('dodavatel'),
                poznamka=request.form.get('poznamka'),
                datum=request.form.get('datum') or datetime.utcnow()
            )
            
            if result['success']:
                flash(result['message'], 'success')
                return redirect(url_for('budget.index'))
            else:
                flash(f"Chyba: {result['error']}", 'danger')
    
    return render_template(
        'budget/novy_vydaj.html',
        budget=hlavni_rozpocet,
        kategorie=kategorie,
        polozky_rozpoctu=polozky_rozpoctu,
        personnel=personnel
    )


@budget_bp.route('/seznam')
def seznam():
    """Seznam rozpočtů - kompatibilita"""
    return redirect(url_for('budget.index'))


@budget_bp.route('/vynos/novy', methods=['GET', 'POST'])
def novy_vynos():
    """Přidat nový výnos (jednorázový nebo pravidelný)"""
    hlavni_rozpocet = BudgetExecutor.get_or_create_main_budget()
    kategorie = BudgetExecutor.get_categories_by_type(hlavni_rozpocet.id, typ='vynos')
    
    if request.method == 'POST':
        typ = request.form.get('typ', 'jednorazovy')
        subcategory_id = int(request.form.get('subcategory_id')) if request.form.get('subcategory_id') else None
        
        if typ == 'jednorazovy':
            datum = request.form.get('datum') or datetime.utcnow()
            result = BudgetExecutor.add_revenue(
                budget_id=hlavni_rozpocet.id,
                category_id=int(request.form.get('category_id')),
                subcategory_id=subcategory_id,
                nazev=request.form.get('nazev'),
                castka=float(request.form.get('castka', 0)),
                typ='jednorazovy',
                datum=datum,
                naplanovano=request.form.get('naplanovano') == 'on',
                skutecne_prijato=request.form.get('skutecne_prijato') == 'on',
                cis_faktury=request.form.get('cis_faktury'),
                odberatel=request.form.get('odberatel'),
                popis=request.form.get('popis'),
                poznamka=request.form.get('poznamka')
            )
        else:  # pravidelny
            datum_zacatku = request.form.get('datum_zacatku')
            datum_konce = request.form.get('datum_konce') or None
            result = BudgetExecutor.add_revenue(
                budget_id=hlavni_rozpocet.id,
                category_id=int(request.form.get('category_id')),
                subcategory_id=subcategory_id,
                nazev=request.form.get('nazev'),
                castka=float(request.form.get('castka', 0)),
                typ='pravidelny',
                rok=int(request.form.get('rok', datetime.utcnow().year)),
                datum_zacatku=datum_zacatku,
                datum_konce=datum_konce,
                frekvence=request.form.get('frekvence', 'mesicne'),
                mesice=request.form.get('mesice', 'vse'),
                naplanovano=request.form.get('naplanovano') == 'on',
                skutecne_prijato=request.form.get('skutecne_prijato') == 'on',
                cis_faktury=request.form.get('cis_faktury'),
                odberatel=request.form.get('odberatel'),
                popis=request.form.get('popis'),
                poznamka=request.form.get('poznamka')
            )
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('budget.index'))
        else:
            flash(f"Chyba: {result['error']}", 'danger')
    
    return render_template(
        'budget/novy_vynos.html',
        budget=hlavni_rozpocet,
        kategorie=kategorie
    )


@budget_bp.route('/api/kategorie/<int:category_id>/podkategorie')
def api_podkategorie(category_id):
    """API endpoint pro získání podkategorií"""
    podkategorie = BudgetSubCategory.query.filter_by(
        category_id=category_id,
        aktivni=True
    ).order_by(BudgetSubCategory.poradi).all()
    
    return jsonify([
        {'id': p.id, 'nazev': p.nazev}
        for p in podkategorie
    ])


# ============================================================================
# SPRÁVA VÍCE ROZPOČTŮ (ROKY)
# ============================================================================

@budget_bp.route('/dalsi-roky')
def dalsi_roky():
    """Správa rozpočtů pro další roky"""
    rozpocty = BudgetExecutor.get_all_budgets_by_year()
    hlavni_rozpocet = BudgetExecutor.get_or_create_main_budget()
    
    return render_template(
        'budget/dalsi_roky.html',
        rozpocty=rozpocty,
        hlavni_rozpocet=hlavni_rozpocet
    )


@budget_bp.route('/dalsi-roky/novy', methods=['GET', 'POST'])
def novy_rozpocet_rok():
    """Vytvořit nový rozpočet pro rok"""
    if request.method == 'POST':
        try:
            rok = int(request.form.get('rok', 0))
            nazev = request.form.get('nazev', '').strip() or None
            
            if rok < 2000 or rok > 2100:
                flash('Neplatný rok (musí být mezi 2000 a 2100)', 'danger')
            else:
                result = BudgetExecutor.create_budget_for_year(rok, nazev)
                
                if result['success']:
                    flash(result['message'], 'success')
                    return redirect(url_for('budget.dalsi_roky'))
                else:
                    flash(f"Chyba: {result['error']}", 'danger')
        except ValueError:
            flash('Neplatný rok', 'danger')
        except Exception as e:
            flash(f'Chyba: {str(e)}', 'danger')
    
    return render_template('budget/novy_rozpocet_rok.html')


@budget_bp.route('/dalsi-roky/<int:budget_id>/nastavit-hlavni', methods=['POST'])
def nastavit_hlavni_rozpocet(budget_id):
    """Nastavit rozpočet jako hlavní"""
    result = BudgetExecutor.set_main_budget(budget_id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f"Chyba: {result['error']}", 'danger')
    
    return redirect(url_for('budget.dalsi_roky'))


@budget_bp.route('/polozky')
def seznam_polozek():
    """Seznam všech položek rozpočtu"""
    import json
    from datetime import datetime as dt
    
    # #region agent log
    with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"budget/routes.py:262","message":"seznam_polozek route called","data":{},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
    # #endregion
    
    try:
        hlavni_rozpocet = BudgetExecutor.get_or_create_main_budget()
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"budget/routes.py:268","message":"get_or_create_main_budget completed","data":{"budget_id":hlavni_rozpocet.id if hlavni_rozpocet else None},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        
        # Filtry
        typ_filter = request.args.get('typ', '')  # 'naklad', 'vynos', nebo prázdné pro všechny
        rok = request.args.get('rok', hlavni_rozpocet.rok, type=int)
        
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"budget/routes.py:275","message":"Before database query","data":{"budget_id":hlavni_rozpocet.id,"typ_filter":typ_filter},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        
        # Získat všechny položky rozpočtu
        query = BudgetItem.query.filter_by(budget_id=hlavni_rozpocet.id, aktivni=True)
        
        if typ_filter:
            query = query.filter_by(typ=typ_filter)
        
        polozky = query.order_by(BudgetItem.typ, BudgetItem.ucet, BudgetItem.poducet).all()
        
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"budget/routes.py:285","message":"Database query completed","data":{"polozky_count":len(polozky)},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"budget/routes.py:288","message":"Before calculating sums","data":{},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        
        # Součty
        naklady_celkem = sum(p.castka_float for p in polozky if p.typ == 'naklad')
        vynosy_celkem = sum(p.castka_float for p in polozky if p.typ == 'vynos')
        
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"budget/routes.py:295","message":"Before calculating aktualni_plneni","data":{},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        
        naklady_plneni = sum(p.aktualni_plneni for p in polozky if p.typ == 'naklad')
        vynosy_plneni = sum(p.aktualni_plneni for p in polozky if p.typ == 'vynos')
        
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"budget/routes.py:300","message":"Sums calculated","data":{"naklady_celkem":naklady_celkem,"vynosy_celkem":vynosy_celkem,"naklady_plneni":naklady_plneni,"vynosy_plneni":vynosy_plneni},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"budget/routes.py:303","message":"Before render_template","data":{},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        
        return render_template(
            'budget/seznam_polozek.html',
            polozky=polozky,
            hlavni_rozpocet=hlavni_rozpocet,
            typ_filter=typ_filter,
            rok=rok,
            naklady_celkem=naklady_celkem,
            vynosy_celkem=vynosy_celkem,
            naklady_plneni=naklady_plneni,
            vynosy_plneni=vynosy_plneni
        )
    except Exception as e:
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"budget/routes.py:320","message":"Exception in seznam_polozek","data":{"error":str(e),"type":type(e).__name__},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        raise


@budget_bp.route('/polozka/pridat', methods=['GET', 'POST'])
def pridat_polozku():
    """Přidat novou položku rozpočtu"""
    import json
    from datetime import datetime as dt
    
    # #region agent log
    with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"budget/routes.py:298","message":"pridat_polozku route called","data":{"method":request.method},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
    # #endregion
    
    hlavni_rozpocet = BudgetExecutor.get_or_create_main_budget()
    
    if request.method == 'POST':
        try:
            # #region agent log
            with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"budget/routes.py:305","message":"Before creating BudgetItem","data":{"form_data":dict(request.form)},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
            # #endregion
            
            polozka = BudgetItem(
                budget_id=hlavni_rozpocet.id,
                ucet=request.form.get('ucet', '').strip(),
                poducet=request.form.get('poducet', '').strip() or None,
                popis=request.form.get('popis', '').strip(),
                typ=request.form.get('typ', 'naklad'),
                castka=float(request.form.get('castka', 0) or 0),
                aktivni=True
            )
            
            # #region agent log
            with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"budget/routes.py:316","message":"BudgetItem created","data":{"ucet":polozka.ucet,"popis":polozka.popis,"typ":polozka.typ,"castka":float(polozka.castka)},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
            # #endregion
            
            if not polozka.ucet or not polozka.popis:
                # #region agent log
                with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"budget/routes.py:319","message":"Validation failed","data":{"ucet":polozka.ucet,"popis":polozka.popis},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
                # #endregion
                flash('Účet a popis jsou povinné', 'danger')
            else:
                # #region agent log
                with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"budget/routes.py:322","message":"Before db.session.add","data":{},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
                # #endregion
                db.session.add(polozka)
                # #region agent log
                with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"budget/routes.py:324","message":"Before db.session.commit","data":{},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
                # #endregion
                db.session.commit()
                # #region agent log
                with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"budget/routes.py:326","message":"db.session.commit completed","data":{"polozka_id":polozka.id},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
                # #endregion
                flash(f'Položka rozpočtu "{polozka.popis}" byla přidána', 'success')
                return redirect(url_for('budget.seznam_polozek'))
        except Exception as e:
            # #region agent log
            with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"budget/routes.py:330","message":"Exception in pridat_polozku","data":{"error":str(e),"type":type(e).__name__},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
            # #endregion
            db.session.rollback()
            flash(f'Chyba při přidávání položky: {str(e)}', 'danger')
    
    return render_template('budget/pridat_polozku.html', budget=hlavni_rozpocet)


@budget_bp.route('/polozka/<int:polozka_id>/upravit', methods=['GET', 'POST'])
def upravit_polozku(polozka_id):
    """Upravit položku rozpočtu"""
    polozka = BudgetItem.query.get_or_404(polozka_id)
    
    if request.method == 'POST':
        try:
            polozka.ucet = request.form.get('ucet', '').strip()
            polozka.poducet = request.form.get('poducet', '').strip() or None
            polozka.popis = request.form.get('popis', '').strip()
            polozka.typ = request.form.get('typ', 'naklad')
            polozka.castka = float(request.form.get('castka', 0) or 0)
            
            if not polozka.ucet or not polozka.popis:
                flash('Účet a popis jsou povinné', 'danger')
            else:
                db.session.commit()
                flash(f'Položka rozpočtu "{polozka.popis}" byla upravena', 'success')
                return redirect(url_for('budget.seznam_polozek'))
        except Exception as e:
            db.session.rollback()
            flash(f'Chyba při úpravě položky: {str(e)}', 'danger')
    
    return render_template('budget/upravit_polozku.html', polozka=polozka)


@budget_bp.route('/polozka/<int:polozka_id>/smazat', methods=['POST'])
def smazat_polozku(polozka_id):
    """Smazat položku rozpočtu a všechny související výdaje"""
    polozka = BudgetItem.query.get_or_404(polozka_id)
    
    try:
        popis = polozka.popis
        
        # Počítadla pro upozornění
        pocet_vydaju = len(polozka.vydaje) if polozka.vydaje else 0
        pocet_vynosu = len(polozka.vynosy) if polozka.vynosy else 0
        pocet_mesicnich = len(polozka.mesicni_stavy) if hasattr(polozka, 'mesicni_stavy') and polozka.mesicni_stavy else 0
        
        # Smaž všechny související výdaje
        if polozka.vydaje:
            for vydaj in polozka.vydaje:
                db.session.delete(vydaj)
        
        # Smaž všechny související výnosy
        if polozka.vynosy:
            for vynos in polozka.vynosy:
                db.session.delete(vynos)
        
        # Smaž všechny měsíční stavy
        if hasattr(polozka, 'mesicni_stavy') and polozka.mesicni_stavy:
            for stav in polozka.mesicni_stavy:
                db.session.delete(stav)
        
        # Smaž položku
        db.session.delete(polozka)
        db.session.commit()
        
        message = f'Položka rozpočtu "{popis}" byla smazána'
        if pocet_vydaju > 0 or pocet_vynosu > 0 or pocet_mesicnich > 0:
            message += f' (včetně {pocet_vydaju} výdajů, {pocet_vynosu} výnosů, {pocet_mesicnich} měsíčních aktualizací)'
        flash(message, 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Chyba při mazání položky: {str(e)}', 'danger')
    
    return redirect(url_for('budget.seznam_polozek'))


@budget_bp.route('/mesicni-stav', methods=['GET', 'POST'])
def mesicni_stav():
    """Měsíční stav rozpočtu - tabulka všech položek pro daný měsíc"""
    from decimal import Decimal
    
    hlavni_rozpocet = BudgetExecutor.get_or_create_main_budget()
    
    # GET parametry nebo default - vždy aktuální měsíc
    dnes = datetime.utcnow()
    mesic = request.args.get('mesic', type=int) or dnes.month
    rok = request.args.get('rok', type=int) or dnes.year
    
    if request.method == 'POST':
        try:
            # Zpracuj data z formuláře - může přijít více položek najednou
            mesic = int(request.form.get('mesic'))
            rok = int(request.form.get('rok'))
            
            # Zpracuj všechny položky - aktuální stav
            for key, value in request.form.items():
                if key.startswith('aktualni_stav_'):
                    polozka_id = int(key.replace('aktualni_stav_', ''))
                    aktualni_stav_str = value.strip() if value else None
                    aktualni_stav = Decimal(str(aktualni_stav_str)) if aktualni_stav_str else None
                    
                    # Zkontroluj, zda už existuje záznam
                    existujici = MonthlyBudgetItem.query.filter_by(
                        budget_item_id=polozka_id,
                        mesic=mesic,
                        rok=rok
                    ).first()
                    
                    if existujici:
                        existujici.aktualni_stav = aktualni_stav
                        existujici.datum_aktualizace = datetime.utcnow()
                    else:
                        nova = MonthlyBudgetItem(
                            budget_item_id=polozka_id,
                            mesic=mesic,
                            rok=rok,
                            aktualni_stav=aktualni_stav
                        )
                        db.session.add(nova)
            
            db.session.commit()
            flash(f'Měsíční stav pro {rok}/{mesic:02d} byl uložen', 'success')
            return redirect(url_for('budget.mesicni_stav', mesic=mesic, rok=rok))
        except Exception as e:
            db.session.rollback()
            flash(f'Chyba při ukládání: {str(e)}', 'danger')
    
    # GET - zobraz tabulku
    polozky = BudgetItem.query.filter_by(
        budget_id=hlavni_rozpocet.id,
        aktivni=True
    ).order_by(BudgetItem.typ.desc(), BudgetItem.ucet).all()
    
    # Načti měsíční stavy pro všechny položky
    mesicni_stavy = {}
    for polozka in polozky:
        stav = MonthlyBudgetItem.query.filter_by(
            budget_item_id=polozka.id,
            mesic=mesic,
            rok=rok
        ).first()
        mesicni_stavy[polozka.id] = stav
    
    # Statistiky pro měsíc
    statistiky = BudgetExecutor.get_mesicni_statistiky(hlavni_rozpocet.id, mesic, rok)
    
    nazvy_mesicu = [
        'Leden', 'Únor', 'Březen', 'Duben', 'Květen', 'Červen',
        'Červenec', 'Srpen', 'Září', 'Říjen', 'Listopad', 'Prosinec'
    ]
    
    return render_template(
        'budget/mesicni_stav.html',
        hlavni_rozpocet=hlavni_rozpocet,
        polozky=polozky,
        mesicni_stavy=mesicni_stavy,
        mesic=mesic,
        rok=rok,
        nazvy_mesicu=nazvy_mesicu,
        statistiky=statistiky
    )


@budget_bp.route('/mesicni-prehledy', methods=['GET'])
def mesicni_prehledy():
    """Měsíční přehledy rozpočtu s grafy"""
    hlavni_rozpocet = BudgetExecutor.get_or_create_main_budget()
    
    # GET parametry nebo default
    rok = request.args.get('rok', type=int) or datetime.utcnow().year
    
    # Získej data pro všechny měsíce v roce
    mesicni_data = []
    nazvy_mesicu = [
        'Leden', 'Únor', 'Březen', 'Duben', 'Květen', 'Červen',
        'Červenec', 'Srpen', 'Září', 'Říjen', 'Listopad', 'Prosinec'
    ]
    
    for mesic in range(1, 13):
        statistiky = BudgetExecutor.get_mesicni_statistiky(hlavni_rozpocet.id, mesic, rok)
        mesicni_data.append({
            'mesic': mesic,
            'nazev': nazvy_mesicu[mesic - 1],
            'statistiky': statistiky
        })
    
    # Celkové statistiky za rok
    celkove_statistiky = BudgetExecutor.get_rocni_statistiky(hlavni_rozpocet.id, rok)
    
    return render_template(
        'budget/mesicni_prehledy.html',
        hlavni_rozpocet=hlavni_rozpocet,
        mesicni_data=mesicni_data,
        rok=rok,
        nazvy_mesicu=nazvy_mesicu,
        celkove_statistiky=celkove_statistiky
    )


@budget_bp.route('/polozka/<int:polozka_id>/mesicni-aktualizace', methods=['GET', 'POST'])
def mesicni_aktualizace(polozka_id):
    """Měsíční aktualizace stavu položky rozpočtu"""
    from .models import MonthlyBudgetItem
    
    polozka = BudgetItem.query.get_or_404(polozka_id)
    hlavni_rozpocet = BudgetExecutor.get_or_create_main_budget()
    
    if request.method == 'POST':
        try:
            mesic = int(request.form.get('mesic'))
            rok = int(request.form.get('rok'))
            souhrnne_vydaje = float(request.form.get('souhrnne_vydaje', 0) or 0)
            poznamka = request.form.get('poznamka', '').strip()
            
            # Zkontroluj, zda už existuje záznam pro tento měsíc
            existujici = MonthlyBudgetItem.query.filter_by(
                budget_item_id=polozka_id,
                mesic=mesic,
                rok=rok
            ).first()
            
            if existujici:
                existujici.souhrnne_vydaje = Decimal(str(souhrnne_vydaje))
                existujici.poznamka = poznamka
                existujici.datum_aktualizace = datetime.utcnow()
                flash(f'Měsíční aktualizace pro {rok}/{mesic:02d} byla upravena', 'success')
            else:
                nova = MonthlyBudgetItem(
                    budget_item_id=polozka_id,
                    mesic=mesic,
                    rok=rok,
                    souhrnne_vydaje=Decimal(str(souhrnne_vydaje)),
                    poznamka=poznamka
                )
                db.session.add(nova)
                flash(f'Měsíční aktualizace pro {rok}/{mesic:02d} byla přidána', 'success')
            
            db.session.commit()
            return redirect(url_for('budget.seznam_polozek'))
        except Exception as e:
            db.session.rollback()
            flash(f'Chyba při aktualizaci: {str(e)}', 'danger')
    
    # GET - zobraz formulář
    aktualni_mesic = datetime.utcnow().month
    aktualni_rok = datetime.utcnow().year
    
    # Načti existující měsíční stavy
    mesicni_stavy = MonthlyBudgetItem.query.filter_by(
        budget_item_id=polozka_id
    ).order_by(MonthlyBudgetItem.rok.desc(), MonthlyBudgetItem.mesic.desc()).all()
    
    return render_template(
        'budget/mesicni_aktualizace.html',
        polozka=polozka,
        hlavni_rozpocet=hlavni_rozpocet,
        aktualni_mesic=aktualni_mesic,
        aktualni_rok=aktualni_rok,
        mesicni_stavy=mesicni_stavy
    )




