"""
Centralizované modely - pro zpětnou kompatibilitu
Všechny modely jsou nyní v modules/*/models.py
Tento soubor importuje všechny modely pro kompatibilitu se starým kódem
"""

from core import db

# Import všech modelů z modulů
from modules.budget.models import UctovaSkupina, RozpoctovaPolozka, Vydaj, Budget, BudgetCategory, BudgetItem, Expense
from modules.projects.models import Projekt, BudgetProjektu, VydajProjektu, Termin, Zprava, Znalost
from modules.personnel.models import ZamestnanecAOON
from modules.ai.models import Employee, AISession, Message, KnowledgeEntry, ServiceRecord, AssistantMemory
from modules.users.models import User, UserProject, UserConnection, SharedChat, UserMessage, UserNotification

# Export pro zpětnou kompatibilitu
__all__ = [
    'db',
    # Budget
    'UctovaSkupina', 'RozpoctovaPolozka', 'Vydaj', 'Budget', 'BudgetCategory', 'BudgetItem', 'Expense',
    # Projects
    'Projekt', 'BudgetProjektu', 'VydajProjektu', 'Termin', 'Zprava', 'Znalost',
    # Personnel
    'ZamestnanecAOON',
    # AI
    'Employee', 'AISession', 'Message', 'KnowledgeEntry', 'ServiceRecord', 'AssistantMemory',
    # Users
    'User', 'UserProject', 'UserConnection', 'SharedChat', 'UserMessage', 'UserNotification'
]
