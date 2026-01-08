"""安全模块 - 认证、授权、密码处理等"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
import bcrypt
import uuid
import time
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from ..models import User
from .database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        password_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌（短期令牌，默认1小时）"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    """创建刷新令牌（长期令牌，7天）"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_refresh_token(token: str) -> Optional[str]:
    """验证刷新令牌，返回用户ID"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_type = payload.get("type")
        user_id = payload.get("sub")
        
        if token_type != "refresh" or user_id is None:
            return None
        return user_id
    except JWTError:
        return None


def get_user_by_username_or_email(db: Session, username_or_email: str) -> Optional[User]:
    """根据用户名或邮箱获取用户"""
    user = db.query(User).filter(
        (User.username == username_or_email) | (User.email == username_or_email.lower())
    ).first()
    return user


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """获取当前登录用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def generate_uuid() -> str:
    """生成 UUID"""
    return str(uuid.uuid4())


def handle_login_failure(
    db: Session,
    user: User,
    captcha_id: str = None,
    captcha_code: str = None
):
    """处理登录失败"""
    current_time = int(time.time() * 1000)
    
    # 更新密码失败计数
    user.password_fail_count = (user.password_fail_count or 0) + 1
    user.last_fail_time = current_time
    
    # 如果验证码验证失败，增加验证码失败计数
    if captcha_id and captcha_code:
        if not verify_captcha(captcha_id, captcha_code):
            user.captcha_fail_count = (user.captcha_fail_count or 0) + 1
    
    # 如果密码失败次数达到阈值，锁定账户
    MAX_PASSWORD_FAILURES = 5
    LOCK_DURATION_MS = 15 * 60 * 1000  # 15分钟
    
    if user.password_fail_count >= MAX_PASSWORD_FAILURES:
        user.locked_until = current_time + LOCK_DURATION_MS
    
    db.commit()


# 验证码模块（临时简化版）
_captcha_store: Dict[str, str] = {}


def generate_captcha() -> Dict[str, str]:
    """生成验证码（简化版，返回空图片）"""
    captcha_id = str(uuid.uuid4())
    code = "1234"  # 固定验证码
    _captcha_store[captcha_id] = code
    return {
        "captcha_id": captcha_id,
        "image": ""  # 空图片
    }


def verify_captcha(captcha_id: str, code: str) -> bool:
    """验证验证码"""
    stored_code = _captcha_store.get(captcha_id)
    if stored_code:
        # 验证成功后删除
        del _captcha_store[captcha_id]
        return stored_code == code
    return False


def check_login_status(db: Session, username_or_email: str) -> Dict[str, bool]:
    """检查登录状态（简化版，不需要验证码）"""
    return {
        "requires_captcha": False,
        "exists": True
    }

