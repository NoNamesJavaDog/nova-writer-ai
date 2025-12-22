-- NovaWrite AI 数据库结构

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at BIGINT NOT NULL,
    last_login_at BIGINT,
    CONSTRAINT username_length CHECK (char_length(username) >= 3),
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- 小说表
CREATE TABLE IF NOT EXISTS novels (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    genre VARCHAR(50) NOT NULL,
    synopsis TEXT,
    full_outline TEXT,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    CONSTRAINT novels_user_fk FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 卷表
CREATE TABLE IF NOT EXISTS volumes (
    id VARCHAR(36) PRIMARY KEY,
    novel_id VARCHAR(36) NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    summary TEXT,
    outline TEXT,
    volume_order INTEGER NOT NULL DEFAULT 0,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    CONSTRAINT volumes_novel_fk FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
);

-- 章节表
CREATE TABLE IF NOT EXISTS chapters (
    id VARCHAR(36) PRIMARY KEY,
    volume_id VARCHAR(36) NOT NULL REFERENCES volumes(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    summary TEXT,
    content TEXT,
    ai_prompt_hints TEXT,
    chapter_order INTEGER NOT NULL DEFAULT 0,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    CONSTRAINT chapters_volume_fk FOREIGN KEY (volume_id) REFERENCES volumes(id) ON DELETE CASCADE
);

-- 角色表
CREATE TABLE IF NOT EXISTS characters (
    id VARCHAR(36) PRIMARY KEY,
    novel_id VARCHAR(36) NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    age VARCHAR(50),
    role VARCHAR(100),
    personality TEXT,
    background TEXT,
    goals TEXT,
    character_order INTEGER NOT NULL DEFAULT 0,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    CONSTRAINT characters_novel_fk FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
);

-- 世界观设置表
CREATE TABLE IF NOT EXISTS world_settings (
    id VARCHAR(36) PRIMARY KEY,
    novel_id VARCHAR(36) NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('地理', '社会', '魔法/科技', '历史', '其他')),
    setting_order INTEGER NOT NULL DEFAULT 0,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    CONSTRAINT world_settings_novel_fk FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
);

-- 时间线事件表
CREATE TABLE IF NOT EXISTS timeline_events (
    id VARCHAR(36) PRIMARY KEY,
    novel_id VARCHAR(36) NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    time VARCHAR(100) NOT NULL,
    event TEXT NOT NULL,
    impact TEXT,
    event_order INTEGER NOT NULL DEFAULT 0,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    CONSTRAINT timeline_events_novel_fk FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
);

-- 用户当前选择的小说ID（用于快速访问）
CREATE TABLE IF NOT EXISTS user_current_novel (
    user_id VARCHAR(36) PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    novel_id VARCHAR(36) REFERENCES novels(id) ON DELETE SET NULL,
    updated_at BIGINT NOT NULL
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_novels_user_id ON novels(user_id);
CREATE INDEX IF NOT EXISTS idx_volumes_novel_id ON volumes(novel_id);
CREATE INDEX IF NOT EXISTS idx_chapters_volume_id ON chapters(volume_id);
CREATE INDEX IF NOT EXISTS idx_characters_novel_id ON characters(novel_id);
CREATE INDEX IF NOT EXISTS idx_world_settings_novel_id ON world_settings(novel_id);
CREATE INDEX IF NOT EXISTS idx_timeline_events_novel_id ON timeline_events(novel_id);
CREATE INDEX IF NOT EXISTS idx_volumes_order ON volumes(novel_id, volume_order);
CREATE INDEX IF NOT EXISTS idx_chapters_order ON chapters(volume_id, chapter_order);

