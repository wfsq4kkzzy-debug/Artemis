"""
Users Executor - Business logika pro modul uživatelů
"""

from datetime import datetime
from typing import Dict, List, Optional
from core import db
from .models import User, UserProject, UserConnection, SharedChat, UserMessage, UserNotification


class UsersExecutor:
    """Třída pro správu uživatelů"""
    
    # ========================================================================
    # UŽIVATELÉ
    # ========================================================================
    
    @staticmethod
    def create_user(personnel_id: int, username: str, email: str, role: str = 'user', **kwargs) -> Dict:
        """Vytvoří nového uživatele z personálního záznamu"""
        try:
            # Zkontroluj, zda personální záznam existuje
            from ..personnel.models import ZamestnanecAOON
            personnel = ZamestnanecAOON.query.get(personnel_id)
            if not personnel:
                return {"success": False, "error": f"Personální záznam ID {personnel_id} neexistuje"}
            
            # Zkontroluj, zda uživatel s tímto personnel_id už neexistuje
            existing = User.query.filter_by(personnel_id=personnel_id).first()
            if existing:
                return {"success": False, "error": f"Uživatel pro personální záznam ID {personnel_id} již existuje"}
            
            # Zkontroluj, zda username nebo email už neexistují
            if User.query.filter_by(username=username).first():
                return {"success": False, "error": f"Uživatelské jméno '{username}' již existuje"}
            if email and User.query.filter_by(email=email).first():
                return {"success": False, "error": f"Email '{email}' již existuje"}
            
            # Vytvoř uživatele
            user = User(
                personnel_id=personnel_id,
                username=username,
                email=email,
                role=role,
                slouzi_nedele=kwargs.get('slouzi_nedele', False),
                slouzi_rotujici=kwargs.get('slouzi_rotujici', False),
                workspace_settings=kwargs.get('workspace_settings')
            )
            
            db.session.add(user)
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Uživatel '{username}' byl vytvořen",
                "user_id": user.id
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Vrátí uživatele podle ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Vrátí uživatele podle username"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def get_all_users(aktivni_only: bool = True) -> List[User]:
        """Vrátí všechny uživatele"""
        query = User.query
        if aktivni_only:
            query = query.filter_by(aktivni=True)
        return query.order_by(User.username).all()
    
    @staticmethod
    def get_users_without_account() -> List:
        """Vrátí personální záznamy, které ještě nemají uživatelský účet"""
        from ..personnel.models import ZamestnanecAOON
        
        # Všechny personální záznamy
        all_personnel = ZamestnanecAOON.query.filter_by(aktivni=True).all()
        
        # Uživatelé s personálním ID
        users_with_personnel = {u.personnel_id for u in User.query.all()}
        
        # Vrátit personální záznamy bez uživatelského účtu
        return [p for p in all_personnel if p.id not in users_with_personnel]
    
    # ========================================================================
    # UŽIVATELÉ V PROJEKTECH
    # ========================================================================
    
    @staticmethod
    def add_user_to_project(user_id: int, projekt_id: int, role: str = 'member') -> Dict:
        """Přidá uživatele do projektu"""
        try:
            # Zkontroluj, zda už není v projektu
            existing = UserProject.query.filter_by(user_id=user_id, projekt_id=projekt_id).first()
            if existing:
                existing.aktivni = True
                existing.role = role
                db.session.commit()
                return {
                    "success": True,
                    "message": f"Uživatel byl aktualizován v projektu",
                    "user_project_id": existing.id
                }
            
            user_project = UserProject(
                user_id=user_id,
                projekt_id=projekt_id,
                role=role
            )
            
            db.session.add(user_project)
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Uživatel byl přidán do projektu",
                "user_project_id": user_project.id
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_project_users(projekt_id: int, aktivni_only: bool = True) -> List[User]:
        """Vrátí všechny uživatele v projektu"""
        query = UserProject.query.filter_by(projekt_id=projekt_id)
        if aktivni_only:
            query = query.filter_by(aktivni=True)
        
        user_projects = query.all()
        return [up.user for up in user_projects]
    
    @staticmethod
    def get_user_projects(user_id: int, aktivni_only: bool = True) -> List:
        """Vrátí všechny projekty uživatele"""
        from ..projects.models import Projekt
        
        query = UserProject.query.filter_by(user_id=user_id)
        if aktivni_only:
            query = query.filter_by(aktivni=True)
        
        user_projects = query.all()
        return [
            {
                'projekt': up.projekt,
                'role': up.role,
                'datum_pridani': up.datum_pridani
            }
            for up in user_projects
        ]
    
    # ========================================================================
    # SDÍLENÍ CHATŮ
    # ========================================================================
    
    @staticmethod
    def share_chat(ai_session_id: int, shared_by_user_id: int, shared_with_user_id: int = None, poznamka: str = None) -> Dict:
        """Sdílí AI chat s uživatelem (nebo veřejně)"""
        try:
            # Zkontroluj, zda session existuje
            from ..ai.models import AISession
            session = AISession.query.get(ai_session_id)
            if not session:
                return {"success": False, "error": f"AI session ID {ai_session_id} neexistuje"}
            
            shared_chat = SharedChat(
                ai_session_id=ai_session_id,
                shared_by_user_id=shared_by_user_id,
                shared_with_user_id=shared_with_user_id,
                poznamka=poznamka
            )
            
            db.session.add(shared_chat)
            db.session.commit()
            
            if shared_with_user_id:
                return {
                    "success": True,
                    "message": f"Chat byl sdílen s uživatelem",
                    "shared_chat_id": shared_chat.id
                }
            else:
                return {
                    "success": True,
                    "message": f"Chat byl sdílen veřejně",
                    "shared_chat_id": shared_chat.id
                }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_shared_chats_for_user(user_id: int, include_public: bool = True) -> List[SharedChat]:
        """Vrátí sdílené chaty pro uživatele"""
        query = SharedChat.query.filter_by(aktivni=True)
        
        # Chaty sdílené s uživatelem nebo veřejné
        if include_public:
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    SharedChat.shared_with_user_id == user_id,
                    SharedChat.shared_with_user_id.is_(None)
                )
            )
        else:
            query = query.filter_by(shared_with_user_id=user_id)
        
        return query.order_by(SharedChat.datum_sdileni.desc()).all()
    
    # ========================================================================
    # ZPRÁVY
    # ========================================================================
    
    @staticmethod
    def send_message(from_user_id: int, to_user_id: int = None, subject: str = "", content: str = "", typ: str = 'message') -> Dict:
        """Pošle zprávu uživateli (nebo veřejnou zprávu)"""
        try:
            message = UserMessage(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                subject=subject,
                content=content,
                typ=typ
            )
            
            db.session.add(message)
            
            # Vytvoř notifikaci pro příjemce (pokud není veřejná)
            if to_user_id:
                notification = UserNotification(
                    user_id=to_user_id,
                    typ='message',
                    title=f"Nová zpráva: {subject}",
                    content=content[:200],  # Prvních 200 znaků
                    related_id=message.id,
                    related_type='message'
                )
                db.session.add(notification)
            
            db.session.commit()
            
            return {
                "success": True,
                "message": "Zpráva byla odeslána",
                "message_id": message.id
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_user_messages(user_id: int, include_public: bool = True, unread_only: bool = False) -> List[UserMessage]:
        """Vrátí zprávy pro uživatele"""
        from sqlalchemy import or_
        
        query = UserMessage.query
        
        if include_public:
            query = query.filter(
                or_(
                    UserMessage.to_user_id == user_id,
                    UserMessage.to_user_id.is_(None)
                )
            )
        else:
            query = query.filter_by(to_user_id=user_id)
        
        if unread_only:
            query = query.filter_by(precteno=False)
        
        return query.order_by(UserMessage.datum_odeslani.desc()).all()
    
    # ========================================================================
    # NOTIFIKACE
    # ========================================================================
    
    @staticmethod
    def create_notification(user_id: int, typ: str, title: str, content: str = None, related_id: int = None, related_type: str = None) -> Dict:
        """Vytvoří notifikaci pro uživatele"""
        try:
            notification = UserNotification(
                user_id=user_id,
                typ=typ,
                title=title,
                content=content,
                related_id=related_id,
                related_type=related_type
            )
            
            db.session.add(notification)
            db.session.commit()
            
            return {
                "success": True,
                "message": "Notifikace byla vytvořena",
                "notification_id": notification.id
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_user_notifications(user_id: int, unread_only: bool = False) -> List[UserNotification]:
        """Vrátí notifikace pro uživatele"""
        query = UserNotification.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(precteno=False)
        
        return query.order_by(UserNotification.datum_vytvoreni.desc()).all()
    
    @staticmethod
    def mark_notification_read(notification_id: int) -> Dict:
        """Označí notifikaci jako přečtenou"""
        try:
            notification = UserNotification.query.get(notification_id)
            if not notification:
                return {"success": False, "error": "Notifikace neexistuje"}
            
            notification.precteno = True
            db.session.commit()
            
            return {"success": True, "message": "Notifikace byla označena jako přečtená"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}




