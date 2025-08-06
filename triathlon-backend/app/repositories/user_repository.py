from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user import User, AdminUser

class UserRepositoryInterface(ABC):
    """ユーザーリポジトリインターフェース"""
    
    @abstractmethod
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        pass
    
    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[User]:
        pass
    
    @abstractmethod
    def create_user(self, user: User) -> User:
        pass
    
    @abstractmethod
    def update_user(self, user: User) -> User:
        pass
    
    @abstractmethod
    def delete_user(self, user_id: str) -> bool:
        pass

class SQLiteUserRepository(UserRepositoryInterface):
    """SQLite用ユーザーリポジトリ実装"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter_by(user_id=user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter_by(username=username).first()
    
    def create_user(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_user(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete_user(self, user_id: str) -> bool:
        user = self.get_user_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False