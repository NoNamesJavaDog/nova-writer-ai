#!/bin/bash
# 执行数据库迁移脚本

PGPASSWORD='novawrite_db_2024' psql -U postgres -d novawrite_ai -h localhost <<EOF
-- 添加登录安全相关字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_fail_count INTEGER DEFAULT 0 NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS captcha_fail_count INTEGER DEFAULT 0 NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until BIGINT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_fail_time BIGINT;

-- 验证字段是否添加成功
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('password_fail_count', 'captcha_fail_count', 'locked_until', 'last_fail_time')
ORDER BY column_name;
EOF

