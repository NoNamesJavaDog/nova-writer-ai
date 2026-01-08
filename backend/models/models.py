"""数据库模型"""
from sqlalchemy import Column, String, Text, Integer, BigInteger, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(BigInteger, nullable=False)
    last_login_at = Column(BigInteger, nullable=True)
    # 登录失败计数
    password_fail_count = Column(Integer, nullable=False, default=0)  # 密码失败次数
    captcha_fail_count = Column(Integer, nullable=False, default=0)  # 验证码失败次数
    locked_until = Column(BigInteger, nullable=True)  # 账户锁定到期时间（时间戳，毫秒）
    last_fail_time = Column(BigInteger, nullable=True)  # 最后失败时间（用于重置计数器）
    
    novels = relationship("Novel", back_populates="user", cascade="all, delete-orphan")

class Novel(Base):
    __tablename__ = "novels"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    genre = Column(String(50), nullable=False)
    synopsis = Column(Text, nullable=True)
    full_outline = Column(Text, nullable=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)
    
    user = relationship("User", back_populates="novels")
    volumes = relationship("Volume", back_populates="novel", cascade="all, delete-orphan", order_by="Volume.volume_order")
    characters = relationship("Character", back_populates="novel", cascade="all, delete-orphan", order_by="Character.character_order")
    world_settings = relationship("WorldSetting", back_populates="novel", cascade="all, delete-orphan", order_by="WorldSetting.setting_order")
    timeline_events = relationship("TimelineEvent", back_populates="novel", cascade="all, delete-orphan", order_by="TimelineEvent.event_order")
    foreshadowings = relationship("Foreshadowing", back_populates="novel", cascade="all, delete-orphan", order_by="Foreshadowing.foreshadowing_order")

class Volume(Base):
    __tablename__ = "volumes"
    
    id = Column(String(36), primary_key=True)
    novel_id = Column(String(36), ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=True)
    outline = Column(Text, nullable=True)
    volume_order = Column(Integer, nullable=False, default=0)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)
    
    novel = relationship("Novel", back_populates="volumes")
    chapters = relationship("Chapter", back_populates="volume", cascade="all, delete-orphan", order_by="Chapter.chapter_order")

class Chapter(Base):
    __tablename__ = "chapters"
    
    id = Column(String(36), primary_key=True)
    volume_id = Column(String(36), ForeignKey("volumes.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    ai_prompt_hints = Column(Text, nullable=True)
    chapter_order = Column(Integer, nullable=False, default=0)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)
    
    volume = relationship("Volume", back_populates="chapters")

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(String(36), primary_key=True)
    novel_id = Column(String(36), ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(String(50), nullable=True)
    role = Column(String(100), nullable=True)
    personality = Column(Text, nullable=True)
    background = Column(Text, nullable=True)
    goals = Column(Text, nullable=True)
    character_order = Column(Integer, nullable=False, default=0)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)
    
    novel = relationship("Novel", back_populates="characters")

class WorldSetting(Base):
    __tablename__ = "world_settings"
    
    id = Column(String(36), primary_key=True)
    novel_id = Column(String(36), ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    setting_order = Column(Integer, nullable=False, default=0)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)
    
    novel = relationship("Novel", back_populates="world_settings")
    
    __table_args__ = (
        CheckConstraint("category IN ('地理', '社会', '魔法/科技', '科技', '历史', '其他')", name="check_category"),
    )

class TimelineEvent(Base):
    __tablename__ = "timeline_events"
    
    id = Column(String(36), primary_key=True)
    novel_id = Column(String(36), ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    time = Column(String(100), nullable=False)
    event = Column(Text, nullable=False)
    impact = Column(Text, nullable=True)
    event_order = Column(Integer, nullable=False, default=0)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)
    
    novel = relationship("Novel", back_populates="timeline_events")

class Foreshadowing(Base):
    __tablename__ = "foreshadowings"
    
    id = Column(String(36), primary_key=True)
    novel_id = Column(String(36), ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    chapter_id = Column(String(36), ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True)  # 伏笔产生的章节ID，可为空（大纲阶段生成）
    resolved_chapter_id = Column(String(36), ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True)  # 闭环章节ID
    content = Column(Text, nullable=False)  # 伏笔内容
    is_resolved = Column(String(10), nullable=False, default="false")  # 是否已闭环："true" 或 "false" (使用字符串以保持一致性)
    foreshadowing_order = Column(Integer, nullable=False, default=0)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)
    
    novel = relationship("Novel", back_populates="foreshadowings")
    chapter = relationship("Chapter", foreign_keys=[chapter_id])
    resolved_chapter = relationship("Chapter", foreign_keys=[resolved_chapter_id])

class UserCurrentNovel(Base):
    __tablename__ = "user_current_novel"
    
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    novel_id = Column(String(36), ForeignKey("novels.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(BigInteger, nullable=False)

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True)
    novel_id = Column(String(36), ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_type = Column(String(50), nullable=False)  # generate_outline, generate_volume_outline, write_chapter, etc.
    task_data = Column(Text, nullable=True)  # JSON 格式的任务参数
    status = Column(String(20), nullable=False, default="pending")  # pending, running, completed, failed
    progress = Column(Integer, nullable=False, default=0)  # 0-100
    progress_message = Column(Text, nullable=True)
    result = Column(Text, nullable=True)  # JSON 格式的任务结果
    error_message = Column(Text, nullable=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)
    started_at = Column(BigInteger, nullable=True)
    completed_at = Column(BigInteger, nullable=True)

