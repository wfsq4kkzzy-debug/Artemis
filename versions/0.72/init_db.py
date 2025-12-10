#!/usr/bin/env python
"""Inicializace databáze a naplnění rozpočtem na rok 2026"""

from app import app, db
from models import UctovaSkupina, RozpoctovaPolozka

def init_database():
    """Vytvořit tabulky a naplnit počáteční data"""
    with app.app_context():
        # Smazat starou databázi
        db.drop_all()
        print("Stará databáze smazána...")
        
        # Vytvořit nové tabulky
        db.create_all()
        print("Nové tabulky vytvořeny...")
        
        # Definice všech účtových skupin a jejich položek
        rozpocet_data = {
            # NÁKLADY
            '501': {
                'nazev': 'Spotřeba materiálu',
                'typ': 'naklad',
                'polozky': [
                    ('30', 'nákup materiálu', 38000),
                    ('31', 'čistící prostředky', 25000),
                    ('32', 'knihy', 350660),
                    ('33', 'časopisy', 35000),
                    ('35', 'drobný materiál', 40000),
                    ('35', 'vybavení knihovny - Lezník', 0),
                    ('35', 'rozšíření dětského odd.', 0),
                    ('37', 'drobný majetek do 3 tis.', 0),
                    ('41', 'knihy dary', 0),
                    ('43', 'hry', 0),
                ]
            },
            '502': {
                'nazev': 'Spotřeba energie',
                'typ': 'naklad',
                'polozky': [
                    ('30', 'el.energie', 171000),
                    ('31', 'spotřeba plynu', 130000),
                    ('35', 'voda spotřebovaná', 10000),
                ]
            },
            '504': {
                'nazev': 'Prodané zboží',
                'typ': 'naklad',
                'polozky': [
                    ('30', 'Prodej zboží - knihy', 10000),
                ]
            },
            '508': {
                'nazev': 'Změna stavu zásob vlastní činnosti',
                'typ': 'naklad',
                'polozky': [
                    ('30', 'Vlastní výrobky', 10000),
                ]
            },
            '511': {
                'nazev': 'Opravy a udržování',
                'typ': 'naklad',
                'polozky': [
                    ('30', 'opravy a údržba', 20000),
                    ('30', 'opravy a údržba - odd. dětské', 0),
                    ('30', 'opravy a údržba - čerpadlo', 0),
                ]
            },
            '512': {
                'nazev': 'Cestovné',
                'typ': 'naklad',
                'polozky': [
                    ('30', 'cestovné', 10000),
                ]
            },
            '513': {
                'nazev': 'Náklady na reprezentaci',
                'typ': 'naklad',
                'polozky': [
                    ('30', 'pohoštění', 8000),
                    ('34', 'prezentace knih', 0),
                ]
            },
            '518': {
                'nazev': 'Ostatní služby',
                'typ': 'naklad',
                'polozky': [
                    ('30', 'ostatní služby', 202000),
                    ('30', 'skartace dokumentů', 0),
                    ('32', 'poštovné', 25000),
                    ('33', 'telefon, internet', 110000),
                    ('34', 'stravné', 0),
                    ('35', 'školení', 5000),
                    ('36', 'bankovní poplatky', 10000),
                    ('37', 'servis progr. SHOPTET', 9000),
                    ('38', 'odpad - LIKO', 2500),
                    ('39', 'stočné', 20000),
                    ('43', 'Tiskové služby', 30000),
                    ('44', 'Knih. systém KOHA, Tritius', 68000),
                    ('46', 'kurzy - lektoři', 10000),
                    ('48', 'jízdné, ubytování', 0),
                ]
            },
            '521': {
                'nazev': 'Mzdové náklady',
                'typ': 'naklad',
                'polozky': [
                    ('10', 'mzdy', 4000000),
                    ('20', 'OON', 320000),
                ]
            },
            '524': {
                'nazev': 'Zákonné sociální pojištění',
                'typ': 'naklad',
                'polozky': [
                    ('', 'soc.poj.,zdrav. poj.-fond odměn', 0),
                    ('30', 'sociální poj.', 992000),
                    ('31', 'zdravotní pojištění', 360000),
                ]
            },
            '525': {
                'nazev': 'Jiné sociální pojištění',
                'typ': 'naklad',
                'polozky': [
                    ('30', 'zákonné poj.odpověd.', 10000),
                ]
            },
            '527': {
                'nazev': 'Zákonné sociální náklady',
                'typ': 'naklad',
                'polozky': [
                    ('30', 'základní příděl do FKSP', 35000),
                    ('34', 'příspěvek na stravování', 242000),
                    ('35', 'školení, lék.prohlídky,OOPP', 1000),
                ]
            },
            '549': {
                'nazev': 'Ostatní náklady z činnosti',
                'typ': 'naklad',
                'polozky': [
                    ('30', 'ostatní náklady z činnosti', 0),
                    ('35', 'pojištění majetku', 30000),
                ]
            },
            '551': {
                'nazev': 'Odpisy',
                'typ': 'naklad',
                'polozky': [
                    ('30', 'odpisy', 308080),
                ]
            },
            '558': {
                'nazev': 'Tvorba fondů',
                'typ': 'naklad',
                'polozky': [
                    ('31', 'pořízení DNM (018)', 0),
                    ('37', 'čerpadlo - vertikální zahrada', 0),
                    ('37', 'oddělení dětské', 0),
                    ('37', 'spoluúč. na dotaci VISK 3 laser', 0),
                    ('37', 'pořízení DHM (028)', 50000),
                ]
            },
            
            # VÝNOSY
            '601': {
                'nazev': 'Tržby z prodeje výrobků',
                'typ': 'vynos',
                'polozky': [
                    ('30', 'prodej vlastních výrobků - knih', 50220),
                ]
            },
            '602': {
                'nazev': 'Tržby z prodeje služeb',
                'typ': 'vynos',
                'polozky': [
                    ('30', 'tržby', 227000),
                    ('30', 'tržby knihovna Svitavy region', 184000),
                    ('40', 'tržby za tisk internet', 2000),
                    ('42', 'vzdělávací kurzy', 100000),
                ]
            },
            '603': {
                'nazev': 'Tržby za zboží',
                'typ': 'vynos',
                'polozky': [
                    ('33', 'pronájem prostor', 98000),
                ]
            },
            '604': {
                'nazev': 'Změna stavu zásob vlastní činnosti',
                'typ': 'vynos',
                'polozky': [
                    ('30', 'Prodej knih a zboží', 40000),
                    ('31', 'prodej vyřazených knih a čas.', 20000),
                ]
            },
            '648': {
                'nazev': 'Čerpání fondů',
                'typ': 'vynos',
                'polozky': [
                    ('30', 'rezervní fond', 0),
                    ('30', 'rezervní fond - čerpadlo', 0),
                    ('30', 'rezervní fond - SP, ZP z odměn', 0),
                    ('50', 'fond odměn', 0),
                ]
            },
            '662': {
                'nazev': 'Úroky',
                'typ': 'vynos',
                'polozky': [
                    ('30', 'úrok běžný rok', 50),
                ]
            },
            '672': {
                'nazev': 'Provozní dotace',
                'typ': 'vynos',
                'polozky': [
                    ('00', 'dotace na provoz a na mzdy od zřizovatel', 6816000),
                    ('20', 'příspěvek účelový - skartace', 0),
                    ('20', 'příspěvek účelový - VISK 3 laser', 0),
                    ('20', 'příspěvek účelový - Lezník', 0),
                    ('20', 'příspěvek účelový - rozšíření čítárny o dětské odd.', 0),
                    ('21', 'dotace z odpisů MK - transfer', 159970),
                    ('23', 'pracovní cesta SDRUK', 0),
                    ('33', 'Grant Ministerstvo kultury', 0),
                ]
            },
        }
        
        # Naplnit databázi
        for ucet_num, data in rozpocet_data.items():
            # Vytvořit účtovou skupinu
            uctova_skupina = UctovaSkupina(
                ucet=ucet_num,
                nazev=data['nazev'],
                typ=data['typ']
            )
            db.session.add(uctova_skupina)
            db.session.flush()  # Aby se vytvořilo ID
            
            # Vytvořit položky pro tuto účtovou skupinu
            for analyticky_ucet, nazev_polozky, castka in data['polozky']:
                polozka = RozpoctovaPolozka(
                    rok=2026,
                    uctova_skupina_id=uctova_skupina.id,
                    analyticky_ucet=analyticky_ucet,
                    nazev=nazev_polozky,
                    rozpocet=castka
                )
                db.session.add(polozka)
        
        # Uložit všechny změny
        db.session.commit()
        
        # Statistika
        pocet_skupin = UctovaSkupina.query.count()
        pocet_polozek = RozpoctovaPolozka.query.count()
        
        print(f"✓ Databáze inicializována!")
        print(f"✓ Účtových skupin: {pocet_skupin}")
        print(f"✓ Rozpočtových položek: {pocet_polozek}")
        
        # Výpis součtů
        soucet_naklady = db.session.query(db.func.sum(RozpoctovaPolozka.rozpocet)).join(
            UctovaSkupina
        ).filter(UctovaSkupina.typ == 'naklad').scalar() or 0
        
        soucet_vynos = db.session.query(db.func.sum(RozpoctovaPolozka.rozpocet)).join(
            UctovaSkupina
        ).filter(UctovaSkupina.typ == 'vynos').scalar() or 0
        
        print(f"\n📊 Souhrn rozpočtu 2026:")
        print(f"  Celkové náklady: {float(soucet_naklady):,.0f} Kč")
        print(f"  Celkové výnosy:  {float(soucet_vynos):,.0f} Kč")
        print(f"  Bilance:         {float(soucet_vynos - soucet_naklady):,.0f} Kč")

if __name__ == '__main__':
    init_database()
