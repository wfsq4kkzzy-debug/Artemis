"""
AI Asistent pro správu projektů
- Komunikace přes Claude API
- Správa projektů, rozpočtů, výdajů, termínů
- Paměť konverzací
- Znalostní databáze
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime
from typing import List, Optional, Tuple, Dict
import json
import os
import re
from dotenv import load_dotenv

from core import db
from .models import Employee, AISession, Message, KnowledgeEntry, ServiceRecord, AssistantMemory
from .executor import AIExecutor
from ..projects.executor import ProjectExecutor

# Načti environment variables
load_dotenv()

# Vytvoř blueprint
ai_bp = Blueprint('ai_assistant', __name__, url_prefix='/ai', template_folder='templates', static_folder='static')

# Import AI models
from .models import Employee, AISession, Message, KnowledgeEntry, ServiceRecord, AssistantMemory


# ============================================================================
# AI ASISTENT SERVICE
# ============================================================================

class AIAssistantService:
    """Třída pro komunikaci s Claude API a správu AI asistenta"""
    
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        # Použij podporovaný model - zkus nejnovější, pak starší verze
        # Dostupné modely: claude-sonnet-4-20250514, claude-3-5-sonnet-20241022, claude-3-5-sonnet-20240620
        self.model = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')
        
        if not self.api_key:
            raise Exception("ANTHROPIC_API_KEY není nastaven v .env")
        
        # Inicializuj Anthropic client - bez httpx
        try:
            import anthropic
            # Přímý request bez httpx wrapper
            self.client = anthropic
            self.api_key_value = self.api_key
        except ImportError:
            raise Exception("Anthropic SDK není nainstalován. Spusť: pip install anthropic")
    
    def get_knowledge_base_context(self) -> str:
        """Vrátí celou znalostní databázi jako kontext"""
        entries = KnowledgeEntry.query.filter_by(is_public=True).all()
        
        if not entries:
            return "Znalostní databáze je prázdná."
        
        context = "=== ZNALOSTNÍ DATABÁZE ===\n\n"
        for entry in entries:
            context += f"### {entry.title}\n"
            context += f"Kategorie: {entry.category or 'Není zadána'}\n"
            context += f"Obsah:\n{entry.content}\n"
            if entry.tags:
                context += f"Tags: {entry.tags}\n"
            context += "\n---\n\n"
        
        return context
    
    def get_employee_memory(self, employee_id: int) -> str:
        """Vrátí paměť specifického zaměstnance"""
        memories = AssistantMemory.query.filter_by(employee_id=employee_id).all()
        
        if not memories:
            return ""
        
        memory_text = "=== PAMĚŤ O ZAMĚSTNANCI ===\n\n"
        for memory in memories:
            memory_text += f"**{memory.key}**: {memory.value}\n"
        
        return memory_text
    
    def build_system_prompt(self, employee: Employee, session: AISession, projekt_id: Optional[int] = None) -> str:
        """Vytvoří system prompt s kontextem"""
        
        knowledge_context = self.get_knowledge_base_context()
        employee_memory = self.get_employee_memory(employee.id)
        
        # Informace o projektu pokud existuje
        project_info = ""
        if projekt_id:
            project = ProjectExecutor.get_project_detail(projekt_id)
            if project.get("success"):
                project_info = f"""
=== AKTUÁLNÍ PROJEKT ===
Projekt: {project['nazev']}
Vedoucí: {project['vedouci'] or 'Není přiřazen'}
Status: {project['status']}
Rozpočet: {project['celkovy_rozpocet']} Kč
Vydaje: {project['celkove_vydaje']} Kč
Zbývá: {project['zbytek']} Kč
Termínů: {project['terminy']}
"""
        
        # Aktuální informace o rozpočtu (automaticky načtené)
        budget_info = ""
        try:
            overview = AIExecutor.get_budget_overview_new()
            if overview.get('success'):
                budget = overview['budget']
                budget_info = f"""
=== AKTUÁLNÍ STAV ROZPOČTU ===
Rozpočet: {budget['nazev']} (Rok: {budget['rok']})
Celkový rozpočet: {budget['castka_celkem']:,.2f} Kč
Celkové výdaje: {budget['celkove_vydaje']:,.2f} Kč
Celkové výnosy: {budget['celkove_vynosy']:,.2f} Kč
Bilance: {budget['bilance']:,.2f} Kč
Zbývá: {budget['zbytek']:,.2f} Kč
Čerpání: {budget['procento_vycerpano']:.1f}%

Kategorie:
"""
                for kat in overview.get('kategorie', [])[:5]:  # Prvních 5 kategorií
                    budget_info += f"  - {kat['nazev']} ({kat['typ']}): {kat['vydaje']:,.2f} Kč\n"
                
                # Přidej informace o počtu účtů
                try:
                    ucty = AIExecutor.get_all_budget_items_new()
                    if ucty:
                        budget_info += f"\nPočet účtů v rozpočtu: {len(ucty)}\n"
                        budget_info += "Pro detailní seznam všech účtů použij příkaz: 'Ukaž všechny účty v rozpočtu'\n"
                except:
                    pass
        except Exception as e:
            budget_info = f"\n(Poznámka: Nepodařilo se načíst aktuální stav rozpočtu: {e})\n"
        
        # Informace o aplikaci a jejích funkcích
        app_info = """
=== DOSTUPNÉ FUNKCE V APLIKACI ===

1. HLAVNÍ ROZPOČET (nový systém):
   - Přidat kategorii: "Přidej kategorii 'název' typu 'naklad_mzdovy'/'naklad_ostatni'/'vynos'"
   - Přidat podkategorii: "Přidej podkategorii 'název' do kategorie ID X"
   - Přidat rozpočtovou položku: "Přidej položku 'název' s částkou X Kč do kategorie ID Y"
   - Přidat výdaj: "Přidej výdaj X Kč za 'popis' do kategorie ID Y"
   - Zobrazit přehled: "Ukaž přehled rozpočtu"
   - Stav rozpočtu: "Jaký je stav hlavního rozpočtu?"
   
   DOSTUPNÉ DOTAZY PRO ČTENÍ DAT:
   - "Ukaž všechny účty v rozpočtu" - zobrazí všechny položky rozpočtu (účty)
   - "Ukaž všechny kategorie" - zobrazí všechny kategorie rozpočtu
   - "Ukaž všechny výdaje" - zobrazí všechny výdaje
   - "Ukaž všechny výnosy" - zobrazí všechny výnosy
   - "Ukaž měsíční přehled" - zobrazí měsíční přehled výdajů a výnosů
   - "Jaké jsou účty v rozpočtu?" - zobrazí seznam všech účtů s jejich stavem

2. PROJEKTY:
   - Vytvořit projekt: "Vytvoř projekt s názvem X"
   - Zobrazit projekty: "Ukaž mi všechny projekty"
   - Detail projektu: "Ukaž detail projektu ID X"
   - Nastavit rozpočet projektu: "Nastav rozpočet projektu ID X na Y Kč"
   - Projekty mají vlastní rozpočet a výdaje, které se NEZAPOČÍTAVAJÍ do hlavního rozpočtu

3. VÝDAJE PROJEKTU:
   - Přidat výdaj k projektu: "Přidej výdaj X Kč za 'popis' k projektu ID Y"
   - Výdaje projektů jsou oddělené od hlavního rozpočtu

4. MZDOVÉ NÁKLADY:
   - Přidat mzdu: "Přidej mzdu X Kč pro personální záznam ID Y"
   - Mzdy se automaticky kategorizují podle typu (zaměstnanec/brigádník)

5. TERMÍNY/MILESTONY:
   - Přidat termín: "Přidej termín 'název' na datum DD.MM.YYYY"
   - Zobrazit termíny: "Ukaž všechny termíny"

6. KOMUNIKACE:
   - Přidat zprávu: "Zaznamenej poznámku: ..."
   - Zobrazit zprávy: "Ukaž všechny zprávy"

7. ZNALOSTI:
   - Přidat znalost: "Ulož znalost 'název' s obsahem '...'"
   - Zobrazit znalosti: "Jaké znalosti máme?"

8. SLUŽBY/SMĚNY:
   - MÁŠ PLNÝ PŘÍSTUP KE VŠEM SLUŽBÁM A SMĚNÁM
   - Zobrazit služby: "Ukaž všechny služby", "Ukaž služby", "Jaké jsou služby?", "Rozpis služeb"
   - Zobrazit šablony služeb: "Ukaž šablony služeb"
   - Zobrazit výjimky: "Ukaž výjimky služeb"
   - Zobrazit výměny: "Ukaž výměny služeb"
   - Když uživatel chce informace o službách, automaticky načti data z databáze
   - NIKDY neříkej, že nemáš přístup ke službám - MÁŠ HO!

9. UŽIVATELÉ:
   - Zobrazit uživatele: "Ukaž všechny uživatele", "Kdo jsou uživatelé?"

10. CHANGELOG:
   - Zobrazit změny: "Ukaž changelog", "Jaké byly změny?"

KLÍČOVÉ POKYNY:
- Vždy si ujasni, zda pracujeme s hlavním rozpočtem nebo projektem
- Projekty mají vlastní rozpočet a výdaje - NEPOČÍTAJÍ se do hlavního rozpočtu
- Mzdy se automaticky kategorizují podle personálního záznamu
- Pokaždé, když provádíš akci, potvrď ji s výsledkem
- Komunikuj česky a buď přátelský

DŮLEŽITÉ - PŘÍSTUP K DATŮM:
- MÁŠ PLNÝ PŘÍSTUP KE VŠEM DATŮM V DATABÁZI - VČETNĚ SLUŽEB A SMĚN!
- Můžeš číst: účty (položky rozpočtu), kategorie, výdaje, výnosy, projekty, zaměstnance, SLUŽBY, SMĚNY, uživatele, měsíční přehledy, changelog
- Když uživatel chce informace, automaticky se načtou data z databáze
- Příklady dotazů, které automaticky načtou data:
  * "Ukaž všechny účty v rozpočtu" -> načte všechny položky rozpočtu (účty) s jejich stavem
  * "Jaké jsou účty?" -> načte seznam všech účtů
  * "Ukaž kategorie" -> načte všechny kategorie rozpočtu
  * "Ukaž výdaje" -> načte všechny výdaje
  * "Ukaž výnosy" -> načte všechny výnosy
  * "Ukaž projekty" -> načte všechny projekty
  * "Ukaž služby" / "Rozpis služeb" / "Jaké jsou služby?" -> načte všechny služby ze databáze
  * "Ukaž směny" -> načte všechny služby
  * "Ukaž uživatele" -> načte všechny uživatele
  * "Ukaž měsíční přehled" -> načte měsíční přehled výdajů a výnosů
  * "Ukaž changelog" -> načte všechny záznamy changelogu
- Vždy zobraz uživateli načtená data v přehledné formě
- NIKDY neříkej, že nemáš přístup ke službám - MÁŠ PLNÝ PŘÍSTUP!
"""
        
        prompt = f"""Jsi AI asistent pro správu projektů v Knihovně Polička.

ZÁKLADNÍ INFORMACE:
- Jméno uživatele: {employee.name}
- Role: {employee.role}
- Aktuální čas: {datetime.utcnow().strftime('%d.%m.%Y %H:%M')}

{project_info}

{budget_info}

{app_info}

{knowledge_context}

{employee_memory}

POKYNY:
1. Buď pomocný, profesionální a zdvořilý
2. Máš plný přístup ke všem datům v databázi - včetně služeb, směn, projektů, rozpočtu, uživatelů
3. Můžeš číst všechna data z databáze - když uživatel chce informace, automaticky je načti a zobraz
4. Můžeš provádět všechny akce: vytvářet, upravovat, mazat
5. Vždy potvrď provedené akce s konkrétními výsledky
6. Když si nejsi jistý, zeptej se pro upřesnění
7. Komunikuj česky a přátelsky
8. Pomáhej uživateli spravovat projekty efektivně
9. NIKDY neříkej, že nemáš přístup k datům - MÁŠ PLNÝ PŘÍSTUP KE VŠEMU!
10. Pokud uživatel chce informace o službách/směnách, automaticky načti data pomocí příkazu get_all_services

Kontext relace: {session.context or 'Bez speciálního kontextu'}
"""
        return prompt
    
    def send_message(self, employee_id: int, session_id: int, user_message: str) -> Tuple[str, int]:
        """
        Odešle zprávu Claude a vrátí odpověď
        
        1. Nejdřív se pokusí rozpoznat příkazy z uživatelovy zprávy
        2. Pokud je příkaz, provede jej přes AIExecutor
        3. Pak pošle zprávu asistentovi s výsledky
        
        Returns:
            tuple: (odpověď asistenta, počet tokenů)
        """
        import requests
        
        # Získej zaměstnance a relaci
        employee = Employee.query.get(employee_id)
        session = AISession.query.get(session_id)
        
        if not employee or not session:
            raise ValueError("Zaměstnanec nebo relace nenalezeny")
        
        # Pokus se detekovat a provést příkazy
        execution_results = self._detect_and_execute_commands(user_message, session_id)
        
        # Přidej kontakt s výsledky do zprávy pro AI
        enhanced_message = user_message
        if execution_results:
            enhanced_message += "\n\n[VÝSLEDKY PROVEDENÝCH AKCÍ]\n"
            enhanced_message += json.dumps(execution_results, ensure_ascii=False, indent=2)
        
        # Urči si všechny zprávy v konverzaci
        messages = Message.query.filter_by(session_id=session_id).order_by(Message.created_at).all()
        
        # Přeformátuj pro API
        conversation = []
        for msg in messages:
            conversation.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Přidej novou zprávu s eventuálními výsledky akcí
        conversation.append({
            "role": "user",
            "content": enhanced_message
        })
        
        # Zavolej Claude API
        system_prompt = self.build_system_prompt(employee, session)
        
        headers = {
            "x-api-key": self.api_key_value,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Ověření, že model existuje
        if not self.model:
            raise Exception("Model není nastaven")
        
        data = {
            "model": self.model,
            "max_tokens": 2048,
            "system": system_prompt,
            "messages": conversation
        }
        
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                json=data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Zpracování odpovědi - může být text nebo array
            if isinstance(result.get('content'), list) and len(result['content']) > 0:
                if isinstance(result['content'][0], dict) and 'text' in result['content'][0]:
                    assistant_message = result['content'][0]['text']
                else:
                    assistant_message = str(result['content'][0])
            elif isinstance(result.get('content'), str):
                assistant_message = result['content']
            else:
                assistant_message = str(result.get('content', 'Žádná odpověď'))
            
            tokens_used = result.get('usage', {}).get('input_tokens', 0) + result.get('usage', {}).get('output_tokens', 0)
            
            return assistant_message, tokens_used
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            status_code = "?"
            try:
                if hasattr(e, 'response') and e.response is not None:
                    status_code = e.response.status_code
                    try:
                        error_response = e.response.json()
                        error_msg = error_response.get('error', {})
                        if isinstance(error_msg, dict):
                            error_detail = f" - {error_msg.get('message', str(e))}"
                        else:
                            error_detail = f" - {error_msg}"
                    except:
                        error_detail = f" - {e.response.text[:200]}"
                else:
                    error_detail = f" - {str(e)}"
            except:
                error_detail = f" - {str(e)}"
            
            # Pokud je 404, zkus jiný model
            if status_code == 404:
                raise Exception(f"Model '{self.model}' není dostupný (HTTP 404). Zkus nastavit jiný model v .env jako ANTHROPIC_MODEL=claude-3-5-sonnet-20240620 nebo claude-3-opus-20240229{error_detail}")
            else:
                raise Exception(f"Chyba při komunikaci s Claude API (HTTP {status_code}){error_detail}")
        except Exception as e:
            raise Exception(f"Chyba při komunikaci s Claude API: {str(e)}")
    
    def _detect_and_execute_commands(self, user_message: str, session_id: int) -> Optional[Dict]:
        """
        Detekuje příkazy v uživatelově zprávě a provádí je
        
        Příklady:
        - "Ukaž mi rozpočet" -> seznam položek
        - "Přidej nový výdaj 5000 Kč" -> add_expense
        """
        
        results = []
        keywords_query = ['rozpočet', 'polozka', 'položka', 'seznam', 'ukaž', 'ukaz', 'jaký', 'jaky', 'kolik', 'jak']
        keywords_employees = ['zaměstnanec', 'zamestnanec', 'osoba', 'pracovník', 'pracovnic', 'pracovníka', 'lidé', 'lide']
        keywords_status = ['stav', 'jak je', 'kolik', 'zbývá', 'zbyva', 'bilance', 'vydali', 'spálili', 'spali', 'vydaje']
        keywords_accounts = ['účty', 'ucty', 'účet', 'ucet', 'položky rozpočtu', 'polozky rozpoctu', 'jaké účty', 'jake ucty']
        keywords_categories = ['kategorie', 'kategorii', 'kategorií', 'kategorii rozpočtu']
        keywords_expenses = ['výdaje', 'vydaje', 'výdajů', 'vydaju', 'výdaj', 'vydaj']
        keywords_revenues = ['výnosy', 'vynosy', 'výnosů', 'vynosu', 'výnos', 'vynos']
        keywords_projects = ['projekty', 'projektů', 'projektu', 'projekt']
        keywords_monthly = ['měsíční', 'mesicni', 'měsíc', 'mesic', 'měsíce', 'mesice', 'měsíční přehled', 'mesicni prehled']
        keywords_services = ['služby', 'sluzby', 'služba', 'sluzba', 'služeb', 'sluzeb', 'směny', 'směna', 'smeny', 'smena', 'rozpis služeb', 'rozpis sluzeb', 'kalendář služeb', 'kalendar sluzeb']
        keywords_users = ['uživatelé', 'uzivatele', 'uživatel', 'uzivatel', 'uživatelů', 'uzivatelu']
        keywords_changelog = ['changelog', 'změny', 'zmeny', 'historie změn', 'historie zmen']
        
        lower_msg = user_message.lower()
        
        # Detekce dotazů na čtení dat z databáze (priorita - konkrétní dotazy)
        # Účty v rozpočtu (nejčastější dotaz)
        if any(k in lower_msg for k in keywords_accounts):
            try:
                # Zkontroluj, zda je to dotaz na typ (náklady/výnosy)
                typ = None
                if 'náklad' in lower_msg or 'naklad' in lower_msg:
                    typ = 'naklad'
                elif 'výnos' in lower_msg or 'vynos' in lower_msg:
                    typ = 'vynos'
                
                result = AIExecutor.execute_command('get_all_budget_items_new', {'typ': typ} if typ else {})
                results.append({
                    "action": "get_all_budget_items_new",
                    "data": result.get('result', [])
                })
            except Exception as e:
                print(f"Chyba při čtení účtů: {e}")
                pass
        
        # Kategorie
        elif any(k in lower_msg for k in keywords_categories):
            try:
                result = AIExecutor.execute_command('get_all_budget_categories')
                results.append({
                    "action": "get_all_budget_categories",
                    "data": result.get('result', [])
                })
            except:
                pass
        
        # Výdaje
        elif any(k in lower_msg for k in keywords_expenses):
            try:
                result = AIExecutor.execute_command('get_all_expenses')
                results.append({
                    "action": "get_all_expenses",
                    "data": result.get('result', [])
                })
            except:
                pass
        
        # Výnosy
        elif any(k in lower_msg for k in keywords_revenues):
            try:
                result = AIExecutor.execute_command('get_all_revenues')
                results.append({
                    "action": "get_all_revenues",
                    "data": result.get('result', [])
                })
            except:
                pass
        
        # Projekty
        elif any(k in lower_msg for k in keywords_projects) and 'projekt' in lower_msg:
            try:
                result = AIExecutor.execute_command('get_all_projects')
                results.append({
                    "action": "get_all_projects",
                    "data": result.get('result', [])
                })
            except:
                pass
        
        # Měsíční přehled
        elif any(k in lower_msg for k in keywords_monthly):
            try:
                result = AIExecutor.execute_command('get_monthly_overview')
                results.append({
                    "action": "get_monthly_overview",
                    "data": result.get('result', [])
                })
            except:
                pass
        
        # Detekce stavu rozpočtu (obecný dotaz) - nový systém
        elif any(k in lower_msg for k in keywords_status):
            try:
                # Zkus nový systém
                result = AIExecutor.execute_command('get_budget_overview_new')
                if result.get('success'):
                    results.append({
                        "action": "get_budget_overview_new",
                        "data": result.get('result', {})
                    })
                else:
                    # Fallback na starý systém
                    result = AIExecutor.execute_command('get_budget_status')
                    results.append({
                        "action": "get_budget_status",
                        "data": result.get('result', {})
                    })
                    
                    summary = AIExecutor.execute_command('get_budget_summary')
                    results.append({
                        "action": "get_budget_summary",
                        "data": summary.get('result', {})
                    })
            except:
                pass
        
        # Starý systém - dotazy na rozpočet (kompatibilita)
        elif any(k in lower_msg for k in keywords_query):
            try:
                result = AIExecutor.execute_command('list_budget_items')
                results.append({
                    "action": "list_budget_items",
                    "data": result.get('result', [])[:10]  # Limit na prvních 10
                })
            except:
                pass
        
        # Detekce dotazů na zaměstnance
        elif any(k in lower_msg for k in keywords_employees):
            try:
                result = AIExecutor.execute_command('get_employees')
                results.append({
                    "action": "get_employees",
                    "data": result.get('result', [])
                })
            except:
                pass
        
        # Detekce přidávání výdajů do nového rozpočtu
        elif 'přidej' in lower_msg or 'pridej' in lower_msg:
            try:
                import re
                numbers = re.findall(r'\d+(?:,\d+)?', user_message)
                
                # Nový systém rozpočtu
                if 'kategorii' in lower_msg or 'kategorie' in lower_msg:
                    # Přidání kategorie
                    if 'mzdov' in lower_msg:
                        typ = 'naklad_mzdovy'
                    elif 'ostatn' in lower_msg:
                        typ = 'naklad_ostatni'
                    elif 'výnos' in lower_msg or 'vynos' in lower_msg:
                        typ = 'vynos'
                    else:
                        typ = 'naklad_ostatni'
                    
                    # Extrahuj název kategorie
                    nazev_match = re.search(r'kategorii\s+[\'"]?([^\'"]+)[\'"]?', user_message, re.IGNORECASE)
                    if nazev_match:
                        nazev = nazev_match.group(1).strip()
                        result = AIExecutor.execute_command('add_budget_category', {
                            'typ': typ,
                            'nazev': nazev
                        })
                        results.append({
                            "action": "add_budget_category",
                            "result": result
                        })
                
                # Přidání rozpočtové položky
                elif 'položku' in lower_msg or 'polozku' in lower_msg or 'řádek' in lower_msg or 'radek' in lower_msg:
                    if numbers:
                        castka = float(numbers[0].replace(',', '.'))
                        # Hledej ID kategorie
                        id_match = re.search(r'kategorii\s+(\d+)|kategorie\s+(\d+)', user_message, re.IGNORECASE)
                        category_id = int(id_match.group(1) or id_match.group(2)) if id_match else None
                        
                        # Extrahuj název
                        nazev_match = re.search(r'položku\s+[\'"]?([^\'"]+)[\'"]?', user_message, re.IGNORECASE)
                        nazev = nazev_match.group(1).strip() if nazev_match else 'Nová položka'
                        
                        if category_id and castka:
                            result = AIExecutor.execute_command('add_new_budget_item', {
                                'category_id': category_id,
                                'nazev': nazev,
                                'castka': castka
                            })
                            results.append({
                                "action": "add_new_budget_item",
                                "result": result
                            })
                
                # Přidání výdaje
                elif ('výdaj' in lower_msg or 'vydaj' in lower_msg or 'kč' in lower_msg) and numbers:
                    castka = float(numbers[0].replace(',', '.'))
                    # Hledej ID kategorie
                    id_match = re.search(r'kategorii\s+(\d+)|kategorie\s+(\d+)', user_message, re.IGNORECASE)
                    category_id = int(id_match.group(1) or id_match.group(2)) if id_match else None
                    
                    # Extrahuj popis
                    popis_match = re.search(r'za\s+[\'"]?([^\'"]+)[\'"]?|popis[:\s]+[\'"]?([^\'"]+)[\'"]?', user_message, re.IGNORECASE)
                    popis = (popis_match.group(1) or popis_match.group(2) or 'Výdaj').strip() if popis_match else 'Výdaj'
                    
                    if category_id and castka:
                        result = AIExecutor.execute_command('add_budget_expense', {
                            'category_id': category_id,
                            'popis': popis,
                            'castka': castka
                        })
                        results.append({
                            "action": "add_budget_expense",
                            "result": result
                        })
                
                # Starý systém (kompatibilita)
                elif numbers and ('výdaj' in lower_msg or 'vydaj' in lower_msg or 'kč' in lower_msg):
                    # Pokus se detekovat ID položky a částku
                    castka = None
                    polozka_id = None
                    
                    # Hledej "ID XXX" nebo "položka XXX"
                    id_match = re.search(r'ID\s+(\d+)', user_message, re.IGNORECASE)
                    if id_match:
                        polozka_id = int(id_match.group(1))
                    
                    # Hledej "XXXX Kč" nebo jen první číslo
                    if numbers:
                        castka = float(numbers[0].replace(',', '.'))
                    
                    if castka and polozka_id:
                        result = AIExecutor.execute_command('add_expense', {
                            'polozka_id': polozka_id,
                            'castka': castka,
                            'popis': 'Přidáno AI asistentem'
                        })
                        results.append({
                            "action": "add_expense",
                            "result": result
                        })
            except Exception as e:
                print(f"Chyba při detekci příkazu: {e}")
                pass
        
        return results if results else None
    
    def save_message_pair(self, session_id: int, user_message: str, assistant_message: str, tokens_used: int):
        """Ulož pár zpráv do databáze"""
        
        user_msg = Message(
            session_id=session_id,
            role='user',
            content=user_message
        )
        
        asst_msg = Message(
            session_id=session_id,
            role='assistant',
            content=assistant_message,
            tokens_used=tokens_used
        )
        
        db.session.add(user_msg)
        db.session.add(asst_msg)
        db.session.commit()


# ============================================================================
# ROUTES - AI ASISTENT
# ============================================================================

@ai_bp.route('/')
def index():
    """Hlavní stránka - chat s AI"""
    # Kontrola API klíče
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key or api_key.startswith('sk-ant-your'):
        return render_template('ai/setup.html')
    
    # Získej nebo vytvoř defaultního uživatele
    user = Employee.query.filter_by(email='user@library.local').first()
    if not user:
        user = Employee(name='Ja', email='user@library.local', role='admin', active=True)
        db.session.add(user)
        db.session.commit()
    
    # Získej aktuální session (poslední aktivení)
    session = AISession.query.filter_by(
        employee_id=user.id, 
        is_archived=False
    ).order_by(AISession.updated_at.desc()).first()
    
    if not session:
        session = AISession(
            employee_id=user.id,
            title='Moje konverzace'
        )
        db.session.add(session)
        db.session.commit()
    
    return render_template('ai/index.html', session=session, user=user)


@ai_bp.route('/setup', methods=['POST'])
def setup():
    """Ulož API klíč"""
    data = request.get_json()
    api_key = data.get('api_key', '').strip()
    
    if not api_key:
        return jsonify({'error': 'API klíč nemůže být prázdný'}), 400
    
    if not api_key.startswith('sk-ant-'):
        return jsonify({'error': 'Neplatný formát API klíče. Měl by začínat na sk-ant-'}), 400
    
    # Ulož do .env souboru
    try:
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        
        # Přečti existující obsah
        content = ''
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                content = f.read()
        
        # Nahraď nebo přidej API klíč
        if 'ANTHROPIC_API_KEY=' in content:
            content = re.sub(r'ANTHROPIC_API_KEY=.*', f'ANTHROPIC_API_KEY={api_key}', content)
        else:
            if content and not content.endswith('\n'):
                content += '\n'
            content += f'ANTHROPIC_API_KEY={api_key}\n'
        
        # Ulož zpět
        with open(env_file, 'w') as f:
            f.write(content)
        
        # Aktualizuj v paměti aplikace
        os.environ['ANTHROPIC_API_KEY'] = api_key
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': f'Chyba při ukládání: {str(e)}'}), 500


def send_claude_message(system_prompt: str, user_message: str, conversation_history: list = None) -> Dict:
    """Pošle zprávu do Claude API s možností historie konverzace"""
    import requests
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return {"error": "API klíč není konfigurován"}
    
    # Sestav messages - historie + aktuální zpráva
    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    else:
        messages.append({
            'role': 'user',
            'content': user_message
        })
    
    # Pokud historie neobsahuje aktuální zprávu, přidej ji
    if conversation_history and (not messages or messages[-1].get('content') != user_message):
        messages.append({
            'role': 'user',
            'content': user_message
        })
    
    try:
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            },
            json={
                'model': os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514'),
                'max_tokens': 1024,  # Zkráceno pro úsporu tokenů
                'system': system_prompt,
                'messages': messages
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Zpracování odpovědi - může být text nebo array
            if isinstance(data.get('content'), list) and len(data['content']) > 0:
                if isinstance(data['content'][0], dict) and 'text' in data['content'][0]:
                    assistant_message = data['content'][0]['text']
                else:
                    assistant_message = str(data['content'][0])
            elif isinstance(data.get('content'), str):
                assistant_message = data['content']
            else:
                assistant_message = str(data.get('content', 'Žádná odpověď'))
            return {
                'success': True,
                'content': data.get('content', [{}])[0].get('text', 'Chyba odpovědi'),
                'usage': data.get('usage', {})
            }
        else:
            return {'error': f'API error: {response.status_code} - {response.text}'}
    except Exception as e:
        return {'error': str(e)}


@ai_bp.route('/send-message', methods=['POST'])
def send_message():
    """Odeslání zprávy AI"""
    data = request.get_json()
    message_text = data.get('message', '').strip()
    session_id = data.get('session_id')
    projekt_id = data.get('projekt_id')
    
    if not message_text:
        return jsonify({'error': 'Zpráva je prázdná'}), 400
    
    # Dvě možnosti: project kontext nebo AI session
    if projekt_id:
        # Projekt kontexst - jednoduchý režim pro chat v projektu
        from ..projects.models import Projekt, Zprava
        
        projekt = Projekt.query.get_or_404(projekt_id)
        
        try:
            # Načti historii konverzace z databáze (posledních 10 zpráv pro kontext)
            from ..projects.models import Zprava
            previous_messages = Zprava.query.filter_by(
                projekt_id=projekt_id
            ).order_by(Zprava.datum.desc()).limit(10).all()
            
            # Formátuj historii (od nejstarší po nejnovější)
            history_context = ""
            if previous_messages:
                history_context = "\n=== HISTORIE KONVERZACE (poslední 10) ===\n"
                for msg in reversed(previous_messages):
                    role = "Uživatel" if msg.autor == 'uživatel' else "AI"
                    # Zkrať dlouhé zprávy
                    obsah = msg.obsah[:200] + "..." if len(msg.obsah) > 200 else msg.obsah
                    history_context += f"{role}: {obsah}\n"
            
            # Vytvořit system prompt s project kontextem - STRUČNĚ (NOVÁ LOGIKA)
            budget_info = ProjectExecutor.get_project_budget(projekt_id)
            expenses = ProjectExecutor.get_project_expenses(projekt_id)
            
            # Stručné formátování
            if budget_info.get('success'):
                budget_summary = f"Rozpočet: {budget_info['rozpocet']:.2f} Kč, Vydaje: {budget_info['vydaje']:.2f} Kč, Zbývá: {budget_info['zbytek']:.2f} Kč ({budget_info['procento_vycerpano']:.1f}%)"
            else:
                budget_summary = "Rozpočet: 0 Kč (není nastaven)"
            
            expense_summary = f"{len(expenses)} výdajů" if expenses else "0 výdajů"
            
            # Import AIExecutor pro příkazy
            from .executor import AIExecutor
            
            # STRUČNÝ system prompt pro úsporu tokenů - NOVÁ LOGIKA
            system_prompt = f"""AI asistent pro projekt {projekt.nazev} (ID:{projekt_id}).
Projekt: {projekt.nazev}, Vedoucí: {projekt.vedouci or 'N/A'}, Status: {projekt.status}
{budget_summary}, {expense_summary}

Příkazy:
- set_project_budget(projekt_id={projekt_id}, rozpocet=číslo) - nastavit rozpočet
- get_project_budget(projekt_id={projekt_id}) - zobrazit rozpočet
- add_project_expense(projekt_id={projekt_id}, popis="text", castka=číslo, datum?, cis_faktury?, dodavatel?, poznamka?) - přidat výdaj
- update_project_expense(vydaj_id=číslo, popis?, castka?, datum?, ...) - upravit výdaj
- delete_project_expense(vydaj_id=číslo) - smazat výdaj
- get_project_expenses(projekt_id={projekt_id}) - seznam výdajů

Logika: Projekt má jeden celkový rozpočet. K němu se přidávají výdaje bez kategorií.
{history_context}
Odpovídej stručně česky."""
            
            # Načti historii pro kontext konverzace (posledních 5 párů zpráv)
            conversation_history = []
            if previous_messages:
                # Seskupit zprávy do párů (uživatel + AI) - od nejstarší po nejnovější
                messages_list = list(reversed(previous_messages[-10:]))  # Posledních 10 zpráv
                i = 0
                while i < len(messages_list) - 1:
                    user_msg = messages_list[i]
                    # Najdi následující AI odpověď
                    ai_msg = None
                    for j in range(i + 1, len(messages_list)):
                        if messages_list[j].autor == 'AI Asistent':
                            ai_msg = messages_list[j]
                            break
                    
                    if user_msg.autor == 'uživatel' and ai_msg:
                        conversation_history.append({
                            "role": "user",
                            "content": user_msg.obsah[:300]  # Limit délky pro úsporu tokenů
                        })
                        conversation_history.append({
                            "role": "assistant",
                            "content": ai_msg.obsah[:300]  # Limit délky pro úsporu tokenů
                        })
                        i = j + 1
                    else:
                        i += 1
            
            # Omezit historii na posledních 6 zpráv (3 páry) pro úsporu tokenů
            conversation_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
            
            # Poslat zprávu do Claude API s historií
            response = send_claude_message(
                system_prompt=system_prompt,
                user_message=message_text,
                conversation_history=conversation_history
            )
            
            # Po obdržení odpovědi z Claude, zkus detekovat a provést příkazy
            assistant_response = response.get('content', '')
            execution_results = None
            
            # Detekce příkazů v odpovědi AI nebo v původní zprávě
            from .executor import AIExecutor
            import re
            
            # Inicializuj assistant_response před použitím
            if 'error' in response:
                assistant_response = f"Chyba: {response['error']}"
            else:
                assistant_response = response.get('content', 'Chyba odpovědi')
            
            # Inicializuj response dict pro flagy (pokud ještě neexistuje)
            if 'expense_added' not in response:
                response['expense_added'] = False
            if 'budget_updated' not in response:
                response['budget_updated'] = False
            if 'expense_updated' not in response:
                response['expense_updated'] = False
            if 'expense_deleted' not in response:
                response['expense_deleted'] = False
            
            # Detekce příkazů pro nastavení rozpočtu - NOVÁ LOGIKA
            budget_set_keywords = ['nastav rozpočet', 'nastavit rozpočet', 'set budget', 'rozpočet na', 'rozpočet je']
            is_budget_set_command = any(keyword in message_text.lower() for keyword in budget_set_keywords) and \
                                   any(word in message_text.lower() for word in ['kč', 'korun', 'koruny', 'částka', 'castka'])
            
            if is_budget_set_command:
                # Pokus se extrahovat částku
                castka_match = re.search(r'(\d+(?:\s*\d+)*(?:[.,]\d+)?)\s*kč', message_text, re.IGNORECASE)
                if not castka_match:
                    castka_match = re.search(r'(\d+(?:\s*\d+)*(?:[.,]\d+)?)', message_text)
                
                if castka_match:
                    castka_str = castka_match.group(1).replace(' ', '').replace(',', '.')
                    try:
                        castka = float(castka_str)
                        try:
                            result = AIExecutor.execute_command("set_project_budget", {
                                "projekt_id": projekt_id,
                                "rozpocet": castka
                            })
                            execution_results = {"set_budget": result}
                            
                            if result.get('success') and result.get('result', {}).get('success'):
                                success_msg = f"✅ {result['result'].get('message', 'Rozpočet byl nastaven')}"
                                assistant_response = success_msg + "\n\n" + assistant_response
                                response['budget_updated'] = True
                            elif result.get('success') and not result.get('result', {}).get('success'):
                                error_msg = f"❌ Chyba: {result.get('result', {}).get('error', 'Neznámá chyba')}"
                                assistant_response = error_msg + "\n\n" + assistant_response
                        except Exception as e:
                            assistant_response = f"❌ Chyba při nastavení rozpočtu: {str(e)}\n\n{assistant_response}"
                    except ValueError:
                        pass
            
            # Detekce příkazů pro přidání rozpočtu (zastaralé, ale ponecháno)
            budget_keywords = ['přidej rozpočet', 'přidej do rozpočtu', 'přidat rozpočet', 'add budget']
            is_budget_command = any(keyword in message_text.lower() for keyword in budget_keywords) and \
                              any(word in message_text.lower() for word in ['kč', 'korun', 'koruny', 'částka', 'castka'])
            
            if is_budget_command and not is_budget_set_command:
                # Pokus se extrahovat parametry z uživatelovy zprávy
                # Hledej částku - různé formáty: "5000 Kč", "5 000 Kč", "5000.50 Kč"
                castka_match = re.search(r'(\d+(?:\s*\d+)*(?:[.,]\d+)?)\s*kč', message_text, re.IGNORECASE)
                if not castka_match:
                    castka_match = re.search(r'(\d+(?:\s*\d+)*(?:[.,]\d+)?)', message_text)
                
                # Hledej kategorii
                kategorie_match = re.search(r'(?:kategorii?|kategorie|typ)[:\s]+([^,\n]+)', message_text, re.IGNORECASE)
                
                # Hledej popis - může být před nebo po částce
                popis_match = re.search(r'(?:popis|název|nazev|pro)[:\s]+([^,\n]+)', message_text, re.IGNORECASE)
                
                # Pokud není popis explicitně zadán, zkus ho extrahovat z kontextu
                if not popis_match:
                    # Zkus najít text před částkou
                    if castka_match:
                        before_amount = message_text[:castka_match.start()].strip()
                        after_amount = message_text[castka_match.end():].strip()
                        
                        # Odstraň klíčová slova
                        for keyword in budget_keywords:
                            before_amount = before_amount.replace(keyword, '').strip()
                        before_amount = re.sub(r'(?:přidej|přidat|do|rozpočtu|rozpočet)', '', before_amount, flags=re.IGNORECASE).strip()
                        
                        if before_amount and len(before_amount) > 3:
                            popis_match = type('obj', (object,), {'group': lambda x: before_amount.split(',')[0].split('.')[0].strip()})()
                        elif after_amount and len(after_amount) > 3 and 'kč' not in after_amount.lower():
                            popis_match = type('obj', (object,), {'group': lambda x: after_amount.split(',')[0].split('.')[0].strip()})()
                
                if castka_match:
                    castka_str = castka_match.group(1).replace(' ', '').replace(',', '.')
                    try:
                        castka = float(castka_str)
                        kategorie = kategorie_match.group(1).strip() if kategorie_match else "Ostatní"
                        popis = popis_match.group(1).strip() if popis_match else f"Rozpočtová položka {castka} Kč"
                        
                        try:
                            result = AIExecutor.execute_command("add_project_budget", {
                                "projekt_id": projekt_id,
                                "kategorie": kategorie,
                                "popis": popis,
                                "castka": castka
                            })
                            execution_results = {"add_budget": result}
                            
                            # Pokud bylo úspěšné, uprav odpověď
                            if result.get('success') and result.get('result', {}).get('success'):
                                assistant_response = f"✅ {result['result'].get('message', 'Rozpočtová položka byla přidána')}\n\n{assistant_response}"
                            elif result.get('success') and not result.get('result', {}).get('success'):
                                assistant_response = f"❌ Chyba: {result.get('result', {}).get('error', 'Neznámá chyba')}\n\n{assistant_response}"
                        except Exception as e:
                            assistant_response = f"❌ Chyba při přidávání rozpočtu: {str(e)}\n\n{assistant_response}"
                    except ValueError:
                        pass  # Neplatná částka
            
            # Detekce příkazů pro přidání výdaje - rozšířená detekce
            expense_keywords = ['přidej výdaj', 'přidej výdaje', 'přidat výdaj', 'add expense', 
                              'výdaj', 'vydaj', 'utratil', 'zaplatil', 'zaplaceno', 'zaplatit']
            is_expense_command = any(keyword in message_text.lower() for keyword in expense_keywords) and \
                               any(word in message_text.lower() for word in ['kč', 'korun', 'koruny', 'částka', 'castka'])
            
            # Detekce příkazů pro úpravu výdaje
            expense_edit_keywords = ['uprav výdaj', 'upravit výdaj', 'změň výdaj', 'zmen výdaj', 'edit expense']
            is_expense_edit_command = any(keyword in message_text.lower() for keyword in expense_edit_keywords)
            
            # Detekce příkazů pro smazání výdaje
            expense_delete_keywords = ['smaž výdaj', 'smazat výdaj', 'odstraň výdaj', 'odstran výdaj', 'delete expense']
            is_expense_delete_command = any(keyword in message_text.lower() for keyword in expense_delete_keywords)
            
            if is_expense_command and not is_budget_command and not is_budget_set_command:
                # Hledej částku
                castka_match = re.search(r'(\d+(?:\s*\d+)*(?:[.,]\d+)?)\s*kč', message_text, re.IGNORECASE)
                if not castka_match:
                    castka_match = re.search(r'(\d+(?:\s*\d+)*(?:[.,]\d+)?)', message_text)
                
                # Hledej popis
                popis_match = re.search(r'(?:za|popis|název|nazev|pro|zaplatil|utratil)[:\s]+([^,\n]+)', message_text, re.IGNORECASE)
                
                if not popis_match:
                    # Zkus najít popis z kontextu
                    if castka_match:
                        before_amount = message_text[:castka_match.start()].strip()
                        after_amount = message_text[castka_match.end():].strip()
                        
                        # Odstraň klíčová slova
                        for keyword in expense_keywords:
                            before_amount = before_amount.replace(keyword, '').strip()
                        before_amount = re.sub(r'(?:přidej|přidat|výdaj|vydaj)', '', before_amount, flags=re.IGNORECASE).strip()
                        
                        if before_amount and len(before_amount) > 3:
                            popis_match = type('obj', (object,), {'group': lambda x: before_amount.split(',')[0].split('.')[0].strip()})()
                        elif after_amount and len(after_amount) > 3 and 'kč' not in after_amount.lower():
                            popis_match = type('obj', (object,), {'group': lambda x: after_amount.split(',')[0].split('.')[0].strip()})()
                
                if castka_match:
                    castka_str = castka_match.group(1).replace(' ', '').replace(',', '.')
                    try:
                        castka = float(castka_str)
                        popis = popis_match.group(1).strip() if popis_match else f"Výdaj {castka} Kč"
                        
                        try:
                            result = AIExecutor.execute_command("add_project_expense", {
                                "projekt_id": projekt_id,
                                "popis": popis,
                                "castka": castka
                            })
                            execution_results = {"add_expense": result}
                            
                            # Pokud bylo úspěšné, uprav odpověď
                            if result.get('success') and result.get('result', {}).get('success'):
                                success_msg = f"✅ {result['result'].get('message', 'Výdaj byl přidán')}"
                                if result['result'].get('warning'):
                                    success_msg += f"\n⚠️ {result['result']['warning']}"
                                # Přidej úspěšnou zprávu PŘED odpověď AI (ne duplikuj)
                                assistant_response = success_msg + "\n\n" + assistant_response
                                # Označ, že byl přidán výdaj (pro reload stránky)
                                response['expense_added'] = True
                            elif result.get('success') and not result.get('result', {}).get('success'):
                                error_msg = f"❌ Chyba: {result.get('result', {}).get('error', 'Neznámá chyba')}"
                                assistant_response = error_msg + "\n\n" + assistant_response
                        except Exception as e:
                            assistant_response = f"❌ Chyba při přidávání výdaje: {str(e)}\n\n{assistant_response}"
                    except ValueError:
                        pass  # Neplatná částka
            
            # Detekce příkazů pro úpravu výdaje
            elif is_expense_edit_command:
                # Hledej ID výdaje
                vydaj_id_match = re.search(r'(?:vydaj|vydaje|expense)\s*(?:id|číslo|cislo)?\s*[:\s]*(\d+)', message_text, re.IGNORECASE)
                if not vydaj_id_match:
                    vydaj_id_match = re.search(r'ID\s*(\d+)', message_text, re.IGNORECASE)
                
                if vydaj_id_match:
                    vydaj_id = int(vydaj_id_match.group(1))
                    # Zkus extrahovat parametry pro úpravu
                    update_params = {"vydaj_id": vydaj_id}
                    
                    castka_match = re.search(r'(\d+(?:\s*\d+)*(?:[.,]\d+)?)\s*kč', message_text, re.IGNORECASE)
                    if castka_match:
                        castka_str = castka_match.group(1).replace(' ', '').replace(',', '.')
                        try:
                            update_params["castka"] = float(castka_str)
                        except:
                            pass
                    
                    popis_match = re.search(r'popis[:\s]+([^,\n]+)', message_text, re.IGNORECASE)
                    if popis_match:
                        update_params["popis"] = popis_match.group(1).strip()
                    
                    try:
                        result = AIExecutor.execute_command("update_project_expense", update_params)
                        execution_results = {"update_expense": result}
                        
                        if result.get('success') and result.get('result', {}).get('success'):
                            success_msg = f"✅ {result['result'].get('message', 'Výdaj byl upraven')}"
                            assistant_response = success_msg + "\n\n" + assistant_response
                            response['expense_updated'] = True
                        else:
                            error_msg = f"❌ Chyba: {result.get('result', {}).get('error', 'Neznámá chyba')}"
                            assistant_response = error_msg + "\n\n" + assistant_response
                    except Exception as e:
                        assistant_response = f"❌ Chyba při úpravě výdaje: {str(e)}\n\n{assistant_response}"
            
            # Detekce příkazů pro smazání výdaje
            elif is_expense_delete_command:
                vydaj_id_match = re.search(r'(?:vydaj|vydaje|expense)\s*(?:id|číslo|cislo)?\s*[:\s]*(\d+)', message_text, re.IGNORECASE)
                if not vydaj_id_match:
                    vydaj_id_match = re.search(r'ID\s*(\d+)', message_text, re.IGNORECASE)
                
                if vydaj_id_match:
                    vydaj_id = int(vydaj_id_match.group(1))
                    try:
                        result = AIExecutor.execute_command("delete_project_expense", {"vydaj_id": vydaj_id})
                        execution_results = {"delete_expense": result}
                        
                        if result.get('success') and result.get('result', {}).get('success'):
                            success_msg = f"✅ {result['result'].get('message', 'Výdaj byl smazán')}"
                            assistant_response = success_msg + "\n\n" + assistant_response
                            response['expense_deleted'] = True
                        else:
                            error_msg = f"❌ Chyba: {result.get('result', {}).get('error', 'Neznámá chyba')}"
                            assistant_response = error_msg + "\n\n" + assistant_response
                    except Exception as e:
                        assistant_response = f"❌ Chyba při mazání výdaje: {str(e)}\n\n{assistant_response}"
            
            # Aktualizuj odpověď s výsledky
            response['content'] = assistant_response
            
            # ULOŽIT ZPRÁVY DO DATABÁZE - VŽDY, I PŘI CHYBĚ
            try:
                # Uložit uživatelskou zprávu
                zprava = Zprava(
                    projekt_id=projekt_id,
                    autor='uživatel',
                    obsah=message_text,
                    typ='dotaz',
                    datum=datetime.utcnow()
                )
                db.session.add(zprava)
                
                # Použít aktualizovanou odpověď s výsledky příkazů
                final_response = assistant_response
                
                # Uložit odpověď AI (i když je chyba)
                odpoved = Zprava(
                    projekt_id=projekt_id,
                    autor='AI Asistent',
                    obsah=final_response if 'error' not in response else f"Chyba: {response.get('error', 'Neznámá chyba')}",
                    typ='odpověď',
                    datum=datetime.utcnow()
                )
                db.session.add(odpoved)
                db.session.commit()
            except Exception as save_error:
                # I když se nepodaří uložit, pokračuj
                db.session.rollback()
                print(f"Chyba při ukládání zpráv: {save_error}")
            
            if 'error' in response:
                return jsonify({
                    'error': response['error'],
                    'assistant_message': f"Chyba: {response['error']}",
                    'tokens_used': 0
                }), 500
            
            # Připravit response s informací o změnách
            json_response = {
                'assistant_message': final_response,
                'tokens_used': response.get('usage', {}).get('output_tokens', 0)
            }
            
            # Přidat flagy pro reload stránky
            if response.get('expense_added'):
                json_response['expense_added'] = True
            if response.get('budget_updated'):
                json_response['budget_updated'] = True
            if response.get('expense_updated'):
                json_response['expense_updated'] = True
            if response.get('expense_deleted'):
                json_response['expense_deleted'] = True
            
            return jsonify(json_response)
        except Exception as e:
            # Uložit chybu do databáze
            try:
                zprava = Zprava(
                    projekt_id=projekt_id,
                    autor='uživatel',
                    obsah=message_text,
                    typ='dotaz',
                    datum=datetime.utcnow()
                )
                db.session.add(zprava)
                chyba_zprava = Zprava(
                    projekt_id=projekt_id,
                    autor='AI Asistent',
                    obsah=f"Chyba: {str(e)}",
                    typ='odpověď',
                    datum=datetime.utcnow()
                )
                db.session.add(chyba_zprava)
                db.session.commit()
            except:
                db.session.rollback()
            
            return jsonify({'error': f'Project chat error: {str(e)}'}), 500
    
    elif session_id:
        # Klasická AI session
        session = AISession.query.get_or_404(session_id)
        user = session.employee
        
        try:
            service = AIAssistantService()
            assistant_response, tokens = service.send_message(user.id, session_id, message_text)
            
            # Ulož zprávy
            service.save_message_pair(session_id, message_text, assistant_response, tokens)
            
            return jsonify({
                'assistant_message': assistant_response,
                'tokens_used': tokens
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    else:
        return jsonify({'error': 'Projekt ID nebo Session ID chybí'}), 400


@ai_bp.route('/knowledge-base', methods=['GET', 'POST'])
def knowledge_base():
    """Správa znalostní databáze - pro administraci"""
    
    if request.method == 'POST':
        data = request.get_json()
        
        # Získej aktuálního uživatele
        user = Employee.query.filter_by(email='user@library.local').first()
        if not user:
            return jsonify({'error': 'Uživatel nenalezen'}), 404
        
        entry = KnowledgeEntry(
            title=data.get('title'),
            content=data.get('content'),
            category=data.get('category'),
            tags=data.get('tags'),
            created_by_id=user.id
        )
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({'success': True, 'id': entry.id})
    
    # GET - vrátí všechny záznamy
    entries = KnowledgeEntry.query.filter_by(is_public=True).order_by(KnowledgeEntry.updated_at.desc()).all()
    categories = db.session.query(KnowledgeEntry.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('ai/knowledge_base.html', entries=entries, categories=categories)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@ai_bp.route('/api/session/<int:session_id>/messages', methods=['GET'])
def api_session_messages(session_id: int):
    """Vrátí všechny zprávy ze relace"""
    messages = Message.query.filter_by(session_id=session_id).order_by(Message.created_at).all()
    return jsonify([msg.to_dict() for msg in messages])


@ai_bp.route('/api/knowledge', methods=['GET'])
def api_knowledge():
    """Vrátí všechny znalostní záznamy"""
    entries = KnowledgeEntry.query.filter_by(is_public=True).all()
    return jsonify([e.to_dict() for e in entries])
