from typing import Optional, List
from datetime import datetime
import uuid
from ..models.user import UserCreate, UserInDB, User, UserUpdate
from ..core.security import get_password_hash, verify_password
from .elasticsearch import es_service

class UserService:
    async def create_user(self, user_data: UserCreate) -> User:
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(user_data.password)
        now = datetime.utcnow().isoformat()
        
        user_doc = {
            "id": user_id,
            "customer_id": user_data.customer_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "role": user_data.role,
            "is_active": user_data.is_active,
            "hashed_password": hashed_password,
            "created_at": now,
            "updated_at": now
        }
        
        es_service.index_document("users", user_id, user_doc)
        return User(**{k: v for k, v in user_doc.items() if k != "hashed_password"})
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        query = {
            "query": {
                "term": {"email": email}
            }
        }
        
        result = es_service.search_documents("users", query)
        if result["hits"]["total"]["value"] > 0:
            user_data = result["hits"]["hits"][0]["_source"]
            return UserInDB(**user_data)
        return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        result = es_service.get_document("users", user_id)
        if result:
            user_data = result["_source"]
            return User(**{k: v for k, v in user_data.items() if k != "hashed_password"})
        return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    async def get_users_by_customer(self, customer_id: str) -> List[User]:
        if customer_id:
            query = {"query": {"term": {"customer_id": customer_id}}}
        else:
            query = {"query": {"match_all": {}}}
        
        result = es_service.search_documents("users", query)
        users = []
        for hit in result["hits"]["hits"]:
            user_data = hit["_source"]
            users.append(User(**{k: v for k, v in user_data.items() if k != "hashed_password"}))
        return users
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        current_user = es_service.get_document("users", user_id)
        if not current_user:
            return None
        
        user_data = current_user["_source"]
        update_data = user_update.dict(exclude_unset=True)
        user_data.update(update_data)
        user_data["updated_at"] = datetime.utcnow().isoformat()
        
        es_service.index_document("users", user_id, user_data)
        return User(**{k: v for k, v in user_data.items() if k != "hashed_password"})
    
    async def delete_user(self, user_id: str) -> bool:
        try:
            es_service.delete_document("users", user_id)
            return True
        except Exception:
            return False

user_service = UserService()