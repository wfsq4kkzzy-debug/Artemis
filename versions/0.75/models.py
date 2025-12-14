"""
Centralizované modely - pro zpětnou kompatibilitu
Všechny modely jsou nyní v modules/*/models.py
Tento soubor importuje všechny modely pro kompatibilitu se starým kódem
"""

from core import db

# Import všech modelů z modulů
from modules.budget.models import UctovaSkupina, RozpoctovaPolozka, Vydaj
from modules.projects.models import Projekt, BudgetProjektu, VydajProjektu, Termin, Zprava, Znalost
from modules.personnel.models import ZamestnanecAOON
from modules.ai.models import Employee, AISession, Message, KnowledgeEntry, ServiceRecord, AssistantMemory

# Export pro zpětnou kompatibilitu
__all__ = [
    'db',
    # Budget
    'UctovaSkupina', 'RozpoctovaPolozka', 'Vydaj',
    # Projects
    'Projekt', 'BudgetProjektu', 'VydajProjektu', 'Termin', 'Zprava', 'Znalost',
    # Personnel
    'ZamestnanecAOON',
    # AI
    'Employee', 'AISession', 'Message', 'KnowledgeEntry', 'ServiceRecord', 'AssistantMemory'
]
