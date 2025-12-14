"""
Services Executor - Logika pro správu služeb
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from calendar import monthrange
import json

from core import db
from .models import SluzbaTemplate, Sluzba, SluzbaVynimka, SluzbaVymena


class ServicesExecutor:
    """Třída pro správu služeb"""
    
    @staticmethod
    def create_fixni_sluzba(nazev: str, oddeleni: str, den_v_tydnu: int, zamestnanci_data: List[Dict], poznamka: str = None) -> Dict:
        """Vytvoří fixní službu (opakuje se každý týden) s možností více zaměstnanců a různých časů
        
        Args:
            zamestnanci_data: Seznam slovníků s klíči 'zamestnanec_id', 'hodina_od', 'hodina_do'
                Příklad: [{'zamestnanec_id': 1, 'hodina_od': '08:00', 'hodina_do': '12:00'}, ...]
        """
        try:
            # Úterý je zavřeno (den_v_tydnu = 1)
            if den_v_tydnu == 1:
                return {"success": False, "error": "Úterý je zavřeno, nelze vytvořit službu"}
            
            # Ověř oddělení
            if oddeleni not in ['detske', 'dospělé']:
                return {"success": False, "error": "Oddělení musí být 'detske' nebo 'dospělé'"}
            
            if not zamestnanci_data or len(zamestnanci_data) == 0:
                return {"success": False, "error": "Musíte zadat alespoň jednoho zaměstnance"}
            
            # Pro zpětnou kompatibilitu - pokud je jen jeden zaměstnanec, použij první
            prvni_zamestnanec = zamestnanci_data[0]
            default_hodina_od = prvni_zamestnanec.get('hodina_od', '08:00')
            default_hodina_do = prvni_zamestnanec.get('hodina_do', '16:00')
            default_zamestnanec_id = prvni_zamestnanec.get('zamestnanec_id')
            
            # Ulož seznam zaměstnanců jako JSON
            fixni_zamestnanci_json = json.dumps(zamestnanci_data)
            
            template = SluzbaTemplate(
                nazev=nazev,
                typ='fixni',
                oddeleni=oddeleni,
                den_v_tydnu=den_v_tydnu,
                hodina_od=default_hodina_od,  # Pro zpětnou kompatibilitu
                hodina_do=default_hodina_do,  # Pro zpětnou kompatibilitu
                zamestnanec_id=default_zamestnanec_id,  # Pro zpětnou kompatibilitu
                fixni_zamestnanci=fixni_zamestnanci_json,
                poznamka=poznamka
            )
            
            db.session.add(template)
            db.session.commit()
            
            # Vygeneruj služby od dneška rok dopředu
            ServicesExecutor._generate_sluzby_from_template(template.id)
            
            return {
                "success": True,
                "message": f"Fixní služba '{nazev}' byla vytvořena s {len(zamestnanci_data)} zaměstnanci",
                "template_id": template.id
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def create_rotujici_sluzba(prirazeni: Dict[str, int], poznamka: str = None) -> Dict:
        """Vytvoří rotující službu - pátek a sobota jako jedna služba s přiřazením zaměstnanců k termínům
        
        Args:
            prirazeni: Slovník {datum_str: zamestnanec_id} - přiřazení zaměstnanců k termínům
            poznamka: Volitelná poznámka
        """
        try:
            if not prirazeni:
                return {"success": False, "error": "Musíte přiřadit alespoň jednoho zaměstnance k termínu"}
            
            # Zkontroluj, zda všichni zaměstnanci slouží rotující služby
            from modules.users.models import User
            pouziti_zamestnanci = set()
            
            for datum_str, zamestnanec_id in prirazeni.items():
                if zamestnanec_id in pouziti_zamestnanci:
                    return {"success": False, "error": "Každý zaměstnanec může být přiřazen jen k jednomu termínu"}
                
                user = User.query.filter_by(personnel_id=zamestnanec_id, slouzi_rotujici=True, aktivni=True).first()
                if not user:
                    return {"success": False, "error": f"Zaměstnanec ID {zamestnanec_id} nemá zaškrtnuté 'Slouží rotující služby'"}
                
                pouziti_zamestnanci.add(zamestnanec_id)
            
            # Rotující služby jsou pouze pro dospělé oddělení
            oddeleni = 'dospělé'
            
            vytvoreno = 0
            terminy_datumy = []
            
            for datum_str, zamestnanec_id in prirazeni.items():
                try:
                    patek_datum = date.fromisoformat(datum_str)
                except ValueError:
                    continue
                
                # Ověř, že je to pátek
                if patek_datum.weekday() != 4:
                    continue
                
                sobota_datum = patek_datum + timedelta(days=1)
                
                # Zkontroluj, zda už není služba pro pátek
                existing_patek = Sluzba.query.filter_by(
                    datum=patek_datum,
                    oddeleni=oddeleni,
                    typ='rotujici'
                ).first()
                
                if existing_patek:
                    continue  # Přeskoč, pokud už existuje
                
                # Vytvoř službu pro pátek (13:00-16:00)
                sluzba_patek = Sluzba(
                    template_id=None,  # Rotující služby nepotřebují šablonu
                    datum=patek_datum,
                    den_v_tydnu=4,  # Pátek
                    oddeleni=oddeleni,
                    hodina_od='13:00',
                    hodina_do='16:00',
                    zamestnanec_id=zamestnanec_id,
                    typ='rotujici',
                    poznamka=poznamka
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
                    typ='rotujici',
                    poznamka=poznamka
                )
                db.session.add(sluzba_sobota)
                
                terminy_datumy.append(patek_datum)
                vytvoreno += 1
            
            # Rotující služby se ukládají bez šablony (nemají název)
            
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Rotující služba byla vytvořena pro {vytvoreno} termínů (pátek+sobota)",
                "vytvoreno": vytvoreno
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def create_nedelni_sluzba(nazev: str, oddeleni: str, zamestnanci_ids: List[int], poznamka: str = None) -> Dict:
        """Vytvoří nedělní službu (rotující, vždy neděle, fixně 14:00-17:00) - pouze pro dospělé oddělení"""
        try:
            if not zamestnanci_ids or len(zamestnanci_ids) == 0:
                return {"success": False, "error": "Musíte zadat alespoň jednoho zaměstnance"}
            
            # Ověř oddělení - nedělní služby jsou pouze pro dospělé oddělení
            if oddeleni != 'dospělé':
                return {"success": False, "error": "Nedělní služby jsou pouze pro dospělé oddělení"}
            
            template = SluzbaTemplate(
                nazev=nazev,
                typ='nedele',
                oddeleni=oddeleni,
                den_v_tydnu=6,  # Neděle
                hodina_od='14:00',  # Fixně 14:00
                hodina_do='17:00',  # Fixně 17:00
                rotujici_seznam=json.dumps(zamestnanci_ids),
                poznamka=poznamka
            )
            
            db.session.add(template)
            db.session.commit()
            
            # Vygeneruj služby od dneška rok dopředu
            ServicesExecutor._generate_sluzby_from_template(template.id)
            
            return {
                "success": True,
                "message": f"Nedělní služba '{nazev}' byla vytvořena",
                "template_id": template.id
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _generate_sluzby_from_template(template_id: int, start_date: date = None, end_date: date = None):
        """Vygeneruje služby z šablony od start_date do end_date (defaultně od dneška rok dopředu)
        
        POZOR: Pro rotující služby se služby negenerují automaticky - jsou vytvořeny při vytvoření šablony!
        """
        template = SluzbaTemplate.query.get(template_id)
        if not template:
            return
        
        # Rotující služby se negenerují automaticky - jsou vytvořeny při vytvoření šablony
        if template.typ == 'rotujici':
            return
        
        # Pokud není zadáno, použij od dneška rok dopředu
        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = start_date + timedelta(days=365)
        
        current_date = start_date
        rotujici_index = 0
        
        # Pro nedělní služby - spočítej, kolik služeb už bylo vygenerováno před start_date
        # (aby rotace pokračovala správně)
        if template.typ == 'nedele':
            zamestnanci_ids = template.rotujici_seznam_ids
            if zamestnanci_ids:
                # Najdi poslední službu před start_date pro tuto šablonu
                last_sluzba = Sluzba.query.filter(
                    Sluzba.template_id == template_id,
                    Sluzba.datum < start_date
                ).order_by(Sluzba.datum.desc()).first()
                
                if last_sluzba:
                    # Najdi index zaměstnance v seznamu
                    try:
                        last_index = zamestnanci_ids.index(last_sluzba.zamestnanec_id)
                        rotujici_index = (last_index + 1) % len(zamestnanci_ids)
                    except ValueError:
                        rotujici_index = 0
        
        while current_date <= end_date:
            den_v_tydnu = current_date.weekday()  # 0=pondělí, 6=neděle
            
            # Úterý je zavřeno - přeskoč
            if den_v_tydnu == 1:
                current_date += timedelta(days=1)
                continue
            
            # Zkontroluj, zda má šablona službu pro tento den
            if template.den_v_tydnu == den_v_tydnu or (template.typ == 'nedele' and den_v_tydnu == 6):
                # Urči zaměstnance
                zamestnanci_pro_den = []
                
                if template.typ == 'fixni':
                    # Pro fixní službu - použij seznam zaměstnanců z fixni_zamestnanci
                    fixni_zamestnanci = template.fixni_zamestnanci_list
                    if fixni_zamestnanci:
                        zamestnanci_pro_den = fixni_zamestnanci
                    elif template.zamestnanec_id:
                        # Zpětná kompatibilita
                        zamestnanci_pro_den = [{
                            'zamestnanec_id': template.zamestnanec_id,
                            'hodina_od': template.hodina_od,
                            'hodina_do': template.hodina_do
                        }]
                elif template.typ == 'nedele':
                    zamestnanci_ids = template.rotujici_seznam_ids
                    if zamestnanci_ids:
                        zamestnanec_id = zamestnanci_ids[rotujici_index % len(zamestnanci_ids)]
                        rotujici_index += 1
                        zamestnanci_pro_den = [{
                            'zamestnanec_id': zamestnanec_id,
                            'hodina_od': template.hodina_od,
                            'hodina_do': template.hodina_do
                        }]
                
                # Vytvoř službu pro každého zaměstnance
                for zam_data in zamestnanci_pro_den:
                    zamestnanec_id = zam_data.get('zamestnanec_id')
                    hodina_od = zam_data.get('hodina_od', template.hodina_od)
                    hodina_do = zam_data.get('hodina_do', template.hodina_do)
                    
                    if zamestnanec_id:
                        # Zkontroluj, zda už služba neexistuje pro tohoto zaměstnance v tento den
                        existing = Sluzba.query.filter_by(
                            datum=current_date,
                            oddeleni=template.oddeleni,
                            zamestnanec_id=zamestnanec_id,
                            template_id=template_id
                        ).first()
                        
                        if not existing:
                            sluzba = Sluzba(
                                template_id=template_id,
                                datum=current_date,
                                den_v_tydnu=den_v_tydnu,
                                oddeleni=template.oddeleni,
                                hodina_od=hodina_od,
                                hodina_do=hodina_do,
                                zamestnanec_id=zamestnanec_id,
                                typ=template.typ
                            )
                            db.session.add(sluzba)
            
            current_date += timedelta(days=1)
        
        db.session.commit()
    
    @staticmethod
    def _apply_vynimky_to_sluzba(sluzba_dict: Dict) -> Dict:
        """Aplikuje výjimky na službu - pokud existuje aktivní výjimka, použije ji"""
        sluzba_id = sluzba_dict.get('id')
        datum = date.fromisoformat(sluzba_dict['datum'])
        
        # Najdi aktivní výjimku pro tuto službu
        vynimka = SluzbaVynimka.query.filter_by(
            sluzba_id=sluzba_id,
            aktivni=True
        ).first()
        
        if vynimka:
            # Použij data z výjimky
            sluzba_dict['hodina_od'] = vynimka.hodina_od
            sluzba_dict['hodina_do'] = vynimka.hodina_do
            sluzba_dict['zamestnanec_id'] = vynimka.zamestnanec_id
            sluzba_dict['zamestnanec'] = {
                "id": vynimka.zamestnanec.id,
                "jmeno_plne": vynimka.zamestnanec.jmeno_plne
            } if vynimka.zamestnanec else None
            sluzba_dict['je_vynimka'] = True
            sluzba_dict['vynimka_id'] = vynimka.id
            sluzba_dict['vynimka_poznamka'] = vynimka.poznamka
        
        return sluzba_dict
    
    @staticmethod
    def get_sluzby_od_do(start_date: date, end_date: date, filtrovat_oddeleni: List[str] = None, filtrovat_typy: List[str] = None) -> Dict:
        """Vrátí všechny služby od start_date do end_date, seskupené podle měsíců a roků (s aplikovanými výjimkami)"""
        query = Sluzba.query.filter(
            Sluzba.datum >= start_date,
            Sluzba.datum <= end_date
        )
        
        # Filtrování podle oddělení
        if filtrovat_oddeleni:
            query = query.filter(Sluzba.oddeleni.in_(filtrovat_oddeleni))
        
        # Filtrování podle typů
        if filtrovat_typy:
            query = query.filter(Sluzba.typ.in_(filtrovat_typy))
        
        sluzby = query.order_by(Sluzba.datum.asc()).all()
        
        # Seskup podle roků a měsíců a aplikuj výjimky
        # Struktura: {rok: {mesic: [sluzby]}}
        mesice = {}
        for sluzba in sluzby:
            rok = sluzba.datum.year
            mesic = sluzba.datum.month
            key = f"{rok}-{mesic:02d}"  # Klíč ve formátu "2025-01"
            
            if key not in mesice:
                mesice[key] = []
            
            sluzba_dict = {
                "id": sluzba.id,
                "datum": sluzba.datum.isoformat(),
                "den_v_tydnu": sluzba.den_v_tydnu,
                "den_nazev": sluzba.den_nazev,
                "oddeleni": sluzba.oddeleni,
                "hodina_od": sluzba.hodina_od,
                "hodina_do": sluzba.hodina_do,
                "zamestnanec_id": sluzba.zamestnanec_id,
                "zamestnanec": {
                    "id": sluzba.zamestnanec.id,
                    "jmeno_plne": sluzba.zamestnanec.jmeno_plne
                } if sluzba.zamestnanec else None,
                "typ": sluzba.typ,
                "poznamka": sluzba.poznamka,
                "je_vynimka": False,
                "je_vymena": sluzba.je_vymena or False
            }
            
            # Aplikuj výjimky
            sluzba_dict = ServicesExecutor._apply_vynimky_to_sluzba(sluzba_dict)
            
            mesice[key].append(sluzba_dict)
        
        return mesice
    
    @staticmethod
    def get_sluzby_pro_rok(rok: int = 2026, filtrovat_oddeleni: List[str] = None, filtrovat_typy: List[str] = None) -> Dict:
        """Vrátí všechny služby pro daný rok, seskupené podle měsíců (s aplikovanými výjimkami)"""
        start_date = date(rok, 1, 1)
        end_date = date(rok, 12, 31)
        
        query = Sluzba.query.filter(
            Sluzba.datum >= start_date,
            Sluzba.datum <= end_date
        )
        
        # Filtrování podle oddělení
        if filtrovat_oddeleni:
            query = query.filter(Sluzba.oddeleni.in_(filtrovat_oddeleni))
        
        # Filtrování podle typů
        if filtrovat_typy:
            query = query.filter(Sluzba.typ.in_(filtrovat_typy))
        
        sluzby = query.order_by(Sluzba.datum.asc()).all()
        
        # Seskup podle měsíců a aplikuj výjimky
        mesice = {}
        for sluzba in sluzby:
            mesic = sluzba.datum.month
            if mesic not in mesice:
                mesice[mesic] = []
            
            sluzba_dict = {
                "id": sluzba.id,
                "datum": sluzba.datum.isoformat(),
                "den_v_tydnu": sluzba.den_v_tydnu,
                "den_nazev": sluzba.den_nazev,
                "oddeleni": sluzba.oddeleni,
                "hodina_od": sluzba.hodina_od,
                "hodina_do": sluzba.hodina_do,
                "zamestnanec_id": sluzba.zamestnanec_id,
                "zamestnanec": {
                    "id": sluzba.zamestnanec.id,
                    "jmeno_plne": sluzba.zamestnanec.jmeno_plne
                } if sluzba.zamestnanec else None,
                "typ": sluzba.typ,
                "poznamka": sluzba.poznamka,
                "je_vynimka": False,
                "je_vymena": sluzba.je_vymena or False
            }
            
            # Aplikuj výjimky
            sluzba_dict = ServicesExecutor._apply_vynimky_to_sluzba(sluzba_dict)
            
            mesice[mesic].append(sluzba_dict)
        
        return mesice
    
    @staticmethod
    def get_sluzby_pro_mesic(rok: int, mesic: int) -> List[Dict]:
        """Vrátí služby pro konkrétní měsíc"""
        start_date = date(rok, mesic, 1)
        days_in_month = monthrange(rok, mesic)[1]
        end_date = date(rok, mesic, days_in_month)
        
        sluzby = Sluzba.query.filter(
            Sluzba.datum >= start_date,
            Sluzba.datum <= end_date
        ).order_by(Sluzba.datum.asc()).all()
        
        return [
            {
                "id": s.id,
                "datum": s.datum.isoformat(),
                "den_v_tydnu": s.den_v_tydnu,
                "den_nazev": s.den_nazev,
                "oddeleni": s.oddeleni,
                "hodina_od": s.hodina_od,
                "hodina_do": s.hodina_do,
                "zamestnanec": {
                    "id": s.zamestnanec.id,
                    "jmeno_plne": s.zamestnanec.jmeno_plne
                } if s.zamestnanec else None,
                "typ": s.typ,
                "poznamka": s.poznamka
            }
            for s in sluzby
        ]
    
    @staticmethod
    def get_all_templates() -> List[Dict]:
        """Vrátí všechny šablony služeb"""
        templates = SluzbaTemplate.query.filter_by(aktivni=True).order_by(SluzbaTemplate.nazev).all()
        
        return [
            {
                "id": t.id,
                "nazev": t.nazev,
                "typ": t.typ,
                "oddeleni": t.oddeleni,
                "den_v_tydnu": t.den_v_tydnu,
                "hodina_od": t.hodina_od,
                "hodina_do": t.hodina_do,
                "zamestnanec": {
                    "id": t.zamestnanec.id,
                    "jmeno_plne": t.zamestnanec.jmeno_plne
                } if t.zamestnanec else None,
                "rotujici_seznam_ids": t.rotujici_seznam_ids,
                "poznamka": t.poznamka
            }
            for t in templates
        ]
    
    @staticmethod
    def delete_template(template_id: int) -> Dict:
        """Smaže šablonu služby a všechny související služby"""
        try:
            template = SluzbaTemplate.query.get(template_id)
            if not template:
                return {"success": False, "error": "Šablona neexistuje"}
            
            # Smaž všechny služby z této šablony
            Sluzba.query.filter_by(template_id=template_id).delete()
            
            # Smaž šablonu
            db.session.delete(template)
            db.session.commit()
            
            return {"success": True, "message": f"Šablona '{template.nazev}' byla smazána"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def update_sluzba(sluzba_id: int, zamestnanec_id: int = None, poznamka: str = None) -> Dict:
        """Upraví konkrétní službu (např. změna zaměstnance)"""
        try:
            sluzba = Sluzba.query.get(sluzba_id)
            if not sluzba:
                return {"success": False, "error": "Služba neexistuje"}
            
            if zamestnanec_id is not None:
                sluzba.zamestnanec_id = zamestnanec_id
            if poznamka is not None:
                sluzba.poznamka = poznamka
            
            db.session.commit()
            return {"success": True, "message": "Služba byla upravena"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def create_vynimka(sluzba_id: int, datum: date, oddeleni: str, hodina_od: str, hodina_do: str, 
                       zamestnanec_id: int, poznamka: str = None, vytvoril_user_id: int = None) -> Dict:
        """Vytvoří výjimku v službě"""
        try:
            sluzba = Sluzba.query.get(sluzba_id)
            if not sluzba:
                return {"success": False, "error": "Služba neexistuje"}
            
            # Deaktivuj staré výjimky pro tuto službu
            SluzbaVynimka.query.filter_by(sluzba_id=sluzba_id, aktivni=True).update({"aktivni": False})
            
            # Vytvoř novou výjimku
            vynimka = SluzbaVynimka(
                sluzba_id=sluzba_id,
                datum=datum,
                oddeleni=oddeleni,
                hodina_od=hodina_od,
                hodina_do=hodina_do,
                zamestnanec_id=zamestnanec_id,
                poznamka=poznamka,
                vytvoril_user_id=vytvoril_user_id
            )
            
            db.session.add(vynimka)
            sluzba.je_vynimka = True
            db.session.commit()
            
            return {"success": True, "message": "Výjimka byla vytvořena", "vynimka_id": vynimka.id}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def delete_vynimka(vynimka_id: int) -> Dict:
        """Smaže výjimku"""
        try:
            vynimka = SluzbaVynimka.query.get(vynimka_id)
            if not vynimka:
                return {"success": False, "error": "Výjimka neexistuje"}
            
            vynimka.aktivni = False
            sluzba = Sluzba.query.get(vynimka.sluzba_id)
            if sluzba:
                # Zkontroluj, zda nejsou další aktivní výjimky
                if not SluzbaVynimka.query.filter_by(sluzba_id=sluzba.id, aktivni=True).first():
                    sluzba.je_vynimka = False
            
            db.session.commit()
            return {"success": True, "message": "Výjimka byla smazána"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def create_vymena(sluzba1_id: int, sluzba2_id: int, poznamka: str = None, vytvoril_user_id: int = None) -> Dict:
        """Vytvoří výměnu služeb mezi dvěma zaměstnanci"""
        try:
            sluzba1 = Sluzba.query.get(sluzba1_id)
            sluzba2 = Sluzba.query.get(sluzba2_id)
            
            if not sluzba1 or not sluzba2:
                return {"success": False, "error": "Jedna nebo obě služby neexistují"}
            
            if sluzba1_id == sluzba2_id:
                return {"success": False, "error": "Nelze vyměnit službu sama se sebou"}
            
            # Vytvoř výměnu
            vymena = SluzbaVymena(
                sluzba1_id=sluzba1_id,
                sluzba2_id=sluzba2_id,
                zamestnanec1_id=sluzba1.zamestnanec_id,
                zamestnanec2_id=sluzba2.zamestnanec_id,
                poznamka=poznamka,
                vytvoril_user_id=vytvoril_user_id,
                schvaleno=False
            )
            
            db.session.add(vymena)
            db.session.commit()
            
            return {"success": True, "message": "Výměna byla vytvořena (čeká na schválení)", "vymena_id": vymena.id}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def schvalit_vymenu(vymena_id: int) -> Dict:
        """Schválí výměnu a prohodí zaměstnance ve službách"""
        try:
            vymena = SluzbaVymena.query.get(vymena_id)
            if not vymena:
                return {"success": False, "error": "Výměna neexistuje"}
            
            if vymena.schvaleno:
                return {"success": False, "error": "Výměna již byla schválena"}
            
            sluzba1 = Sluzba.query.get(vymena.sluzba1_id)
            sluzba2 = Sluzba.query.get(vymena.sluzba2_id)
            
            if not sluzba1 or not sluzba2:
                return {"success": False, "error": "Jedna nebo obě služby neexistují"}
            
            # Prohoď zaměstnance
            temp = sluzba1.zamestnanec_id
            sluzba1.zamestnanec_id = sluzba2.zamestnanec_id
            sluzba2.zamestnanec_id = temp
            
            sluzba1.je_vymena = True
            sluzba2.je_vymena = True
            
            vymena.schvaleno = True
            db.session.commit()
            
            return {"success": True, "message": "Výměna byla schválena a provedena"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_statistiky_zamestnance(zamestnanec_id: int, rok: int = 2026) -> Dict:
        """Vrátí statistiky služeb pro zaměstnance (počet hodin za týden/měsíc/rok)"""
        start_date = date(rok, 1, 1)
        end_date = date(rok, 12, 31)
        
        # Získej všechny služby zaměstnance (včetně výjimek)
        sluzby = Sluzba.query.filter(
            Sluzba.datum >= start_date,
            Sluzba.datum <= end_date,
            Sluzba.zamestnanec_id == zamestnanec_id
        ).all()
        
        # Získej výjimky, kde je zaměstnanec náhradník
        vynimky = SluzbaVynimka.query.filter(
            SluzbaVynimka.datum >= start_date,
            SluzbaVynimka.datum <= end_date,
            SluzbaVynimka.zamestnanec_id == zamestnanec_id,
            SluzbaVynimka.aktivni == True
        ).all()
        
        def pocet_hodin(hodina_od: str, hodina_do: str) -> float:
            """Vypočítá počet hodin mezi dvěma časy"""
            try:
                from datetime import datetime
                od = datetime.strptime(hodina_od, '%H:%M')
                do = datetime.strptime(hodina_do, '%H:%M')
                diff = do - od
                return diff.total_seconds() / 3600.0
            except:
                return 0.0
        
        # Statistiky podle typu
        statistiky = {
            'fixni': {'tyden': 0, 'mesic': 0, 'rok': 0, 'pocet': 0},
            'rotujici': {'tyden': 0, 'mesic': 0, 'rok': 0, 'pocet': 0},
            'nedele': {'tyden': 0, 'mesic': 0, 'rok': 0, 'pocet': 0},
            'celkem': {'tyden': 0, 'mesic': 0, 'rok': 0, 'pocet': 0}
        }
        
        # Aktuální týden a měsíc
        today = date.today()
        if today.year != rok:
            today = date(rok, 1, 1)
        
        # Začátek aktuálního týdne (pondělí)
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)
        
        # Aktuální měsíc
        month_start = date(today.year, today.month, 1)
        days_in_month = monthrange(today.year, today.month)[1]
        month_end = date(today.year, today.month, days_in_month)
        
        # Zpracuj služby
        for sluzba in sluzby:
            # Zkontroluj, zda není výjimka
            vynimka = SluzbaVynimka.query.filter_by(sluzba_id=sluzba.id, aktivni=True).first()
            if vynimka:
                # Pokud je výjimka, použij data z výjimky
                hodiny = pocet_hodin(vynimka.hodina_od, vynimka.hodina_do)
            else:
                hodiny = pocet_hodin(sluzba.hodina_od, sluzba.hodina_do)
            
            typ = sluzba.typ
            if typ not in statistiky:
                typ = 'celkem'
            
            statistiky[typ]['rok'] += hodiny
            statistiky[typ]['pocet'] += 1
            statistiky['celkem']['rok'] += hodiny
            statistiky['celkem']['pocet'] += 1
            
            # Týden
            if week_start <= sluzba.datum <= week_end:
                statistiky[typ]['tyden'] += hodiny
                statistiky['celkem']['tyden'] += hodiny
            
            # Měsíc
            if month_start <= sluzba.datum <= month_end:
                statistiky[typ]['mesic'] += hodiny
                statistiky['celkem']['mesic'] += hodiny
        
        # Zpracuj výjimky (kde je zaměstnanec náhradník)
        for vynimka in vynimky:
            hodiny = pocet_hodin(vynimka.hodina_od, vynimka.hodina_do)
            
            # Zjisti typ služby
            sluzba = Sluzba.query.get(vynimka.sluzba_id)
            if sluzba:
                typ = sluzba.typ
                if typ not in statistiky:
                    typ = 'celkem'
                
                statistiky[typ]['rok'] += hodiny
                statistiky[typ]['pocet'] += 1
                statistiky['celkem']['rok'] += hodiny
                statistiky['celkem']['pocet'] += 1
                
                # Týden
                if week_start <= vynimka.datum <= week_end:
                    statistiky[typ]['tyden'] += hodiny
                    statistiky['celkem']['tyden'] += hodiny
                
                # Měsíc
                if month_start <= vynimka.datum <= month_end:
                    statistiky[typ]['mesic'] += hodiny
                    statistiky['celkem']['mesic'] += hodiny
        
        return statistiky
    
    @staticmethod
    def get_sluzby_pro_zamestnance(zamestnanec_id: int, rok: int = 2026) -> List[Dict]:
        """Vrátí všechny služby zaměstnance (včetně výjimek)"""
        start_date = date(rok, 1, 1)
        end_date = date(rok, 12, 31)
        
        # Získej služby, kde je zaměstnanec přiřazen
        sluzby = Sluzba.query.filter(
            Sluzba.datum >= start_date,
            Sluzba.datum <= end_date,
            Sluzba.zamestnanec_id == zamestnanec_id
        ).order_by(Sluzba.datum.asc()).all()
        
        # Získej výjimky, kde je zaměstnanec náhradník
        vynimky = SluzbaVynimka.query.filter(
            SluzbaVynimka.datum >= start_date,
            SluzbaVynimka.datum <= end_date,
            SluzbaVynimka.zamestnanec_id == zamestnanec_id,
            SluzbaVynimka.aktivni == True
        ).order_by(SluzbaVynimka.datum.asc()).all()
        
        result = []
        
        # Přidej služby
        for sluzba in sluzby:
            # Zkontroluj, zda není výjimka
            vynimka = SluzbaVynimka.query.filter_by(sluzba_id=sluzba.id, aktivni=True).first()
            
            if not vynimka:  # Pouze pokud není výjimka (výjimky přidáme zvlášť)
                result.append({
                    "id": sluzba.id,
                    "datum": sluzba.datum.isoformat(),
                    "den_nazev": sluzba.den_nazev,
                    "oddeleni": sluzba.oddeleni,
                    "hodina_od": sluzba.hodina_od,
                    "hodina_do": sluzba.hodina_do,
                    "typ": sluzba.typ,
                    "je_vynimka": False,
                    "je_vymena": sluzba.je_vymena or False
                })
        
        # Přidej výjimky
        for vynimka in vynimky:
            sluzba = Sluzba.query.get(vynimka.sluzba_id)
            # Získej název dne v týdnu
            den_nazev = ''
            if vynimka.datum:
                dny = ['Pondělí', 'Úterý', 'Středa', 'Čtvrtek', 'Pátek', 'Sobota', 'Neděle']
                den_nazev = dny[vynimka.datum.weekday()] if 0 <= vynimka.datum.weekday() < 7 else ''
            
            result.append({
                "id": vynimka.sluzba_id,
                "datum": vynimka.datum.isoformat() if vynimka.datum else '',
                "den_nazev": den_nazev,
                "oddeleni": vynimka.oddeleni,
                "hodina_od": vynimka.hodina_od,
                "hodina_do": vynimka.hodina_do,
                "typ": sluzba.typ if sluzba else 'neznámý',
                "je_vynimka": True,
                "vynimka_id": vynimka.id,
                "poznamka": vynimka.poznamka
            })
        
        # Seřaď podle data
        result.sort(key=lambda x: x['datum'])
        
        return result
