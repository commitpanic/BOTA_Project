# BOTA Project - Quick Reference

## Development Environment

### Python & Virtual Environment
```bash
# Activate virtual environment (PowerShell)
.\venv\Scripts\Activate.ps1

# Deactivate virtual environment
deactivate

# Check Python version
python --version

# Install package
pip install <package-name>

# Install from requirements.txt (when created)
pip install -r requirements.txt

# Freeze current packages
pip freeze > requirements.txt
```

### Django Management Commands

#### Database
```bash
# Create migrations for specific app
python manage.py makemigrations <app_name>

# Create migrations for all apps
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Create SQL for a migration (don't apply)
python manage.py sqlmigrate <app_name> <migration_number>

# Rollback a migration
python manage.py migrate <app_name> <migration_name_or_zero>
```

#### Users & Authentication
```bash
# Create superuser
python manage.py createsuperuser --email <email> --callsign <callsign>

# Change user password
python manage.py changepassword <email>
```

#### Development Server
```bash
# Run development server (default: http://127.0.0.1:8000)
python manage.py runserver

# Run on different port
python manage.py runserver 8080

# Run on all interfaces
python manage.py runserver 0.0.0.0:8000
```

#### Testing
```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test <app_name>

# Run specific test file
python manage.py test <app_name>.tests.test_models

# Run specific test class
python manage.py test <app_name>.tests.test_models.UserModelTest

# Run specific test method
python manage.py test <app_name>.tests.test_models.UserModelTest.test_create_user

# Run tests with verbosity (0-3)
python manage.py test --verbosity=2

# Run tests and keep test database
python manage.py test --keepdb

# Run tests with coverage (after installing coverage)
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

#### Shell & Debugging
```bash
# Django shell (interactive Python with Django loaded)
python manage.py shell

# Shell plus (if django-extensions installed)
python manage.py shell_plus

# Database shell
python manage.py dbshell

# Check for problems
python manage.py check

# Check deployment readiness
python manage.py check --deploy
```

#### Static Files & Media
```bash
# Collect static files for production
python manage.py collectstatic

# Clear collected static files
python manage.py collectstatic --clear

# Don't ask for confirmation
python manage.py collectstatic --noinput
```

#### Custom Management
```bash
# Create custom management command
# Create: <app>/management/commands/mycommand.py
python manage.py mycommand
```

---

## Git Commands (When Repository Created)

### Basic Git Workflow
```bash
# Initialize repository
git init

# Check status
git status

# Add files to staging
git add .
git add <file_name>

# Commit changes
git commit -m "commit message"

# View commit history
git log
git log --oneline

# Create branch
git checkout -b <branch_name>

# Switch branch
git checkout <branch_name>

# Merge branch
git merge <branch_name>

# Push to remote
git push origin <branch_name>

# Pull from remote
git pull origin <branch_name>
```

---

## Useful Django Shell Commands

### Working with Users
```python
# In Django shell: python manage.py shell
from accounts.models import User, UserStatistics

# Get all users
users = User.objects.all()

# Get user by email
user = User.objects.get(email='test@example.com')

# Create user
user = User.objects.create_user(
    email='newuser@example.com',
    callsign='NEW123',
    password='password123'
)

# Update user statistics
stats = user.statistics
stats.add_hunter_qso()
stats.update_total_points()

# Get user's total points
print(user.statistics.total_points)
```

---

## Database Queries (Examples)

```python
# Get all active users
active_users = User.objects.filter(is_active=True)

# Get users with more than 100 points
top_users = User.objects.filter(statistics__total_points__gt=100)

# Order by points (leaderboard)
leaderboard = User.objects.order_by('-statistics__total_points')[:10]

# Count users
user_count = User.objects.count()

# Aggregate statistics
from django.db.models import Sum, Avg
total_qsos = UserStatistics.objects.aggregate(Sum('total_hunter_qso'))
avg_points = UserStatistics.objects.aggregate(Avg('total_points'))
```

---

## Testing Shortcuts

```bash
# Quick test run for current work
python manage.py test accounts --failfast  # Stop on first failure

# Run with parallel execution (faster)
python manage.py test --parallel

# Run tests matching pattern
python manage.py test --pattern="test_user*"
```

---

## Admin Interface

### Access Admin
- URL: http://127.0.0.1:8000/admin/
- Login: admin@bota.com / (password set during createsuperuser)

### Register Models in Admin
```python
# In admin.py
from django.contrib import admin
from .models import MyModel

@admin.register(MyModel)
class MyModelAdmin(admin.ModelAdmin):
    list_display = ('field1', 'field2')
    list_filter = ('field3',)
    search_fields = ('field1', 'field2')
```

---

## Environment Variables (.env file - to be created)

```env
# Secret key (generate new for production)
SECRET_KEY=your-secret-key-here

# Debug mode (False for production)
DEBUG=True

# Allowed hosts
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (MySQL for production)
DB_ENGINE=django.db.backends.mysql
DB_NAME=bota_db
DB_USER=bota_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=3306

# Email configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
```

---

## Useful VSCode Extensions

- Python (Microsoft)
- Django (Baptiste Darthenay)
- Pylance (Microsoft)
- Python Test Explorer
- SQLite Viewer
- GitLens
- Better Comments

---

## Common Issues & Solutions

### Issue: "No module named 'accounts'"
**Solution**: Make sure virtual environment is activated

### Issue: Migration conflicts
**Solution**: 
```bash
python manage.py migrate --fake <app_name> zero
python manage.py migrate <app_name>
```

### Issue: Admin CSS not loading
**Solution**:
```bash
python manage.py collectstatic
```

### Issue: Port already in use
**Solution**:
```bash
# Use different port
python manage.py runserver 8080

# Or kill process using port (Windows)
netstat -ano | findstr :8000
taskkill /PID <process_id> /F
```

---

## Project-Specific Notes

### Custom User Model
- Username field: **email**
- Required fields: email, password, callsign
- UserStatistics automatically created via signal

### Testing
- All tests must pass before committing
- Target: 80%+ code coverage
- Run tests: `python manage.py test`

### Code Style
- Follow PEP 8
- Use meaningful variable names
- Write docstrings for all functions/classes
- Keep functions small and focused

---

## Documentation Files

- `PROJECT_SPECIFICATION.md` - Complete project specs (v1.7)
- `MILESTONES.md` - Project roadmap and progress
- `SESSION_SUMMARY_*.md` - Daily development summaries

---

*Last Updated: November 3, 2025*
*BOTA Project Development Team*
