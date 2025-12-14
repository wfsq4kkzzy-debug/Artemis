"""
Personnel Module - Modul pro personální agendu
"""

from .models import ZamestnanecAOON
from .routes import personnel_bp

__all__ = ['ZamestnanecAOON', 'personnel_bp']
