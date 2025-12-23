"""验证码生成和验证"""
import random
import string
import io
from PIL import Image, ImageDraw, ImageFont
import base64
from typing import Tuple, Dict
import time

# 验证码存储（生产环境应使用 Redis）
captcha_store: Dict[str, Dict[str, any]] = {}

# 验证码过期时间（5分钟）
CAPTCHA_EXPIRE = 300

def generate_captcha_code(length: int = 4) -> str:
    """生成验证码字符串（数字+字母）"""
    characters = string.ascii_uppercase + string.digits
    # 排除容易混淆的字符
    characters = characters.replace('0', '').replace('O', '').replace('1', '').replace('I', '').replace('L', '')
    return ''.join(random.choices(characters, k=length))

def generate_captcha_image(code: str) -> bytes:
    """生成验证码图片"""
    # 图片大小
    width, height = 120, 40
    
    # 创建图片
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # 绘制背景干扰线
    for _ in range(5):
        start = (random.randint(0, width), random.randint(0, height))
        end = (random.randint(0, width), random.randint(0, height))
        draw.line([start, end], fill=(random.randint(200, 255), random.randint(200, 255), random.randint(200, 255)), width=1)
    
    # 绘制验证码文字
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        try:
            # Windows 字体
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            # 使用默认字体
            font = ImageFont.load_default()
    
    # 计算文字位置
    char_width = width // len(code)
    for i, char in enumerate(code):
        x = char_width * i + random.randint(5, 15)
        y = random.randint(5, 10)
        # 随机颜色（深色）
        color = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
        draw.text((x, y), char, font=font, fill=color)
    
    # 添加干扰点
    for _ in range(50):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    
    # 转换为 base64
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    return image_bytes

def create_captcha() -> Tuple[str, str]:
    """创建验证码，返回 (captcha_id, base64_image)"""
    captcha_code = generate_captcha_code()
    captcha_id = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    
    # 生成图片
    image_bytes = generate_captcha_image(captcha_code)
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    image_data_url = f"data:image/png;base64,{image_base64}"
    
    # 存储验证码（带过期时间）
    captcha_store[captcha_id] = {
        'code': captcha_code.upper(),  # 存储时转为大写，验证时不区分大小写
        'created_at': time.time()
    }
    
    return captcha_id, image_data_url

def verify_captcha(captcha_id: str, user_code: str) -> bool:
    """验证验证码"""
    if not captcha_id or not user_code:
        return False
    
    if captcha_id not in captcha_store:
        return False
    
    captcha_data = captcha_store[captcha_id]
    
    # 检查是否过期
    if time.time() - captcha_data['created_at'] > CAPTCHA_EXPIRE:
        del captcha_store[captcha_id]
        return False
    
    # 验证码不区分大小写
    is_valid = captcha_data['code'].upper() == user_code.upper().strip()
    
    # 验证后删除（一次性使用）
    del captcha_store[captcha_id]
    
    return is_valid

def cleanup_expired_captchas():
    """清理过期的验证码（可选，定期执行）"""
    current_time = time.time()
    expired_ids = [
        captcha_id for captcha_id, data in captcha_store.items()
        if current_time - data['created_at'] > CAPTCHA_EXPIRE
    ]
    for captcha_id in expired_ids:
        del captcha_store[captcha_id]

