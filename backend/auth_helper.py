"""认证辅助函数"""
import time
from sqlalchemy.orm import Session
from models import User

# 登录失败阈值
PASSWORD_FAIL_THRESHOLD_FOR_CAPTCHA = 2  # 2次密码错误后需要验证码
PASSWORD_FAIL_THRESHOLD_FOR_LOCK = 8  # 8次密码错误后锁定账户
CAPTCHA_FAIL_THRESHOLD_FOR_LOCK = 5  # 5次验证码错误后锁定账户
LOCK_DURATION = 3600000  # 锁定时间：1小时（毫秒）

def reset_fail_counters(user: User):
    """重置失败计数器（登录成功时调用）"""
    user.password_fail_count = 0
    user.captcha_fail_count = 0
    user.locked_until = None
    user.last_fail_time = None

def increment_password_fail(user: User):
    """增加密码失败次数"""
    current_time = int(time.time() * 1000)
    
    # 如果距离上次失败超过1小时，重置计数器
    if user.last_fail_time and (current_time - user.last_fail_time) > 3600000:
        user.password_fail_count = 0
        user.captcha_fail_count = 0
    
    user.password_fail_count += 1
    user.last_fail_time = current_time
    
    # 如果达到锁定阈值，锁定账户
    if user.password_fail_count >= PASSWORD_FAIL_THRESHOLD_FOR_LOCK:
        user.locked_until = current_time + LOCK_DURATION

def increment_captcha_fail(user: User):
    """增加验证码失败次数"""
    current_time = int(time.time() * 1000)
    
    # 如果距离上次失败超过1小时，重置计数器
    if user.last_fail_time and (current_time - user.last_fail_time) > 3600000:
        user.password_fail_count = 0
        user.captcha_fail_count = 0
    
    user.captcha_fail_count += 1
    user.last_fail_time = current_time
    
    # 如果达到锁定阈值，锁定账户
    if user.captcha_fail_count >= CAPTCHA_FAIL_THRESHOLD_FOR_LOCK:
        user.locked_until = current_time + LOCK_DURATION

def is_account_locked(user: User) -> bool:
    """检查账户是否被锁定"""
    if not user.locked_until:
        return False
    
    current_time = int(time.time() * 1000)
    
    # 如果锁定时间已过，解除锁定
    if current_time >= user.locked_until:
        user.locked_until = None
        user.password_fail_count = 0
        user.captcha_fail_count = 0
        return False
    
    return True

def requires_captcha(user: User) -> bool:
    """检查是否需要验证码"""
    # 如果账户被锁定，需要验证码（虽然会被拒绝登录）
    if is_account_locked(user):
        return True
    
    # 密码失败次数达到阈值后需要验证码
    return user.password_fail_count >= PASSWORD_FAIL_THRESHOLD_FOR_CAPTCHA

