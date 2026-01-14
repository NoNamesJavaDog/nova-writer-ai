"""认证辅助函数"""
from sqlalchemy.orm import Session
from models import User
import time

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
        from captcha import verify_captcha
        if not verify_captcha(captcha_id, captcha_code):
            user.captcha_fail_count = (user.captcha_fail_count or 0) + 1
    
    # 如果密码失败次数达到阈值，锁定账户
    # 例如：5次失败锁定15分钟
    MAX_PASSWORD_FAILURES = 5
    LOCK_DURATION_MS = 15 * 60 * 1000  # 15分钟
    
    if user.password_fail_count >= MAX_PASSWORD_FAILURES:
        user.locked_until = current_time + LOCK_DURATION_MS
    
    db.commit()


