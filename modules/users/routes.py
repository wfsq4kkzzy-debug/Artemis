"""
Routes pro modul Uživatelé
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from core import db
from .models import User, UserProject, UserConnection, SharedChat, UserMessage, UserNotification
from .executor import UsersExecutor

users_bp = Blueprint('users', __name__, url_prefix='/uzivatele')


@users_bp.route('/')
def index():
    """Seznam uživatelů"""
    users = UsersExecutor.get_all_users()
    users_without_account = UsersExecutor.get_users_without_account()
    
    return render_template(
        'users/index.html',
        users=users,
        users_without_account=users_without_account
    )


@users_bp.route('/novy', methods=['GET', 'POST'])
def novy():
    """Vytvořit nového uživatele z personálního záznamu"""
    if request.method == 'POST':
        result = UsersExecutor.create_user(
            personnel_id=int(request.form.get('personnel_id')),
            username=request.form.get('username'),
            email=request.form.get('email'),
            role=request.form.get('role', 'user'),
            slouzi_nedele=request.form.get('slouzi_nedele') == 'on',
            slouzi_rotujici=request.form.get('slouzi_rotujici') == 'on'
        )
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('users.index'))
        else:
            flash(f"Chyba: {result['error']}", 'danger')
    
    # Získej personální záznamy bez uživatelského účtu
    personnel_without_account = UsersExecutor.get_users_without_account()
    
    return render_template(
        'users/novy.html',
        personnel_without_account=personnel_without_account
    )


@users_bp.route('/<int:user_id>')
def detail(user_id):
    """Detail uživatele"""
    user = UsersExecutor.get_user_by_id(user_id)
    if not user:
        flash("Uživatel neexistuje", 'danger')
        return redirect(url_for('users.index'))
    
    # Projekty uživatele
    user_projects = UsersExecutor.get_user_projects(user_id)
    
    # Sdílené chaty
    shared_chats = UsersExecutor.get_shared_chats_for_user(user_id)
    
    # Zprávy
    messages = UsersExecutor.get_user_messages(user_id, unread_only=False)
    
    # Notifikace
    notifications = UsersExecutor.get_user_notifications(user_id, unread_only=True)
    
    return render_template(
        'users/detail.html',
        user=user,
        user_projects=user_projects,
        shared_chats=shared_chats,
        messages=messages[:10],  # Posledních 10 zpráv
        notifications=notifications
    )


@users_bp.route('/<int:user_id>/projekty')
def user_projects(user_id):
    """Projekty uživatele"""
    user = UsersExecutor.get_user_by_id(user_id)
    if not user:
        flash("Uživatel neexistuje", 'danger')
        return redirect(url_for('users.index'))
    
    user_projects = UsersExecutor.get_user_projects(user_id)
    
    return render_template(
        'users/projekty.html',
        user=user,
        user_projects=user_projects
    )


@users_bp.route('/<int:user_id>/zpravy')
def user_messages(user_id):
    """Zprávy uživatele"""
    user = UsersExecutor.get_user_by_id(user_id)
    if not user:
        flash("Uživatel neexistuje", 'danger')
        return redirect(url_for('users.index'))
    
    messages = UsersExecutor.get_user_messages(user_id)
    
    return render_template(
        'users/zpravy.html',
        user=user,
        messages=messages
    )


@users_bp.route('/<int:user_id>/notifikace')
def user_notifications(user_id):
    """Notifikace uživatele"""
    user = UsersExecutor.get_user_by_id(user_id)
    if not user:
        flash("Uživatel neexistuje", 'danger')
        return redirect(url_for('users.index'))
    
    notifications = UsersExecutor.get_user_notifications(user_id)
    
    return render_template(
        'users/notifikace.html',
        user=user,
        notifications=notifications
    )


@users_bp.route('/<int:user_id>/notifikace/<int:notification_id>/precteno', methods=['POST'])
def mark_notification_read(user_id, notification_id):
    """Označit notifikaci jako přečtenou"""
    result = UsersExecutor.mark_notification_read(notification_id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f"Chyba: {result['error']}", 'danger')
    
    return redirect(url_for('users.user_notifications', user_id=user_id))


@users_bp.route('/<int:user_id>/upravit', methods=['GET', 'POST'])
def upravit(user_id):
    """Úprava uživatele"""
    user = UsersExecutor.get_user_by_id(user_id)
    if not user:
        flash("Uživatel neexistuje", 'danger')
        return redirect(url_for('users.index'))
    
    if request.method == 'POST':
        # Aktualizuj slouzi_nedele a slouzi_rotujici
        user.slouzi_nedele = request.form.get('slouzi_nedele') == 'on'
        user.slouzi_rotujici = request.form.get('slouzi_rotujici') == 'on'
        try:
            db.session.commit()
            flash('Uživatel byl upraven', 'success')
            return redirect(url_for('users.detail', user_id=user_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Chyba: {str(e)}", 'danger')
    
    return render_template('users/upravit.html', user=user)


