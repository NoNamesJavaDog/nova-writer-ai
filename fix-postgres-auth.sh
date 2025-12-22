#!/bin/bash
# Fix PostgreSQL authentication configuration

echo "Configuring PostgreSQL authentication..."

# Find PostgreSQL data directory
PG_DATA_DIR=$(sudo -u postgres psql -t -P format=unaligned -c 'SHOW data_directory' 2>/dev/null || echo "/var/lib/pgsql/data")
PG_HBA_CONF="$PG_DATA_DIR/pg_hba.conf"

# Backup original config
if [ -f "$PG_HBA_CONF" ]; then
  cp "$PG_HBA_CONF" "$PG_HBA_CONF.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Configure pg_hba.conf for password authentication
cat > "$PG_HBA_CONF" << 'EOF'
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# "local" is for Unix domain socket connections only
local   all             all                                     peer
# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
# IPv6 local connections:
host    all             all             ::1/128                 md5
# Allow replication connections from localhost, by a user with the
# replication privilege.
local   replication     all                                     peer
host    replication     all             127.0.0.1/32            md5
host    replication     all             ::1/128                 md5
EOF

# Set correct ownership
chown postgres:postgres "$PG_HBA_CONF"
chmod 600 "$PG_HBA_CONF"

# Reload PostgreSQL
systemctl reload postgresql 2>/dev/null || service postgresql reload 2>/dev/null || sudo -u postgres pg_ctl reload -D "$PG_DATA_DIR" 2>/dev/null

echo "PostgreSQL authentication configured"
echo "Configuration file: $PG_HBA_CONF"
echo "PostgreSQL reloaded"


