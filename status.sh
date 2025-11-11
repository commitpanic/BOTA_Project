#!/bin/bash

# BOTA Project Status Check Script
# Quick health check for all services

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================"
echo "BOTA Project Status Check"
echo "======================================${NC}"
echo ""

# Check Gunicorn service
echo -e "${YELLOW}Gunicorn Service:${NC}"
if systemctl is-active --quiet bota; then
    echo -e "  ${GREEN}✓ Running${NC}"
    systemctl status bota --no-pager | grep "Active:"
else
    echo -e "  ${RED}✗ Not running${NC}"
fi
echo ""

# Check Nginx
echo -e "${YELLOW}Nginx Service:${NC}"
if systemctl is-active --quiet nginx; then
    echo -e "  ${GREEN}✓ Running${NC}"
    systemctl status nginx --no-pager | grep "Active:"
else
    echo -e "  ${RED}✗ Not running${NC}"
fi
echo ""

# Check PostgreSQL (if installed)
if command -v psql &> /dev/null; then
    echo -e "${YELLOW}PostgreSQL Service:${NC}"
    if systemctl is-active --quiet postgresql; then
        echo -e "  ${GREEN}✓ Running${NC}"
        systemctl status postgresql --no-pager | grep "Active:"
    else
        echo -e "  ${RED}✗ Not running${NC}"
    fi
    echo ""
fi

# Check Redis (if installed)
if command -v redis-cli &> /dev/null; then
    echo -e "${YELLOW}Redis Service:${NC}"
    if systemctl is-active --quiet redis-server; then
        echo -e "  ${GREEN}✓ Running${NC}"
        systemctl status redis-server --no-pager | grep "Active:"
    else
        echo -e "  ${RED}✗ Not running${NC}"
    fi
    echo ""
fi

# Check disk space
echo -e "${YELLOW}Disk Space:${NC}"
df -h /home/bota | tail -n 1 | awk '{print "  Used: "$3" / "$2" ("$5")"}'
echo ""

# Check memory usage
echo -e "${YELLOW}Memory Usage:${NC}"
free -h | grep Mem: | awk '{print "  Used: "$3" / "$2}'
echo ""

# Check Gunicorn processes
echo -e "${YELLOW}Gunicorn Workers:${NC}"
worker_count=$(ps aux | grep -c "[g]unicorn")
if [ "$worker_count" -gt 0 ]; then
    echo -e "  ${GREEN}✓ $worker_count processes running${NC}"
else
    echo -e "  ${RED}✗ No Gunicorn processes found${NC}"
fi
echo ""

# Check recent errors in logs (last 1 hour)
echo -e "${YELLOW}Recent Errors (last hour):${NC}"
error_count=$(journalctl -u bota --since "1 hour ago" | grep -ci error || echo "0")
if [ "$error_count" -eq 0 ]; then
    echo -e "  ${GREEN}✓ No errors found${NC}"
else
    echo -e "  ${YELLOW}⚠ $error_count errors found${NC}"
    echo "  Run: journalctl -u bota --since '1 hour ago' | grep -i error"
fi
echo ""

# Check application endpoint
echo -e "${YELLOW}Application Health:${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000 | grep -q "200\|301\|302"; then
    echo -e "  ${GREEN}✓ Application responding${NC}"
else
    echo -e "  ${RED}✗ Application not responding${NC}"
fi
echo ""

# SSL Certificate check (if domain is configured)
if [ -d "/etc/letsencrypt/live" ]; then
    echo -e "${YELLOW}SSL Certificate:${NC}"
    cert_dir=$(ls -t /etc/letsencrypt/live/ | head -n 1)
    if [ -n "$cert_dir" ]; then
        cert_path="/etc/letsencrypt/live/$cert_dir/cert.pem"
        if [ -f "$cert_path" ]; then
            expiry=$(openssl x509 -enddate -noout -in "$cert_path" | cut -d= -f2)
            echo -e "  ${GREEN}✓ Certificate expires: $expiry${NC}"
        fi
    fi
    echo ""
fi

# Quick tips
echo -e "${BLUE}======================================"
echo "Quick Commands:"
echo "======================================${NC}"
echo "Restart services:     sudo systemctl restart bota nginx"
echo "View live logs:       sudo journalctl -u bota -f"
echo "View error logs:      sudo journalctl -u bota | grep -i error"
echo "Update application:   cd /home/bota/BOTA_Project && ./deploy.sh"
echo ""
