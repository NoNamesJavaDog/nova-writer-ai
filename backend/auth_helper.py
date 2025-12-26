"""
认证辅助函数
处理登录失败逻辑
"""
import time
from sqlalchemy.orm import Session
from models import User
from captcha import verify_captcha

def handle_login_failure(
    db: Session,
    user: User,
    captcha_id: str = None,
    captcha_code: str = None
):
    """处理登录失败"""
    current_time = int(time.time() * 1000)
    
    # 如果提供了验证码，检查验证码是否正确
    if captcha_id and captcha_code:
        if verify_captcha(captcha_id, captcha_code):
            # 验证码正确，只增加密码失败计数
            user.password_fail_count = (user.password_fail_count or 0) + 1
        else:
            # 验证码错误，增加验证码失败计数
            user.captcha_fail_count = (user.captcha_fail_count or 0) + 1
    else:
        # 没有提供验证码，增加密码失败计数
        user.password_fail_count = (user.password_fail_count or 0) + 1
    
    # 如果密码失败次数 >= 5，锁定账户 30 分钟
    if (user.password_fail_count or 0) >= 5:
        user.locked_until = current_time + (30 * 60 * 1000)  # 30分钟
    
    # 如果验证码失败次数 >= 5，锁定账户 30 分钟
    if (user.captcha_fail_count or 0) >= 5:
        user.locked_until = current_time + (30 * 60 * 1000)  # 30分钟
    
    db.commit()

