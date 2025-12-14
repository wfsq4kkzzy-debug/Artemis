"""
Budget Module - Modul pro správu rozpočtu
PŘEPRACOVÁVÁ SE - nová flexibilní struktura
"""

# Nové modely
from .models import Budget, BudgetCategory, BudgetSubCategory, BudgetItem, Expense

# Zastaralé modely (pro kompatibilitu)
from .models import UctovaSkupina, RozpoctovaPolozka, Vydaj

# Routes
from .routes import budget_bp

__all__ = [
    # Nové modely
    'Budget', 'BudgetCategory', 'BudgetSubCategory', 'BudgetItem', 'Expense',
    # Zastaralé modely (pro kompatibilitu)
    'UctovaSkupina', 'RozpoctovaPolozka', 'Vydaj',
    # Blueprint
    'budget_bp'
]




