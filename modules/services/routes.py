"""
Routes pro modul Služby
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime, date, timedelta
from calendar import monthrange
from core import db
from .models import SluzbaTemplate, Sluzba, SluzbaVynimka, SluzbaVymena
from .executor import ServicesExecutor

services_bp = Blueprint('services', __name__, url_prefix='/sluzby')


@services_bp.route('/')
def index():
    """Hlavní stránka - kalendář služeb od dneška rok dopředu"""
    dnes = date.today()
    start_date = dnes
    end_date = dnes + timedelta(days=365)  # Rok dopředu
    
    # Získej služby od dneška rok dopředu
    mesice = ServicesExecutor.get_sluzby_od_do(start_date, end_date)
    
    # Získej seznam zaměstnanců pro formuláře
    from modules.personnel.models import ZamestnanecAOON
    zamestnanci = ZamestnanecAOON.query.filter_by(aktivni=True).order_by(ZamestnanecAOON.prijmeni).all()
    
    # Názvy měsíců
    nazvy_mesicu = [
        'Leden', 'Únor', 'Březen', 'Duben', 'Květen', 'Červen',
        'Červenec', 'Srpen', 'Září', 'Říjen', 'Listopad', 'Prosinec'
    ]
    
    # Vypočítej měsíce, které se mají zobrazit (od dnešního měsíce rok dopředu)
    mesice_k_zobrazeni = []
    current_date = dnes.replace(day=1)  # Začni od prvního dne aktuálního měsíce
    end_month = end_date.replace(day=1)
    
    while current_date <= end_month:
        mesice_k_zobrazeni.append({
            'rok': current_date.year,
            'mesic': current_date.month,
            'nazev': nazvy_mesicu[current_date.month - 1]
        })
        # Přesuň se na další měsíc
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    # Pomocné funkce pro šablonu
    def get_days_in_month(year, month):
        """Vrátí počet dní v měsíci"""
        return monthrange(year, month)[1]
    
    def get_first_weekday(year, month):
        """Vrátí den v týdnu pro první den měsíce (0=pondělí)"""
        return date(year, month, 1).weekday()
    
    # Přehled služeb pro aktuální měsíc
    aktualni_mesic = dnes.month
    aktualni_rok = dnes.year
    mesic_key = f'{aktualni_rok}-{aktualni_mesic:02d}'
    sluzby_aktualni_mesic = mesice.get(mesic_key, [])
    
    # Funkce pro výpočet hodin z časů
    def vypocitej_hodiny(hodina_od_str, hodina_do_str):
        """Vypočítá počet hodin mezi dvěma časy"""
        try:
            from datetime import datetime
            if not hodina_od_str or not hodina_do_str:
                return 0.0
            od = datetime.strptime(hodina_od_str, '%H:%M')
            do = datetime.strptime(hodina_do_str, '%H:%M')
            rozdil = do - od
            hodiny = rozdil.total_seconds() / 3600
            return max(0.0, hodiny)
        except:
            return 0.0
    
    # Spočítej hodiny podle typu a zaměstnance
    from collections import defaultdict
    prehled_sluzeb = defaultdict(lambda: {'fixni': 0.0, 'rotujici': 0.0, 'nedele': 0.0})
    
    for sluzba in sluzby_aktualni_mesic:
        if sluzba.get('zamestnanec_id'):
            zam_id = sluzba['zamestnanec_id']
            typ = sluzba.get('typ', '')
            if typ in ['fixni', 'rotujici', 'nedele']:
                hodina_od = sluzba.get('hodina_od', '08:00')
                hodina_do = sluzba.get('hodina_do', '16:00')
                hodiny = vypocitej_hodiny(hodina_od, hodina_do)
                prehled_sluzeb[zam_id][typ] += hodiny
    
    # Získej všechny zaměstnance, kteří mají nějaké služby (včetně těch s nedělními)
    prehled_sluzeb_jmena = {}
    for zam_id, hours in prehled_sluzeb.items():
        zamestnanec = ZamestnanecAOON.query.get(zam_id)
        if zamestnanec:
            prehled_sluzeb_jmena[zam_id] = {
                'jmeno': zamestnanec.jmeno_plne,
                'hours': hours
            }
    
    # Seřaď podle jména
    prehled_sluzeb_jmena = dict(sorted(prehled_sluzeb_jmena.items(), key=lambda x: x[1]['jmeno']))
    
    return render_template(
        'services/index.html',
        dnes=dnes,
        start_date=start_date,
        end_date=end_date,
        mesice=mesice,
        mesice_k_zobrazeni=mesice_k_zobrazeni,
        nazvy_mesicu=nazvy_mesicu,
        prehled_sluzeb=prehled_sluzeb_jmena,
        aktualni_mesic=nazvy_mesicu[aktualni_mesic - 1],
        aktualni_rok=aktualni_rok,
        date=date,
        timedelta=timedelta,
        get_days_in_month=get_days_in_month,
        get_first_weekday=get_first_weekday
    )


@services_bp.route('/spravce')
def spravce():
    """Správce služeb - hlavní stránka"""
    # Získej všechny šablony
    templates = ServicesExecutor.get_all_templates()
    fixni = [t for t in templates if t['typ'] == 'fixni']
    nedelni = [t for t in templates if t['typ'] == 'nedele']
    
    # Rotující služby - zobrazíme všechny jako samostatné služby (pátek i sobota)
    rotujici_sluzby = Sluzba.query.filter_by(
        typ='rotujici',
        oddeleni='dospělé'
    ).order_by(Sluzba.datum.desc()).all()
    
    # Převeď na seznam slovníků pro šablonu
    rotujici = []
    for sluzba in rotujici_sluzby:
        rotujici.append({
            'id': sluzba.id,
            'datum': sluzba.datum,
            'den_v_tydnu': sluzba.den_v_tydnu,
            'den_nazev': sluzba.den_nazev,
            'hodina_od': sluzba.hodina_od,
            'hodina_do': sluzba.hodina_do,
            'zamestnanec': sluzba.zamestnanec,
            'zamestnanec_id': sluzba.zamestnanec_id
        })
    
    return render_template(
        'services/spravce.html',
        fixni=fixni,
        rotujici=rotujici,
        nedelni=nedelni
    )


@services_bp.route('/novy/fixni', methods=['GET', 'POST'])
def novy_fixni():
    """Vytvoření nové fixní služby s možností více zaměstnanců"""
    if request.method == 'POST':
        # Získej data zaměstnanců z formuláře
        zamestnanci_data = []
        
        # Formulář může obsahovat více zaměstnanců
        # Očekáváme pole: zamestnanec_id[], hodina_od[], hodina_do[]
        zamestnanec_ids = request.form.getlist('zamestnanec_id[]')
        hodina_od_list = request.form.getlist('hodina_od[]')
        hodina_do_list = request.form.getlist('hodina_do[]')
        
        # Zkombinuj data
        for i, zam_id in enumerate(zamestnanec_ids):
            if zam_id and zam_id.strip():
                zamestnanci_data.append({
                    'zamestnanec_id': int(zam_id),
                    'hodina_od': hodina_od_list[i] if i < len(hodina_od_list) else '08:00',
                    'hodina_do': hodina_do_list[i] if i < len(hodina_do_list) else '16:00'
                })
        
        result = ServicesExecutor.create_fixni_sluzba(
            nazev=request.form.get('nazev'),
            oddeleni=request.form.get('oddeleni'),
            den_v_tydnu=int(request.form.get('den_v_tydnu')),
            zamestnanci_data=zamestnanci_data,
            poznamka=request.form.get('poznamka')
        )
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('services.index'))
        else:
            flash(f"Chyba: {result['error']}", 'danger')
    
    from modules.personnel.models import ZamestnanecAOON
    zamestnanci = ZamestnanecAOON.query.filter_by(aktivni=True).order_by(ZamestnanecAOON.prijmeni).all()
    
    dny_v_tydnu = [
        (0, 'Pondělí'),
        (2, 'Středa'),
        (3, 'Čtvrtek'),
        (4, 'Pátek'),
        (5, 'Sobota'),
        (6, 'Neděle')
    ]
    
    # Seznam hodin
    hodiny = [
        '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00'
    ]
    
    return render_template('services/novy_fixni.html', zamestnanci=zamestnanci, dny_v_tydnu=dny_v_tydnu, hodiny=hodiny)


@services_bp.route('/spravce/rotujici')
def spravce_rotujici():
    """Správa rotujících služeb - zobrazí pouze zadané bloky služeb (pátek+sobota)"""
    from datetime import date, timedelta
    rok = request.args.get('rok', date.today().year, type=int)
    
    # Získej pouze zadané rotující služby (páteky) v daném roce
    start_date = date(rok, 1, 1)
    end_date = date(rok, 12, 31)
    
    # Najdi všechny páteční rotující služby v roce
    sluzby_patek = Sluzba.query.filter(
        Sluzba.datum >= start_date,
        Sluzba.datum <= end_date,
        Sluzba.typ == 'rotujici',
        Sluzba.oddeleni == 'dospělé',
        Sluzba.den_v_tydnu == 4
    ).order_by(Sluzba.datum.desc()).all()
    
    # Seskup do bloků (pátek+sobota)
    bloky_sluzeb = []
    for sluzba_patek in sluzby_patek:
        sobota_datum = sluzba_patek.datum + timedelta(days=1)
        
        # Najdi sobotní službu (stejný zaměstnanec)
        sluzba_sobota = Sluzba.query.filter_by(
            datum=sobota_datum,
            typ='rotujici',
            oddeleni='dospělé',
            den_v_tydnu=5,
            zamestnanec_id=sluzba_patek.zamestnanec_id
        ).first()
        
        bloky_sluzeb.append({
            'patek_datum': sluzba_patek.datum,
            'sobota_datum': sobota_datum,
            'patek': sluzba_patek,
            'sobota': sluzba_sobota,
            'zamestnanec': sluzba_patek.zamestnanec
        })
    
    # Seřaď podle data (nejnovější první)
    bloky_sluzeb.sort(key=lambda x: x['patek_datum'], reverse=True)
    
    # Získej pouze zaměstnance, kteří slouží rotující služby
    from modules.personnel.models import ZamestnanecAOON
    from modules.users.models import User
    users_slouzi_rotujici = User.query.filter_by(slouzi_rotujici=True, aktivni=True).all()
    personnel_ids_slouzi_rotujici = [u.personnel_id for u in users_slouzi_rotujici]
    zamestnanci = ZamestnanecAOON.query.filter(
        ZamestnanecAOON.id.in_(personnel_ids_slouzi_rotujici),
        ZamestnanecAOON.aktivni == True
    ).order_by(ZamestnanecAOON.prijmeni).all() if personnel_ids_slouzi_rotujici else []
    
    return render_template(
        'services/spravce_rotujici.html',
        rok=rok,
        bloky_sluzeb=bloky_sluzeb,
        zamestnanci=zamestnanci,
        timedelta=timedelta,
        date=date
    )


@services_bp.route('/spravce/rotujici/novy', methods=['GET', 'POST'])
def spravce_rotujici_novy():
    """Vytvoření nové rotující služby - výběr data začátku a přiřazení zaměstnanců - pouze dospělé oddělení"""
    if request.method == 'POST':
        # Získej datum začátku
        datum_zacatku_str = request.form.get('datum_zacatku')
        if not datum_zacatku_str:
            flash('Musíte vybrat datum začátku', 'danger')
            return redirect(url_for('services.spravce_rotujici_novy'))
        
        try:
            datum_zacatku = date.fromisoformat(datum_zacatku_str)
        except ValueError:
            flash('Neplatné datum začátku', 'danger')
            return redirect(url_for('services.spravce_rotujici_novy'))
        
        # Získej přiřazení zaměstnanců k termínům
        prirazeni = {}  # {datum_str: zamestnanec_id}
        for key, value in request.form.items():
            if key.startswith('zamestnanec_'):
                datum_str = key.replace('zamestnanec_', '')
                if value and value != '':
                    prirazeni[datum_str] = int(value)
        
        poznamka = request.form.get('poznamka')
        
        result = ServicesExecutor.create_rotujici_sluzba(
            prirazeni=prirazeni,
            poznamka=poznamka
        )
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('services.spravce_rotujici'))
        else:
            flash(f"Chyba: {result['error']}", 'danger')
    
    # Získej pouze zaměstnance, kteří slouží rotující služby
    from modules.personnel.models import ZamestnanecAOON
    from modules.users.models import User
    users_slouzi_rotujici = User.query.filter_by(slouzi_rotujici=True, aktivni=True).all()
    personnel_ids_slouzi_rotujici = [u.personnel_id for u in users_slouzi_rotujici]
    zamestnanci = ZamestnanecAOON.query.filter(
        ZamestnanecAOON.id.in_(personnel_ids_slouzi_rotujici),
        ZamestnanecAOON.aktivni == True
    ).order_by(ZamestnanecAOON.prijmeni).all() if personnel_ids_slouzi_rotujici else []
    
    # Počet termínů = počet zaměstnanců s rotujícími službami
    pocet_zamestnancu = len(zamestnanci)
    
    # Najdi všechny páteky od dneška rok dopředu
    from datetime import date, timedelta
    start_date = date.today()
    end_date = start_date + timedelta(days=365)
    
    # Najdi všechny páteky a zkontroluj, které jsou volné (jen dospělé oddělení)
    dostupne_pateky = []
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() == 4:  # Pátek
            # Zkontroluj, zda už není služba pro tento pátek (dospělé oddělení)
            existing = Sluzba.query.filter_by(
                datum=current_date,
                typ='rotujici',
                oddeleni='dospělé'
            ).first()
            if not existing:
                dostupne_pateky.append(current_date)
        current_date += timedelta(days=1)
    
    # Najdi první nepřidanou službu (první volný pátek)
    prvni_volny = dostupne_pateky[0] if dostupne_pateky else None
    
    return render_template(
        'services/novy_rotujici.html',
        zamestnanci=zamestnanci,
        dostupne_pateky=dostupne_pateky,
        prvni_volny=prvni_volny,
        timedelta=timedelta
    )


@services_bp.route('/spravce/rotujici/<datum_str>/priradit', methods=['POST'])
def priradit_rotujici_zamestnance(datum_str):
    """Přiřadit zaměstnance k rotující službě - vytvoří službu pro daný pátek+sobota (pouze dospělé oddělení)"""
    try:
        patek_datum = date.fromisoformat(datum_str)
    except ValueError:
        flash('Neplatné datum', 'danger')
        return redirect(url_for('services.spravce_rotujici'))
    
    # Ověř, že je to pátek
    if patek_datum.weekday() != 4:
        flash('Datum musí být pátek', 'danger')
        return redirect(url_for('services.spravce_rotujici'))
    
    zamestnanec_id = int(request.form.get('zamestnanec_id'))
    # Rotující služby jsou pouze pro dospělé oddělení
    oddeleni = 'dospělé'
    
    # Zkontroluj, zda uživatel slouží rotující služby
    from modules.users.models import User
    user = User.query.filter_by(personnel_id=zamestnanec_id, slouzi_rotujici=True, aktivni=True).first()
    if not user:
        flash('Tento uživatel nemá zaškrtnuté "Slouží rotující služby"', 'warning')
        return redirect(url_for('services.spravce_rotujici', rok=patek_datum.year))
    
    sobota_datum = patek_datum + timedelta(days=1)
    
    # Zkontroluj, zda už není služba pro tento pátek
    existing_patek = Sluzba.query.filter_by(
        datum=patek_datum,
        oddeleni=oddeleni,
        typ='rotujici'
    ).first()
    
    if existing_patek:
        # Aktualizuj existující službu
        existing_patek.zamestnanec_id = zamestnanec_id
        # Aktualizuj i sobotu
        existing_sobota = Sluzba.query.filter_by(
            datum=sobota_datum,
            oddeleni=oddeleni,
            typ='rotujici'
        ).first()
        if existing_sobota:
            existing_sobota.zamestnanec_id = zamestnanec_id
        flash('Služba byla aktualizována', 'success')
    else:
        # Vytvoř novou službu pro pátek (13:00-16:00)
        sluzba_patek = Sluzba(
            template_id=None,
            datum=patek_datum,
            den_v_tydnu=4,  # Pátek
            oddeleni=oddeleni,
            hodina_od='13:00',
            hodina_do='16:00',
            zamestnanec_id=zamestnanec_id,
            typ='rotujici'
        )
        db.session.add(sluzba_patek)
        
        # Vytvoř službu pro sobotu (9:00-11:00)
        sluzba_sobota = Sluzba(
            template_id=None,
            datum=sobota_datum,
            den_v_tydnu=5,  # Sobota
            oddeleni=oddeleni,
            hodina_od='09:00',
            hodina_do='11:00',
            zamestnanec_id=zamestnanec_id,
            typ='rotujici'
        )
        db.session.add(sluzba_sobota)
        flash('Služba byla vytvořena a zaměstnanec přiřazen', 'success')
    
    db.session.commit()
    return redirect(url_for('services.spravce_rotujici', rok=patek_datum.year))


@services_bp.route('/spravce/nedele')
def spravce_nedele():
    """Správa nedělních služeb - seznam nedělí s možností přiřadit uživatele"""
    rok = request.args.get('rok', 2026, type=int)
    
    # Získej všechny neděle v roce
    from datetime import date, timedelta
    start_date = date(rok, 1, 1)
    end_date = date(rok, 12, 31)
    
    # Najdi všechny neděle
    nedele = []
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() == 6:  # Neděle
            nedele.append(current_date)
        current_date += timedelta(days=1)
    
    # Pro každou neděli získej služby (pouze dospělé oddělení)
    nedele_sluzby = {}
    for nedele_datum in nedele:
        sluzby = Sluzba.query.filter_by(
            datum=nedele_datum,
            oddeleni='dospělé',
            typ='nedele'
        ).all()
        nedele_sluzby[nedele_datum.isoformat()] = sluzby
    
    # Získej pouze zaměstnance, kteří slouží neděle
    from modules.personnel.models import ZamestnanecAOON
    from modules.users.models import User
    users_slouzi_nedele = User.query.filter_by(slouzi_nedele=True, aktivni=True).all()
    personnel_ids_slouzi_nedele = [u.personnel_id for u in users_slouzi_nedele]
    zamestnanci = ZamestnanecAOON.query.filter(
        ZamestnanecAOON.id.in_(personnel_ids_slouzi_nedele),
        ZamestnanecAOON.aktivni == True
    ).order_by(ZamestnanecAOON.prijmeni).all() if personnel_ids_slouzi_nedele else []
    
    return render_template(
        'services/spravce_nedele.html',
        rok=rok,
        nedele=nedele,
        nedele_sluzby=nedele_sluzby,
        zamestnanci=zamestnanci
    )


@services_bp.route('/spravce/nedele/novy', methods=['GET', 'POST'])
def novy_nedele():
    """Vytvoření nové nedělní služby"""
    if request.method == 'POST':
        zamestnanci_ids = [int(id) for id in request.form.getlist('zamestnanci_ids')]
        
        result = ServicesExecutor.create_nedelni_sluzba(
            nazev=request.form.get('nazev'),
            oddeleni=request.form.get('oddeleni'),
            zamestnanci_ids=zamestnanci_ids,
            poznamka=request.form.get('poznamka')
        )
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('services.spravce_nedele'))
        else:
            flash(f"Chyba: {result['error']}", 'danger')
    
    # Získej pouze zaměstnance, kteří slouží neděle
    from modules.personnel.models import ZamestnanecAOON
    from modules.users.models import User
    users_slouzi_nedele = User.query.filter_by(slouzi_nedele=True, aktivni=True).all()
    personnel_ids_slouzi_nedele = [u.personnel_id for u in users_slouzi_nedele]
    zamestnanci = ZamestnanecAOON.query.filter(
        ZamestnanecAOON.id.in_(personnel_ids_slouzi_nedele),
        ZamestnanecAOON.aktivni == True
    ).order_by(ZamestnanecAOON.prijmeni).all() if personnel_ids_slouzi_nedele else []
    
    return render_template('services/novy_nedele.html', zamestnanci=zamestnanci)


@services_bp.route('/spravce/nedele/<datum_str>/priradit', methods=['POST'])
def priradit_nedele_zamestnance(datum_str):
    """Přiřadit zaměstnance k nedělní službě - vytvoří službu pro daný den"""
    try:
        nedele_datum = date.fromisoformat(datum_str)
    except ValueError:
        flash('Neplatné datum', 'danger')
        return redirect(url_for('services.spravce_nedele'))
    
    zamestnanec_id = int(request.form.get('zamestnanec_id'))
    oddeleni = request.form.get('oddeleni', 'dospělé')  # Vždy dospělé pro neděle
    
    # Zkontroluj, zda uživatel slouží neděle
    from modules.users.models import User
    user = User.query.filter_by(personnel_id=zamestnanec_id, slouzi_nedele=True, aktivni=True).first()
    if not user:
        flash('Tento uživatel nemá zaškrtnuté "Slouží neděle"', 'warning')
        return redirect(url_for('services.spravce_nedele', rok=nedele_datum.year))
    
    # Zkontroluj, zda už není služba pro tento den a oddělení
    sluzba = Sluzba.query.filter_by(
        datum=nedele_datum,
        oddeleni=oddeleni,
        typ='nedele'
    ).first()
    
    if sluzba:
        # Aktualizuj existující službu
        sluzba.zamestnanec_id = zamestnanec_id
        flash('Služba byla aktualizována', 'success')
    else:
        # Vytvoř novou službu
        sluzba = Sluzba(
            template_id=None,  # Nedělní služby nepotřebují šablonu
            datum=nedele_datum,
            den_v_tydnu=6,  # Neděle
            oddeleni=oddeleni,
            hodina_od='14:00',
            hodina_do='17:00',
            zamestnanec_id=zamestnanec_id,
            typ='nedele'
        )
        db.session.add(sluzba)
        flash('Služba byla vytvořena a zaměstnanec přiřazen', 'success')
    
    db.session.commit()
    return redirect(url_for('services.spravce_nedele', rok=nedele_datum.year))


@services_bp.route('/spravce/rotujici/blok/<patek_datum>/vymenit', methods=['GET', 'POST'])
def vymenit_rotujici_blok(patek_datum):
    """Vyměnit blok rotujících služeb (pátek+sobota) s jiným blokem"""
    try:
        patek_datum_obj = date.fromisoformat(patek_datum)
    except ValueError:
        flash('Neplatné datum', 'danger')
        return redirect(url_for('services.spravce_rotujici'))
    
    sobota_datum = patek_datum_obj + timedelta(days=1)
    
    # Najdi páteční a sobotní službu
    sluzba_patek = Sluzba.query.filter_by(
        datum=patek_datum_obj,
        typ='rotujici',
        oddeleni='dospělé',
        den_v_tydnu=4
    ).first()
    
    if not sluzba_patek:
        flash('Služba pro tento pátek neexistuje', 'danger')
        return redirect(url_for('services.spravce_rotujici'))
    
    sluzba_sobota = Sluzba.query.filter_by(
        datum=sobota_datum,
        typ='rotujici',
        oddeleni='dospělé',
        den_v_tydnu=5,
        zamestnanec_id=sluzba_patek.zamestnanec_id
    ).first()
    
    if request.method == 'POST':
        druhy_patek_datum_str = request.form.get('druhy_patek_datum')
        try:
            druhy_patek_datum = date.fromisoformat(druhy_patek_datum_str)
        except ValueError:
            flash('Neplatné datum druhé služby', 'danger')
            return redirect(url_for('services.vymenit_rotujici_blok', patek_datum=patek_datum))
        
        druha_sobota_datum = druhy_patek_datum + timedelta(days=1)
        
        # Najdi druhou páteční a sobotní službu
        druha_sluzba_patek = Sluzba.query.filter_by(
            datum=druhy_patek_datum,
            typ='rotujici',
            oddeleni='dospělé',
            den_v_tydnu=4
        ).first()
        
        if not druha_sluzba_patek:
            flash('Druhá služba neexistuje', 'danger')
            return redirect(url_for('services.vymenit_rotujici_blok', patek_datum=patek_datum))
        
        druha_sluzba_sobota = Sluzba.query.filter_by(
            datum=druha_sobota_datum,
            typ='rotujici',
            oddeleni='dospělé',
            den_v_tydnu=5,
            zamestnanec_id=druha_sluzba_patek.zamestnanec_id
        ).first()
        
        # Vyměň zaměstnance v obou blocích
        zam1 = sluzba_patek.zamestnanec_id
        zam2 = druha_sluzba_patek.zamestnanec_id
        
        sluzba_patek.zamestnanec_id = zam2
        if sluzba_sobota:
            sluzba_sobota.zamestnanec_id = zam2
        
        druha_sluzba_patek.zamestnanec_id = zam1
        if druha_sluzba_sobota:
            druha_sluzba_sobota.zamestnanec_id = zam1
        
        # Zaloguj výměnu
        from modules.services.models import SluzbaVymena
        try:
            from flask_login import current_user
            user_id = current_user.id if current_user.is_authenticated else None
        except:
            user_id = None
        
        vymena = SluzbaVymena(
            sluzba1_id=sluzba_patek.id,
            sluzba2_id=druha_sluzba_patek.id,
            zamestnanec1_id=zam1,
            zamestnanec2_id=zam2,
            vytvoril_user_id=user_id,
            schvaleno=True
        )
        db.session.add(vymena)
        sluzba_patek.je_vymena = True
        druha_sluzba_patek.je_vymena = True
        
        db.session.commit()
        flash('Bloky služeb byly vyměněny', 'success')
        return redirect(url_for('services.spravce_rotujici', rok=patek_datum_obj.year))
    
    # Získej všechny ostatní bloky pro výběr (zadané bloky v roce)
    rok = patek_datum_obj.year
    start_date = date(rok, 1, 1)
    end_date = date(rok, 12, 31)
    
    ostatni_sluzby_patek = Sluzba.query.filter(
        Sluzba.datum >= start_date,
        Sluzba.datum <= end_date,
        Sluzba.typ == 'rotujici',
        Sluzba.oddeleni == 'dospělé',
        Sluzba.den_v_tydnu == 4,
        Sluzba.id != sluzba_patek.id
    ).order_by(Sluzba.datum).all()
    
    # Vytvoř seznam bloků pro výběr
    vsechny_bloky = []
    for sluzba_p in ostatni_sluzby_patek:
        sobota_d = sluzba_p.datum + timedelta(days=1)
        sluzba_s = Sluzba.query.filter_by(
            datum=sobota_d,
            typ='rotujici',
            oddeleni='dospělé',
            den_v_tydnu=5,
            zamestnanec_id=sluzba_p.zamestnanec_id
        ).first()
        
        vsechny_bloky.append({
            'patek_datum': sluzba_p.datum,
            'sobota_datum': sobota_d,
            'sluzba_patek': sluzba_p,
            'sluzba_sobota': sluzba_s,
            'zamestnanec': sluzba_p.zamestnanec
        })
    
    return render_template(
        'services/vymenit_rotujici_blok.html',
        patek_datum=patek_datum_obj,
        sobota_datum=sobota_datum,
        sluzba_patek=sluzba_patek,
        sluzba_sobota=sluzba_sobota,
        vsechny_bloky=vsechny_bloky,
        timedelta=timedelta
    )


@services_bp.route('/spravce/rotujici/<int:sluzba_id>/vymenit', methods=['GET', 'POST'])
def vymenit_rotujici_sluzbu(sluzba_id):
    """Vyměnit rotující službu s jinou službou"""
    sluzba = Sluzba.query.get_or_404(sluzba_id)
    
    if sluzba.typ != 'rotujici' or sluzba.oddeleni != 'dospělé':
        flash('Tato služba není rotující služba pro dospělé oddělení', 'danger')
        return redirect(url_for('services.spravce'))
    
    if request.method == 'POST':
        druha_sluzba_id = int(request.form.get('druha_sluzba_id'))
        druha_sluzba = Sluzba.query.get_or_404(druha_sluzba_id)
        
        if druha_sluzba.typ != 'rotujici' or druha_sluzba.oddeleni != 'dospělé':
            flash('Druhá služba není rotující služba pro dospělé oddělení', 'danger')
            return redirect(url_for('services.vymenit_rotujici_sluzbu', sluzba_id=sluzba_id))
        
        # Vyměň zaměstnance - každá služba je samostatná
        zam1 = sluzba.zamestnanec_id
        zam2 = druha_sluzba.zamestnanec_id
        
        sluzba.zamestnanec_id = zam2
        druha_sluzba.zamestnanec_id = zam1
        
        # Zaloguj výměnu
        from modules.services.models import SluzbaVymena
        try:
            from flask_login import current_user
            user_id = current_user.id if current_user.is_authenticated else None
        except:
            user_id = None
        
        vymena = SluzbaVymena(
            sluzba1_id=sluzba.id,
            sluzba2_id=druha_sluzba.id,
            zamestnanec1_id=zam1,
            zamestnanec2_id=zam2,
            vytvoril_user_id=user_id,
            schvaleno=True
        )
        db.session.add(vymena)
        sluzba.je_vymena = True
        druha_sluzba.je_vymena = True
        
        db.session.commit()
        flash('Služby byly vyměněny', 'success')
        return redirect(url_for('services.spravce'))
    
    # Získej všechny rotující služby pro výběr (stejný den v týdnu)
    rotujici_sluzby = Sluzba.query.filter_by(
        typ='rotujici',
        oddeleni='dospělé',
        den_v_tydnu=sluzba.den_v_tydnu  # Stejný den jako aktuální služba
    ).filter(
        Sluzba.id != sluzba_id,
        Sluzba.datum >= date.today()
    ).order_by(Sluzba.datum).all()
    
    return render_template(
        'services/vymenit_rotujici_sluzbu.html',
        sluzba=sluzba,
        rotujici_sluzby=rotujici_sluzby
    )


@services_bp.route('/spravce/rotujici/blok/<patek_datum>/zmenit', methods=['GET', 'POST'])
def zmenit_rotujici_blok(patek_datum):
    """Změnit zaměstnance v bloku rotujících služeb (pátek+sobota)"""
    try:
        patek_datum_obj = date.fromisoformat(patek_datum)
    except ValueError:
        flash('Neplatné datum', 'danger')
        return redirect(url_for('services.spravce_rotujici'))
    
    sobota_datum = patek_datum_obj + timedelta(days=1)
    
    # Najdi páteční a sobotní službu
    sluzba_patek = Sluzba.query.filter_by(
        datum=patek_datum_obj,
        typ='rotujici',
        oddeleni='dospělé',
        den_v_tydnu=4
    ).first()
    
    if not sluzba_patek:
        flash('Služba pro tento pátek neexistuje', 'danger')
        return redirect(url_for('services.spravce_rotujici'))
    
    sluzba_sobota = Sluzba.query.filter_by(
        datum=sobota_datum,
        typ='rotujici',
        oddeleni='dospělé',
        den_v_tydnu=5,
        zamestnanec_id=sluzba_patek.zamestnanec_id
    ).first()
    
    if request.method == 'POST':
        novy_zamestnanec_id = int(request.form.get('zamestnanec_id'))
        stary_zamestnanec_id = sluzba_patek.zamestnanec_id
        
        # Zkontroluj, zda uživatel slouží rotující služby
        from modules.users.models import User
        user = User.query.filter_by(personnel_id=novy_zamestnanec_id, slouzi_rotujici=True, aktivni=True).first()
        if not user:
            flash('Tento uživatel nemá zaškrtnuté "Slouží rotující služby"', 'warning')
            return redirect(url_for('services.zmenit_rotujici_blok', patek_datum=patek_datum))
        
        # Změň zaměstnance v obou službách bloku
        sluzba_patek.zamestnanec_id = novy_zamestnanec_id
        if sluzba_sobota:
            sluzba_sobota.zamestnanec_id = novy_zamestnanec_id
        
        # Zaloguj změnu
        from modules.services.models import SluzbaVynimka
        try:
            from flask_login import current_user
            user_id = current_user.id if current_user.is_authenticated else None
        except:
            user_id = None
        
        vynimka = SluzbaVynimka(
            sluzba_id=sluzba_patek.id,
            datum=sluzba_patek.datum,
            oddeleni=sluzba_patek.oddeleni,
            hodina_od=sluzba_patek.hodina_od,
            hodina_do=sluzba_patek.hodina_do,
            zamestnanec_id=novy_zamestnanec_id,
            poznamka=f'Změna zaměstnance v bloku z {stary_zamestnanec_id} na {novy_zamestnanec_id}',
            vytvoril_user_id=user_id
        )
        db.session.add(vynimka)
        sluzba_patek.je_vynimka = True
        
        db.session.commit()
        flash('Zaměstnanec v bloku byl změněn', 'success')
        return redirect(url_for('services.spravce_rotujici', rok=patek_datum_obj.year))
    
    # Získej zaměstnance s rotujícími službami
    from modules.personnel.models import ZamestnanecAOON
    from modules.users.models import User
    users_slouzi_rotujici = User.query.filter_by(slouzi_rotujici=True, aktivni=True).all()
    personnel_ids_slouzi_rotujici = [u.personnel_id for u in users_slouzi_rotujici]
    zamestnanci = ZamestnanecAOON.query.filter(
        ZamestnanecAOON.id.in_(personnel_ids_slouzi_rotujici),
        ZamestnanecAOON.aktivni == True
    ).order_by(ZamestnanecAOON.prijmeni).all() if personnel_ids_slouzi_rotujici else []
    
    return render_template(
        'services/zmenit_rotujici_blok.html',
        patek_datum=patek_datum_obj,
        sobota_datum=sobota_datum,
        sluzba_patek=sluzba_patek,
        sluzba_sobota=sluzba_sobota,
        zamestnanci=zamestnanci
    )


@services_bp.route('/spravce/rotujici/<int:sluzba_id>/zmenit', methods=['GET', 'POST'])
def zmenit_rotujici_sluzbu(sluzba_id):
    """Změnit zaměstnance v rotující službě (pro správu služeb - jednotlivé služby)"""
    sluzba = Sluzba.query.get_or_404(sluzba_id)
    
    if sluzba.typ != 'rotujici' or sluzba.oddeleni != 'dospělé':
        flash('Tato služba není rotující služba pro dospělé oddělení', 'danger')
        return redirect(url_for('services.spravce'))
    
    if request.method == 'POST':
        novy_zamestnanec_id = int(request.form.get('zamestnanec_id'))
        stary_zamestnanec_id = sluzba.zamestnanec_id
        
        # Zkontroluj, zda uživatel slouží rotující služby
        from modules.users.models import User
        user = User.query.filter_by(personnel_id=novy_zamestnanec_id, slouzi_rotujici=True, aktivni=True).first()
        if not user:
            flash('Tento uživatel nemá zaškrtnuté "Slouží rotující služby"', 'warning')
            return redirect(url_for('services.zmenit_rotujici_sluzbu', sluzba_id=sluzba_id))
        
        # Změň zaměstnance - každá služba je samostatná
        sluzba.zamestnanec_id = novy_zamestnanec_id
        
        # Zaloguj změnu
        from modules.services.models import SluzbaVynimka
        try:
            from flask_login import current_user
            user_id = current_user.id if current_user.is_authenticated else None
        except:
            user_id = None
        
        vynimka = SluzbaVynimka(
            sluzba_id=sluzba.id,
            datum=sluzba.datum,
            oddeleni=sluzba.oddeleni,
            hodina_od=sluzba.hodina_od,
            hodina_do=sluzba.hodina_do,
            zamestnanec_id=novy_zamestnanec_id,
            poznamka=f'Změna zaměstnance z {stary_zamestnanec_id} na {novy_zamestnanec_id}',
            vytvoril_user_id=user_id
        )
        db.session.add(vynimka)
        sluzba.je_vynimka = True
        
        db.session.commit()
        flash('Zaměstnanec byl změněn', 'success')
        return redirect(url_for('services.spravce'))
    
    # Získej zaměstnance s rotujícími službami
    from modules.personnel.models import ZamestnanecAOON
    from modules.users.models import User
    users_slouzi_rotujici = User.query.filter_by(slouzi_rotujici=True, aktivni=True).all()
    personnel_ids_slouzi_rotujici = [u.personnel_id for u in users_slouzi_rotujici]
    zamestnanci = ZamestnanecAOON.query.filter(
        ZamestnanecAOON.id.in_(personnel_ids_slouzi_rotujici),
        ZamestnanecAOON.aktivni == True
    ).order_by(ZamestnanecAOON.prijmeni).all() if personnel_ids_slouzi_rotujici else []
    
    return render_template(
        'services/zmenit_rotujici_sluzbu.html',
        sluzba=sluzba,
        zamestnanci=zamestnanci
    )


@services_bp.route('/sluzba/<int:sluzba_id>/log')
def log_sluzby(sluzba_id):
    """Zobrazí log změn služby"""
    sluzba = Sluzba.query.get_or_404(sluzba_id)
    
    # Získej všechny výjimky a výměny pro tuto službu
    vynimky = SluzbaVynimka.query.filter_by(sluzba_id=sluzba_id).order_by(SluzbaVynimka.datum_vytvoreni.desc()).all()
    vymeny = SluzbaVymena.query.filter(
        (SluzbaVymena.sluzba1_id == sluzba_id) | (SluzbaVymena.sluzba2_id == sluzba_id)
    ).order_by(SluzbaVymena.datum_vytvoreni.desc()).all()
    
    # Vytvoř seznam všech změn
    log_entries = []
    
    # Přidej výjimky
    for vynimka in vynimky:
        log_entries.append({
            'typ': 'vynimka',
            'datum': vynimka.datum_vytvoreni,
            'popis': f'Výjimka: {vynimka.zamestnanec.jmeno_plne if vynimka.zamestnanec else "Neznámý"} ({vynimka.hodina_od}-{vynimka.hodina_do})',
            'poznamka': vynimka.poznamka,
            'vytvoril': vynimka.vytvoril_user.username if vynimka.vytvoril_user else 'Systém'
        })
    
    # Přidej výměny
    for vymena in vymeny:
        if vymena.sluzba1_id == sluzba_id:
            druha_sluzba = vymena.sluzba2
            zam1 = vymena.zamestnanec1
            zam2 = vymena.zamestnanec2
        else:
            druha_sluzba = vymena.sluzba1
            zam1 = vymena.zamestnanec2
            zam2 = vymena.zamestnanec1
        
        log_entries.append({
            'typ': 'vymena',
            'datum': vymena.datum_vytvoreni,
            'popis': f'Výměna s {druha_sluzba.datum.strftime("%d.%m.%Y")}: {zam1.jmeno_plne if zam1 else "Neznámý"} ↔ {zam2.jmeno_plne if zam2 else "Neznámý"}',
            'poznamka': vymena.poznamka,
            'vytvoril': vymena.vytvoril_user.username if vymena.vytvoril_user else 'Systém'
        })
    
    # Přidej vytvoření služby
    log_entries.append({
        'typ': 'vytvoreni',
        'datum': sluzba.datum_vytvoreni,
        'popis': f'Vytvoření služby: {sluzba.zamestnanec.jmeno_plne if sluzba.zamestnanec else "Neznámý"}',
        'poznamka': sluzba.poznamka,
        'vytvoril': 'Systém'
    })
    
    # Seřaď podle data (nejnovější první)
    log_entries.sort(key=lambda x: x['datum'], reverse=True)
    
    return render_template(
        'services/log_sluzby.html',
        sluzba=sluzba,
        log_entries=log_entries
    )


@services_bp.route('/sluzba/<int:sluzba_id>/smazat', methods=['POST'])
def smazat_sluzbu(sluzba_id):
    """Smazání konkrétní služby (např. státní svátek)"""
    sluzba = Sluzba.query.get_or_404(sluzba_id)
    datum = sluzba.datum
    datum_str = datum.isoformat()
    typ = sluzba.typ
    oddeleni = sluzba.oddeleni
    
    try:
        # Pro rotující služby - smaž i sobotu, pokud je to pátek
        if typ == 'rotujici' and datum.weekday() == 4:  # Pátek
            sobota_datum = datum + timedelta(days=1)
            sobota_sluzba = Sluzba.query.filter_by(
                datum=sobota_datum,
                typ='rotujici',
                oddeleni=oddeleni
            ).first()
            if sobota_sluzba:
                db.session.delete(sobota_sluzba)
        
        db.session.delete(sluzba)
        db.session.commit()
        flash(f'Služba pro {datum.strftime("%d.%m.%Y")} byla smazána', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Chyba při mazání: {str(e)}', 'danger')
    
    # Přesměruj zpět - pokud je to rotující služba, přesměruj na správu rotujících služeb
    if typ == 'rotujici':
        return redirect(url_for('services.spravce_rotujici', rok=datum.year))
    
    # Jinak přesměruj na kartu služby dne
    return redirect(url_for('services.sluzba_dne', datum_str=datum_str))


@services_bp.route('/template/<int:template_id>/smazat', methods=['POST'])
def smazat_template(template_id):
    """Smazání šablony služby"""
    result = ServicesExecutor.delete_template(template_id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f"Chyba: {result['error']}", 'danger')
    
    return redirect(url_for('services.index'))


@services_bp.route('/fixni/<int:template_id>/upravit', methods=['GET', 'POST'])
def upravit_fixni(template_id):
    """Úprava fixní služby (šablony)"""
    from modules.services.models import SluzbaTemplate
    template = SluzbaTemplate.query.get_or_404(template_id)
    
    if template.typ != 'fixni':
        flash('Tato služba není fixní', 'danger')
        return redirect(url_for('services.spravce'))
    
    if request.method == 'POST':
        # Získej data zaměstnanců z formuláře
        zamestnanci_data = []
        zamestnanec_ids = request.form.getlist('zamestnanec_id[]')
        hodina_od_list = request.form.getlist('hodina_od[]')
        hodina_do_list = request.form.getlist('hodina_do[]')
        
        for i, zam_id in enumerate(zamestnanec_ids):
            if zam_id and zam_id.strip():
                zamestnanci_data.append({
                    'zamestnanec_id': int(zam_id),
                    'hodina_od': hodina_od_list[i] if i < len(hodina_od_list) else '08:00',
                    'hodina_do': hodina_do_list[i] if i < len(hodina_do_list) else '16:00'
                })
        
        if not zamestnanci_data:
            flash('Musíte zadat alespoň jednoho zaměstnance', 'danger')
        else:
            # Aktualizuj šablonu
            template.nazev = request.form.get('nazev', template.nazev)
            template.oddeleni = request.form.get('oddeleni', template.oddeleni)
            template.den_v_tydnu = int(request.form.get('den_v_tydnu', template.den_v_tydnu))
            template.poznamka = request.form.get('poznamka', template.poznamka)
            
            # Ulož seznam zaměstnanců
            import json
            template.fixni_zamestnanci = json.dumps(zamestnanci_data)
            
            # Pro zpětnou kompatibilitu
            if zamestnanci_data:
                prvni = zamestnanci_data[0]
                template.zamestnanec_id = prvni.get('zamestnanec_id')
                template.hodina_od = prvni.get('hodina_od', '08:00')
                template.hodina_do = prvni.get('hodina_do', '16:00')
            
            try:
                db.session.commit()
                flash('Fixní služba byla upravena', 'success')
                return redirect(url_for('services.spravce'))
            except Exception as e:
                db.session.rollback()
                flash(f'Chyba při úpravě: {str(e)}', 'danger')
    
    from modules.personnel.models import ZamestnanecAOON
    zamestnanci = ZamestnanecAOON.query.filter_by(aktivni=True).order_by(ZamestnanecAOON.prijmeni).all()
    
    dny_v_tydnu = [
        (0, 'Pondělí'),
        (2, 'Středa'),
        (3, 'Čtvrtek'),
        (4, 'Pátek'),
        (5, 'Sobota'),
        (6, 'Neděle')
    ]
    
    hodiny = [
        '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00'
    ]
    
    # Načti aktuální zaměstnance
    aktualni_zamestnanci = template.fixni_zamestnanci_list
    
    return render_template(
        'services/upravit_fixni.html',
        template=template,
        zamestnanci=zamestnanci,
        dny_v_tydnu=dny_v_tydnu,
        hodiny=hodiny,
        aktualni_zamestnanci=aktualni_zamestnanci
    )


@services_bp.route('/sluzba/<int:sluzba_id>/upravit', methods=['POST'])
def upravit_sluzbu(sluzba_id):
    """Úprava konkrétní služby"""
    sluzba = Sluzba.query.get_or_404(sluzba_id)
    datum_str = request.form.get('datum_str', sluzba.datum.isoformat())
    
    # Aktualizuj službu
    zamestnanec_id = request.form.get('zamestnanec_id')
    hodina_od = request.form.get('hodina_od')
    hodina_do = request.form.get('hodina_do')
    poznamka = request.form.get('poznamka')
    
    if zamestnanec_id:
        sluzba.zamestnanec_id = int(zamestnanec_id)
    if hodina_od:
        sluzba.hodina_od = hodina_od
    if hodina_do:
        sluzba.hodina_do = hodina_do
    if poznamka is not None:
        sluzba.poznamka = poznamka
    
    try:
        db.session.commit()
        flash('Služba byla upravena', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Chyba při úpravě: {str(e)}', 'danger')
    
    return redirect(url_for('services.sluzba_dne', datum_str=datum_str))


@services_bp.route('/sluzba/den/pridat', methods=['POST'])
def pridat_sluzbu_den():
    """Přidání nové služby pro konkrétní den"""
    try:
        vybrany_datum = date.fromisoformat(request.form.get('datum'))
    except ValueError:
        flash('Neplatné datum', 'danger')
        return redirect(url_for('services.index'))
    
    zamestnanec_id = int(request.form.get('zamestnanec_id'))
    oddeleni = request.form.get('oddeleni')
    hodina_od = request.form.get('hodina_od')
    hodina_do = request.form.get('hodina_do')
    typ = request.form.get('typ', 'fixni')
    
    sluzba = Sluzba(
        template_id=None,  # Ručně přidaná služba nemá šablonu
        datum=vybrany_datum,
        den_v_tydnu=vybrany_datum.weekday(),
        oddeleni=oddeleni,
        hodina_od=hodina_od,
        hodina_do=hodina_do,
        zamestnanec_id=zamestnanec_id,
        typ=typ
    )
    
    try:
        db.session.add(sluzba)
        db.session.commit()
        flash('Služba byla přidána', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Chyba při přidávání: {str(e)}', 'danger')
    
    return redirect(url_for('services.sluzba_dne', datum_str=vybrany_datum.isoformat()))


@services_bp.route('/den/<datum_str>')
def sluzba_dne(datum_str):
    """Služba dne - karta pro každé oddělení s formulářem pro události"""
    try:
        vybrany_datum = date.fromisoformat(datum_str)
    except ValueError:
        flash('Neplatné datum', 'danger')
        return redirect(url_for('services.index'))
    
    # Získej všechny služby pro tento den
    sluzby_dne = Sluzba.query.filter_by(datum=vybrany_datum).all()
    
    # Seskup služby podle oddělení
    sluzby_po_oddelenich = {}
    for sluzba in sluzby_dne:
        oddeleni = sluzba.oddeleni
        if oddeleni not in sluzby_po_oddelenich:
            sluzby_po_oddelenich[oddeleni] = []
        sluzby_po_oddelenich[oddeleni].append(sluzba)
    
    # Získej aktivní změny (výjimky) pro tento den
    zmeny_dne = SluzbaVynimka.query.filter_by(
        datum=vybrany_datum,
        aktivni=True
    ).all()
    
    # Získej výměny, které se týkají služeb tohoto dne
    sluzby_ids = [s.id for s in sluzby_dne]
    vymeny_dne = []
    if sluzby_ids:
        vymeny_dne = SluzbaVymena.query.filter(
            ((SluzbaVymena.sluzba1_id.in_(sluzby_ids)) | (SluzbaVymena.sluzba2_id.in_(sluzby_ids))),
            SluzbaVymena.aktivni == True
        ).all()
    
    # Získej seznam zaměstnanců
    from modules.personnel.models import ZamestnanecAOON
    zamestnanci = ZamestnanecAOON.query.filter_by(aktivni=True).order_by(ZamestnanecAOON.prijmeni).all()
    
    # Získej všechny služby pro výběr výměny (kromě služeb tohoto dne)
    rok = vybrany_datum.year
    start_date = date(rok, 1, 1)
    end_date = date(rok, 12, 31)
    vsechny_sluzby = Sluzba.query.filter(
        Sluzba.datum >= start_date,
        Sluzba.datum <= end_date,
        ~Sluzba.id.in_(sluzby_ids) if sluzby_ids else True
    ).order_by(Sluzba.datum.asc()).all()
    
    # Seznam hodin
    hodiny = [
        '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00'
    ]
    
    # Název dne
    dny = ['Pondělí', 'Úterý', 'Středa', 'Čtvrtek', 'Pátek', 'Sobota', 'Neděle']
    den_nazev = dny[vybrany_datum.weekday()] if 0 <= vybrany_datum.weekday() < 7 else 'Neznámý'
    
    return render_template(
        'services/sluzba_dne.html',
        datum=vybrany_datum,
        datum_str=datum_str,
        den_nazev=den_nazev,
        sluzby_dne=sluzby_dne,
        sluzby_po_oddelenich=sluzby_po_oddelenich,
        zmeny_dne=zmeny_dne,
        vymeny_dne=vymeny_dne,
        zamestnanci=zamestnanci,
        vsechny_sluzby=vsechny_sluzby,
        hodiny=hodiny
    )


@services_bp.route('/zmena/novy', methods=['POST'])
def novy_zmena():
    """Vytvoření nové změny"""
    sluzba_id = request.form.get('sluzba_id')
    datum = date.fromisoformat(request.form.get('datum'))
    oddeleni = request.form.get('oddeleni')
    hodina_od = request.form.get('hodina_od')
    hodina_do = request.form.get('hodina_do')
    zamestnanec_id = int(request.form.get('zamestnanec_id'))
    poznamka = request.form.get('poznamka')
    
    vytvoril_user_id = session.get('current_user_id')
    
    result = ServicesExecutor.create_vynimka(
        sluzba_id=int(sluzba_id),
        datum=datum,
        oddeleni=oddeleni,
        hodina_od=hodina_od,
        hodina_do=hodina_do,
        zamestnanec_id=zamestnanec_id,
        poznamka=poznamka,
        vytvoril_user_id=vytvoril_user_id
    )
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f"Chyba: {result['error']}", 'danger')
    
    # Přesměruj zpět na službu dne
    return redirect(url_for('services.sluzba_dne', datum_str=datum.isoformat()))


@services_bp.route('/zmena/<int:vynimka_id>/smazat', methods=['POST'])
def smazat_zmena(vynimka_id):
    """Smazání změny"""
    vynimka = SluzbaVynimka.query.get(vynimka_id)
    datum_str = vynimka.datum.isoformat() if vynimka else None
    
    result = ServicesExecutor.delete_vynimka(vynimka_id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f"Chyba: {result['error']}", 'danger')
    
    # Přesměruj zpět na detail dne, pokud máme datum
    if datum_str:
        return redirect(url_for('services.sluzba_dne', datum_str=datum_str))
    return redirect(url_for('services.index'))


@services_bp.route('/vymena/novy', methods=['POST'])
def novy_vymena():
    """Vytvoření nové výměny"""
    sluzba1_id = int(request.form.get('sluzba1_id'))
    sluzba2_id = int(request.form.get('sluzba2_id'))
    poznamka = request.form.get('poznamka')
    datum_str = request.form.get('datum_str')  # Pro přesměrování zpět
    
    vytvoril_user_id = session.get('current_user_id')
    
    result = ServicesExecutor.create_vymena(
        sluzba1_id=sluzba1_id,
        sluzba2_id=sluzba2_id,
        poznamka=poznamka,
        vytvoril_user_id=vytvoril_user_id
    )
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f"Chyba: {result['error']}", 'danger')
    
    # Přesměruj zpět na detail dne, pokud máme datum
    if datum_str:
        return redirect(url_for('services.sluzba_dne', datum_str=datum_str))
    return redirect(url_for('services.index'))


@services_bp.route('/vymena/<int:vymena_id>/schvalit', methods=['POST'])
def schvalit_vymena(vymena_id):
    """Schválení výměny"""
    vymena = SluzbaVymena.query.get(vymena_id)
    datum_str = None
    if vymena and vymena.sluzba1:
        datum_str = vymena.sluzba1.datum.isoformat()
    
    result = ServicesExecutor.schvalit_vymenu(vymena_id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f"Chyba: {result['error']}", 'danger')
    
    # Přesměruj zpět na detail dne, pokud máme datum
    if datum_str:
        return redirect(url_for('services.sluzba_dne', datum_str=datum_str))
    return redirect(url_for('services.index'))


@services_bp.route('/muj-prehled')
def muj_prehled_sluzeb():
    """Můj přehled služeb - statistiky a služby uživatele"""
    # Získej aktuálního uživatele
    current_user_id = session.get('current_user_id')
    if not current_user_id:
        flash('Musíte být přihlášeni', 'warning')
        return redirect(url_for('index'))
    
    from modules.users.models import User
    user = User.query.get(current_user_id)
    if not user or not user.personnel_id:
        flash('Uživatel nemá propojený personální záznam', 'warning')
        return redirect(url_for('index'))
    
    zamestnanec_id = user.personnel_id
    rok = request.args.get('rok', 2026, type=int)
    
    # Získej statistiky
    statistiky = ServicesExecutor.get_statistiky_zamestnance(zamestnanec_id, rok)
    
    # Získej služby zaměstnance
    sluzby = ServicesExecutor.get_sluzby_pro_zamestnance(zamestnanec_id, rok)
    
    # Získej změny (výjimky), které vytvořil uživatel
    zmeny = SluzbaVynimka.query.filter_by(
        vytvoril_user_id=current_user_id,
        aktivni=True
    ).order_by(SluzbaVynimka.datum.desc()).limit(10).all()
    
    # Získej výměny, které vytvořil uživatel
    vymeny = SluzbaVymena.query.filter_by(
        vytvoril_user_id=current_user_id,
        aktivni=True
    ).order_by(SluzbaVymena.datum_vytvoreni.desc()).limit(10).all()
    
    return render_template(
        'services/muj_prehled.html',
        user=user,
        zamestnanec_id=zamestnanec_id,
        rok=rok,
        statistiky=statistiky,
        sluzby=sluzby,
        zmeny=zmeny,
        vymeny=vymeny
    )


@services_bp.route('/ulozit-udalost', methods=['POST'])
def ulozit_udalost():
    """Uložení události dne"""
    # TODO: Implementovat ukládání událostí do databáze
    # Prozatím pouze přesměrujeme zpět
    datum_str = request.form.get('datum')
    if datum_str:
        flash('Událost byla přidána (funkce bude dokončena)', 'info')
        return redirect(url_for('services.sluzba_dne', datum_str=datum_str))
    return redirect(url_for('services.index'))
