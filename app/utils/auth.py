import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Union, Any

import bcrypt
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config.config import SECRET_KEY
from app.models.user import User
from app.database.user_repository import UserRepository

# Configure logging
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
JWT_SECRET_KEY = SECRET_KEY
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a password hash"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Create encoded JWT
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"Invalid token: {e}")
        return None


def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password"""
    try:
        user_repo = UserRepository()
        user = user_repo.get_by_email(email)
        
        if not user:
            logger.warning(f"No user found with email: {email}")
            return None
        
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Invalid password for user: {email}")
            return None
        
        # Update last login time
        user_repo.update_last_login(user.id)
        
        return user
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None