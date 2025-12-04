#!/bin/bash

# Clean ALL data from database and Redis
# This is a comprehensive cleanup script for macOS

# Color codes
CYAN='\033[36m'
YELLOW='\033[33m'
RED='\033[31m'
GREEN='\033[32m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================"
echo -e "COMPREHENSIVE CLEANUP SCRIPT"
echo -e "========================================${NC}"
echo ""
echo -e "${YELLOW}This script will clean:${NC}"
echo -e "${YELLOW}  1. All MySQL database tables${NC}"
echo -e "${YELLOW}  2. All Redis data (queues, jobs, cache)${NC}"
echo ""

# Check if containers are running
echo -e "${CYAN}Checking if Docker containers are running...${NC}"
mysql_running=$(docker ps --filter "name=database" --filter "status=running" --format "{{.Names}}")
redis_running=$(docker ps --filter "name=redis" --filter "status=running" --format "{{.Names}}")

if [ -z "$mysql_running" ]; then
    echo -e "${RED}ERROR: Database container is not running!${NC}"
    echo -e "${YELLOW}Please start the development environment first with: ./start-dev.sh${NC}"
    exit 1
fi

if [ -z "$redis_running" ]; then
    echo -e "${RED}ERROR: Redis container is not running!${NC}"
    echo -e "${YELLOW}Please start the development environment first with: ./start-dev.sh${NC}"
    exit 1
fi

echo -e "${GREEN}Database container: $mysql_running${NC}"
echo -e "${GREEN}Redis container: $redis_running${NC}"
echo ""

# Prompt for confirmation
echo -e "${RED}WARNING: This will delete ALL data!${NC}"
echo ""

read -p "Are you sure you want to continue? Type 'YES' to confirm: " confirmation

if [ "$confirmation" != "YES" ]; then
    echo -e "${YELLOW}Cleanup cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${CYAN}========================================"
echo -e "Step 1: Cleaning Redis..."
echo -e "========================================${NC}"
echo ""

# Clean Redis
if ! docker exec -i "$redis_running" redis-cli FLUSHALL 2>&1; then
    echo -e "${RED}ERROR: Failed to flush Redis data${NC}"
    exit 1
fi

echo -e "${GREEN}Redis cleaned successfully!${NC}"
keys_count=$(docker exec -i "$redis_running" redis-cli DBSIZE)
echo -e "${CYAN}Keys remaining: $keys_count${NC}"
echo ""

echo -e "${CYAN}========================================"
echo -e "Step 2: Cleaning MySQL Database..."
echo -e "========================================${NC}"
echo ""

# Get database credentials
env_file="backend/.env"
if [ ! -f "$env_file" ]; then
    echo -e "${RED}ERROR: Environment file not found at $env_file${NC}"
    exit 1
fi

# Extract database credentials from .env file
db_user=$(grep '^MYSQL_USER=' "$env_file" | cut -d'=' -f2)
db_password=$(grep '^MYSQL_PASSWORD=' "$env_file" | cut -d'=' -f2)
db_name=$(grep '^MYSQL_DATABASE=' "$env_file" | cut -d'=' -f2)

if [ -z "$db_user" ] || [ -z "$db_password" ] || [ -z "$db_name" ]; then
    echo -e "${RED}ERROR: Could not read database credentials from $env_file${NC}"
    exit 1
fi

# SQL commands
read -r -d '' sql_commands << 'EOF'
SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE tickets;
TRUNCATE TABLE articles;
TRUNCATE TABLE intents;
TRUNCATE TABLE categories;
TRUNCATE TABLE company_files;
TRUNCATE TABLE company_profile;
TRUNCATE TABLE users;

SET FOREIGN_KEY_CHECKS = 1;

SELECT 'tickets' as table_name, COUNT(*) as row_count FROM tickets
UNION ALL
SELECT 'articles', COUNT(*) FROM articles
UNION ALL
SELECT 'intents', COUNT(*) FROM intents
UNION ALL
SELECT 'categories', COUNT(*) FROM categories
UNION ALL
SELECT 'company_files', COUNT(*) FROM company_files
UNION ALL
SELECT 'company_profile', COUNT(*) FROM company_profile
UNION ALL
SELECT 'users', COUNT(*) FROM users;
EOF

# Execute SQL commands
if ! result=$(docker exec -i "$mysql_running" mysql -u"$db_user" -p"$db_password" "$db_name" -e "$sql_commands" 2>&1); then
    echo -e "${RED}ERROR: Failed to clean database${NC}"
    echo -e "${RED}$result${NC}"
    exit 1
fi

echo -e "${GREEN}Database cleaned successfully!${NC}"
echo ""
echo -e "${CYAN}Table row counts:${NC}"
echo "$result"
echo ""

echo -e "${CYAN}========================================"
echo -e "${GREEN}ALL CLEANUP COMPLETE!${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${CYAN}Summary:${NC}"
echo -e "${GREEN}  - Redis: Flushed${NC}"
echo -e "${GREEN}  - MySQL: All tables truncated${NC}"
echo ""
echo -e "${YELLOW}You can now start fresh with your application!${NC}"
