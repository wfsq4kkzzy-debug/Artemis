"""
Nové routes pro modul rozpočtu - PŘEPRACOVÁVÁ SE
V této verzi pouze placeholder s informací o vývoji
"""

from flask import Blueprint, render_template

budget_bp = Blueprint('budget', __name__, url_prefix='/rozpocet')


@budget_bp.route('/')
def index():
    """Hlavní stránka modulu rozpočtu - ve vývoji"""
    return render_template('budget/vyvoj.html')


@budget_bp.route('/seznam')
def seznam():
    """Seznam rozpočtů - ve vývoji"""
    return render_template('budget/vyvoj.html', message="Seznam rozpočtů je ve vývoji")
