#!/usr/bin/env python
"""
Inicializace AI Asistenta - vytvoření testovacích dat
"""

from app import app, db
from ai_assistant import Employee, KnowledgeEntry

def init_ai_assistant():
    """Vytvoří testovací data pro AI asistenta"""
    
    with app.app_context():
        print("Inicializuji AI asistenta...")
        
        # Nejdřív vytvoř všechny tabulky
        db.create_all()
        
        # Vytvoř testovací zaměstnance
        if Employee.query.count() == 0:
            employees = [
                Employee(name='Jana Nováková', email='jana@knihovna.cz', role='librarian'),
                Employee(name='Petr Svoboda', email='petr@knihovna.cz', role='librarian'),
                Employee(name='Monika Richtrová', email='monika@knihovna.cz', role='manager'),
            ]
            
            for emp in employees:
                db.session.add(emp)
            db.session.commit()
            print(f"✓ Vytvořeno {len(employees)} zaměstnanců")
        
        # Vytvoř testovací znalostní záznamy
        if KnowledgeEntry.query.count() == 0:
            emp = Employee.query.first()
            
            knowledge_entries = [
                KnowledgeEntry(
                    title='Procedura katalogizace',
                    content='Při katalogizaci nové knihy postupuj takto:\n1. Přijmi knihu\n2. Vytvoř záznam v systému\n3. Přidělej ISBN\n4. Zařaď do kategorie\n5. Ulož do skladu',
                    category='Procedury',
                    tags='katalog, kniha, procedura',
                    created_by_id=emp.id,
                    is_public=True
                ),
                KnowledgeEntry(
                    title='Kontakty oddělení',
                    content='Oddělení získávání: Jana Dvořáková (301 555 666)\nOddělení katalogu: Petr Málek (301 555 667)\nAdministrace: Hana Čepelová (301 555 668)',
                    category='Kontakty',
                    tags='kontakt, telefonní číslo, oddělení',
                    created_by_id=emp.id,
                    is_public=True
                ),
                KnowledgeEntry(
                    title='Obecně závazná vyhláška číslo 5/2023',
                    content='Vyhláška město Polička o poskytování služeb v městské knihovně:\n- Otevírací doba: Po-Pá 9-18, So 9-12\n- Členství zdarma pro občany Polički\n- Poplatek za pozdní vrácení: 10 Kč za den\n- Limit výpůjček: 50 položek',
                    category='Právní předpisy',
                    tags='vyhláška, smlouva, pravidla',
                    created_by_id=emp.id,
                    is_public=True
                ),
            ]
            
            for entry in knowledge_entries:
                db.session.add(entry)
            db.session.commit()
            print(f"✓ Vytvořeno {len(knowledge_entries)} záznamů v databázi")
        
        print("✓ Inicializace AI asistenta dokončena!")
        print("\nMůžeš teď přejít na http://localhost:5000/ai/")

if __name__ == '__main__':
    init_ai_assistant()
