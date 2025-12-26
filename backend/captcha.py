"""
验证码和登录状态检查模块
"""
import random
import string
import time
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import base64
from typing import Dict, Optional
from sqlalchemy.orm import Session
from models import User

# 简单的内存存储（生产环境应使用 Redis）
_captcha_store: Dict[str, Dict[str, any]] = {}

def generate_captcha() -> Dict[str, str]:
    """生成验证码"""
    # 生成4位随机字符
    captcha_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    captcha_id = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    
    # 创建验证码图片
    width, height = 120, 40
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # 绘制背景干扰线
    for _ in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), width=1)
    
    # 绘制验证码文字
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        except:
            font = ImageFont.load_default()
    
    # 计算文字位置
    bbox = draw.textbbox((0, 0), captcha_code, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # 绘制文字
    draw.text((x, y), captcha_code, fill=(0, 0, 0), font=font)
    
    # 转换为 base64
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # 存储验证码（5分钟过期）
    _captcha_store[captcha_id] = {
        "code": captcha_code.upper(),
        "created_at": time.time(),
        "expires_at": time.time() + 300  # 5分钟
    }
    
    return {
        "captcha_id": captcha_id,
        "image": f"data:image/png;base64,{image_base64}"
    }

def verify_captcha(captcha_id: str, captcha_code: str) -> bool:
    """验证验证码"""
    if not captcha_id or not captcha_code:
        return False
    
    if captcha_id not in _captcha_store:
        return False
    
    captcha_data = _captcha_store[captcha_id]
    
    # 检查是否过期
    if time.time() > captcha_data["expires_at"]:
        del _captcha_store[captcha_id]
        return False
    
    # 验证码不区分大小写
    is_valid = captcha_data["code"].upper() == captcha_code.upper()
    
    # 验证后删除（一次性使用）
    if captcha_id in _captcha_store:
        del _captcha_store[captcha_id]
    
    return is_valid

def check_login_status(db: Session, username_or_email: str) -> Dict[str, any]:
    """检查登录状态（是否需要验证码等）"""
    user = db.query(User).filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    ).first()
    
    if not user:
        return {
            "requires_captcha": False,
            "locked": False
        }
    
    # 检查是否被锁定
    current_time = int(time.time() * 1000)
    if user.locked_until and user.locked_until > current_time:
        lock_seconds = (user.locked_until - current_time) // 1000
        return {
            "requires_captcha": True,
            "locked": True,
            "lock_message": f"账户已被锁定，请在 {lock_seconds} 秒后重试"
        }
    
    # 如果密码失败次数 >= 3 或验证码失败次数 >= 3，需要验证码
    requires_captcha = (user.password_fail_count or 0) >= 3 or (user.captcha_fail_count or 0) >= 3
    
    return {
        "requires_captcha": requires_captcha,
        "locked": False
    }

