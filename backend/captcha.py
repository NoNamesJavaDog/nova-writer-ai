# 临时验证码模块（简化版）
import uuid
from typing import Dict

# 内存存储验证码（生产环境应使用Redis）
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

def check_login_status(db, username_or_email: str) -> Dict[str, bool]:
    """检查登录状态（简化版，不需要验证码）"""
    return {
        "requires_captcha": False,
        "exists": True
    }

