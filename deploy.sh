#!/bin/bash

# BOTA Project Deployment Script
# This script automates the deployment and update process

set -e  # Exit on any error

echo "======================================"
echo "BOTA Project Deployment Script"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/bota/BOTA_Project"
VENV_DIR="$PROJECT_DIR/venv"
BACKUP_DIR="/home/bota/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Check if running as bota user
if [ "$USER" != "bota" ]; then
    echo -e "${RED}Error: This script must be run as 'bota' user${NC}"
    echo "Use: sudo su - bota"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}Step 1: Creating database backup...${NC}"
if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
    cp "$PROJECT_DIR/db.sqlite3" "$BACKUP_DIR/db_${TIMESTAMP}.sqlite3"
    echo -e "${GREEN}✓ SQLite backup created${NC}"
elif command -v pg_dump &> /dev/null; then
    pg_dump bota_db > "$BACKUP_DIR/bota_db_${TIMESTAMP}.sql" 2>/dev/null || echo "No PostgreSQL database found"
fi

echo ""
echo -e "${YELLOW}Step 2: Fetching latest code from GitHub...${NC}"
cd "$PROJECT_DIR"
git fetch origin
git pull origin main
echo -e "${GREEN}✓ Code updated${NC}"

echo ""
echo -e "${YELLOW}Step 3: Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"
echo -e "${GREEN}✓ Virtual environment activated${NC}"

echo ""
echo -e "${YELLOW}Step 4: Installing/updating Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt --upgrade
echo -e "${GREEN}✓ Dependencies updated${NC}"

echo ""
echo -e "${YELLOW}Step 5: Running database migrations...${NC}"
python manage.py migrate
echo -e "${GREEN}✓ Migrations completed${NC}"

echo ""
echo -e "${YELLOW}Step 6: Collecting static files...${NC}"
python manage.py collectstatic --noinput
echo -e "${GREEN}✓ Static files collected${NC}"

echo ""
echo -e "${YELLOW}Step 7: Compiling translations...${NC}"
python manage.py compilemessages || echo "No translations to compile"
echo -e "${GREEN}✓ Translations compiled${NC}"

echo ""
echo -e "${YELLOW}Step 8: Updating diploma progress...${NC}"
python manage.py update_diploma_progress || echo "Diploma update skipped"
echo -e "${GREEN}✓ Diploma progress updated${NC}"

echo ""
echo -e "${YELLOW}Step 9: Running tests (optional)...${NC}"
read -p "Run tests? (y/N): " run_tests
if [ "$run_tests" = "y" ] || [ "$run_tests" = "Y" ]; then
    python manage.py test
    echo -e "${GREEN}✓ Tests completed${NC}"
else
    echo "Tests skipped"
fi

echo ""
echo -e "${YELLOW}Step 10: Restarting Gunicorn service...${NC}"
echo "You need to run this as root/sudo:"
echo "sudo systemctl restart bota"
echo ""
read -p "Press Enter to continue..."

echo ""
echo -e "${GREEN}======================================"
echo "Deployment completed successfully!"
echo "======================================"
echo ""
echo "Backup location: $BACKUP_DIR/db_${TIMESTAMP}.sqlite3"
echo ""
echo "Next steps:"
echo "1. Exit bota user: exit"
echo "2. Restart services: sudo systemctl restart bota nginx"
echo "3. Check logs: sudo journalctl -u bota -f"
echo ""
echo -e "${YELLOW}Don't forget to test the application!${NC}"
echo ""
