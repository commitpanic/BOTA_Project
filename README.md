# BOTA Project

**Bunkers On The Air** - A Django-based web application for managing bunkers, military buildings, user activities, and achievement-based diplomas.

![Django](https://img.shields.io/badge/Django-5.2.7-green.svg)
![Python](https://img.shields.io/badge/Python-3.11.9-blue.svg)
![Status](https://img.shields.io/badge/Status-In%20Development-yellow.svg)
![Tests](https://img.shields.io/badge/Tests-299%2B%20Passing-success.svg)
![Progress](https://img.shields.io/badge/Progress-85%25-blue.svg)
![i18n](https://img.shields.io/badge/i18n-Polish%20%7C%20English-blueviolet.svg)
![GDPR](https://img.shields.io/badge/GDPR-90%25%20Compliant-green.svg)

---

## 📋 Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Documentation](#documentation)
- [Development Status](#development-status)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Project Overview

BOTA Project is a comprehensive web application designed to manage bunkers, military buildings, and other structures. The system supports:
- User authentication with email-based login
- Activity tracking for "Hunters" and "Activators"
- Achievement-based diploma system with points
- Bunker management with GPS coordinates and photos
- CSV import/export for bulk operations
- Multilingual support (Polish & English)
- Mobile-responsive design

---

## ✨ Features

### Current Features (Phases 1-9 ~90% Complete) ✅

**Backend (100% Complete):**
- ✅ Custom user authentication (email + password + callsign)
- ✅ User statistics tracking (Hunter, Activator, B2B QSOs)
- ✅ Comprehensive points system (6 point categories)
- ✅ Role-based access control (RBAC)
- ✅ Bunker management with GPS coordinates
- ✅ Bunker categories with multilingual support (Polish/English)
- ✅ Photo upload with approval workflow
- ✅ Bunker resources (external links)
- ✅ Bunker inspections (visit tracking)
- ✅ Django admin interface with inline editing
- ✅ Cluster management with regional grouping
- ✅ Cluster alerts with time-based activation
- ✅ Activation keys with auto-generation and usage limits
- ✅ Activation logs with QSO tracking and B2B support
- ✅ Special event licenses with bunker restrictions
- ✅ Diploma types with bilingual names and requirements
- ✅ Achievement tracking with automatic progress calculation
- ✅ Diploma issuance with unique numbering (CATEGORY-YYYY-XXXX)
- ✅ Diploma verification with UUID codes
- ✅ Progress tracking with visual indicators
- ✅ **Spotting system (cluster)** - Real-time spot posting with auto-refresh
- ✅ 299+ unit tests with 100% pass rate

**Frontend (100% Complete):**
- ✅ Bootstrap 5 responsive design
- ✅ User registration and login pages
- ✅ Dashboard with statistics overview
- ✅ ADIF log upload functionality
- ✅ Bunker listing and detail pages
- ✅ Diploma/awards progress tracking page
- ✅ **Spotting page with modals** (post spot, filter)
- ✅ **Auto-refresh with pause/resume button**
- ✅ **Scroll position preservation** (sessionStorage)
- ✅ **BOTA logo integration** in navigation
- ✅ Language switcher (EN/PL)

**Translations (100% Complete):**
- ✅ Complete Polish translations (~400+ strings)
- ✅ All UI elements translated
- ✅ Legal pages fully bilingual
- ✅ Compiled django.mo translations

**GDPR & Legal (90% Complete):**
- ✅ **Cookie consent banner** with localStorage tracking
- ✅ **Privacy Policy** (11 sections, GDPR-compliant)
- ✅ **Cookie Policy** (8 sections, detailed cookie table)
- ✅ **Terms of Service** (14 sections, complete legal terms)
- ✅ Footer links to legal pages
- ✅ Contact information (sp3fck@gmail.com, spbota.pl)
- ⏳ "Download My Data" feature (pending)
- ⏳ "Delete My Account" feature (pending)

### Planned Features (Future Phases)
- 🔄 On-demand PDF diploma generation with reportlab
- 🔄 "Download My Data" JSON export (GDPR)
- 🔄 "Delete My Account" with confirmation (GDPR)
- 🔄 Interactive map view for bunkers
- 🔄 Photo gallery views
- 🔄 Email notifications (SMTP configuration)
- 🔄 Performance optimization (caching, indexes)
- 🔄 Security audit (OWASP checklist)

---

## 🛠️ Technology Stack

### Backend
- **Framework**: Django 5.2.7
- **Language**: Python 3.13.9
- **Database**: SQLite (development) / MySQL (production)
- **Authentication**: Custom User model with email
- **Testing**: Django TestCase (24 tests passing)

### Frontend (Planned)
- **Framework**: Django Templates / Bootstrap
- **JavaScript**: Vanilla JS / Alpine.js
- **CSS**: Tailwind CSS / Bootstrap

### Production Deployment
- **Hosting**: Cyber Folks VPS Managed (Poland)
- **Web Server**: Gunicorn + LiteSpeed
- **Database**: MySQL/MariaDB
- **SSL**: Let's Encrypt
- **Location**: Gdańsk, Poland

---

## 📁 Project Structure

```
BOTA_Project/
├── venv/                          # Python virtual environment
├── bota_project/                  # Main Django project
│   ├── __init__.py
│   ├── settings.py               # Project settings
│   ├── urls.py                   # URL configuration
│   ├── wsgi.py                   # WSGI config
│   └── asgi.py                   # ASGI config
├── accounts/                      # ✅ User authentication & statistics
│   ├── models.py                 # User, UserStatistics, UserRole
│   ├── admin.py                  # Admin configuration
│   ├── signals.py                # Auto-create UserStatistics
│   ├── tests.py                  # 24 unit tests
│   └── migrations/
├── bunkers/                       # ✅ Bunker management
│   ├── models.py                 # BunkerCategory, Bunker, BunkerPhoto, etc.
│   ├── admin.py                  # Admin with photo approval
│   ├── tests.py                  # 20 unit tests
│   └── migrations/
├── cluster/                       # ✅ Cluster management
│   ├── models.py                 # Cluster, ClusterMember, ClusterAlert
│   ├── admin.py                  # Admin with activate/deactivate
│   ├── tests.py                  # 19 unit tests
│   └── migrations/
├── activations/                   # ✅ Activation keys & licenses
│   ├── models.py                 # ActivationKey, ActivationLog, License
│   ├── admin.py                  # Admin with key generation
│   ├── tests.py                  # 26 unit tests
│   └── migrations/
├── diplomas/                      # ✅ Achievement & diploma system
│   ├── models.py                 # DiplomaType, Diploma, DiplomaProgress, DiplomaVerification
│   ├── admin.py                  # Admin with progress bars
│   ├── tests.py                  # 25 unit tests
│   └── migrations/
├── docs/                          # Documentation
│   ├── PROJECT_SPECIFICATION.md  # Complete specifications (v1.7)
│   ├── MILESTONES.md             # Project roadmap
│   ├── QUICK_REFERENCE.md        # Development commands
│   └── SESSION_SUMMARY_*.md      # Daily summaries
├── manage.py                      # Django management script
├── db.sqlite3                     # SQLite database (dev)
├── .gitignore                     # Git ignore rules
└── README.md                      # This file
```

---

## 🚀 Installation

### Prerequisites
- Python 3.13+ (recommended 3.13.9)
- pip (Python package manager)
- Virtual environment tool (venv)

### Production Deployment

📘 **For production deployment on a server, see [DEPLOYMENT.md](DEPLOYMENT.md)**

The deployment guide includes:
- Complete server setup (Ubuntu/Debian)
- PostgreSQL configuration
- Nginx + Gunicorn setup
- SSL/HTTPS with Let's Encrypt
- Automated deployment scripts
- Monitoring and backup procedures

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd BOTA_Project
```

### Step 2: Create Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

*Note: If `requirements.txt` doesn't exist yet:*
```bash
pip install Django==5.2.7
```

### Step 4: Apply Migrations
```bash
python manage.py migrate
```

### Step 5: Create Superuser
```bash
python manage.py createsuperuser --email admin@bota.com --callsign ADMIN
# Follow prompts to set password
```

---

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the project root (optional for development):

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Database Configuration
**Development**: SQLite (no configuration needed)
**Production**: MySQL/MariaDB (update `settings.py`)

```python
# For production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'bota_db',
        'USER': 'bota_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

---

## 🏃 Running the Application

### Development Server
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run development server
python manage.py runserver

# Server will start at: http://127.0.0.1:8000
```

### Access Points
- **Main Site**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/
  - Login: `admin@bota.com` (or your superuser email)
  - Password: (set during createsuperuser)

---

## 🧪 Testing

### Run All Tests
```bash
python manage.py test
```

### Run Tests for Specific App
```bash
python manage.py test accounts
```

### Run Tests with Verbosity
```bash
python manage.py test accounts --verbosity=2
```

### Test Coverage (if coverage installed)
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### Current Test Status
- ✅ **114 tests total** (24 accounts + 20 bunkers + 19 cluster + 26 activations + 25 diplomas)
- ✅ **100% pass rate**
- ✅ **Accounts tests**: User model, UserStatistics, UserRole, UserRoleAssignment
- ✅ **Bunkers tests**: BunkerCategory, Bunker, BunkerPhoto, BunkerResource, BunkerInspection
- ✅ **Cluster tests**: Cluster, ClusterMember, ClusterAlert
- ✅ **Activations tests**: ActivationKey, ActivationLog, License
- ✅ **Diplomas tests**: DiplomaType, Diploma, DiplomaProgress, DiplomaVerification

---

## 📚 Documentation

### Main Documentation Files
- **[PROJECT_SPECIFICATION.md](docs/PROJECT_SPECIFICATION.md)** - Complete project specifications (1,700+ lines)
- **[MILESTONES.md](docs/MILESTONES.md)** - Project roadmap and task tracking
- **[QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** - Development commands and shortcuts
- **[SESSION_SUMMARY_*.md](docs/)** - Daily development summaries

### Key Documentation Sections
- Custom User Model with email authentication
- User statistics and points system
- Achievement-based diploma system
- CSV import/export for bunker data
- Production hosting specifications (Cyber Folks)
- GDPR compliance and cookie policy
- Testing strategy (80%+ coverage goal)

---

## 📊 Development Status

### ✅ Phase 1: Core Setup (COMPLETED - November 3, 2025)
- [x] Django project initialization
- [x] Custom User model with email authentication
- [x] UserStatistics with points system
- [x] Role-based access control
- [x] Database migrations
- [x] Admin interface configuration
- [x] 24 unit tests (all passing)
- [x] Project documentation

### ✅ Phase 2: Bunkers App (COMPLETED - November 3, 2025)
- [x] BunkerCategory model with translations
- [x] Bunker model with GPS coordinates
- [x] BunkerPhoto model with approval workflow
- [x] BunkerResource and BunkerInspection models
- [x] Admin interface for bunkers (with inlines)
- [x] Photo approval workflow in admin
- [x] GPS coordinate validation
- [x] 20 unit tests for bunker models (all passing)

### ✅ Phase 3: Cluster App (COMPLETED - November 4, 2025)
- [x] Cluster model with translations and regions
- [x] ClusterMember through model (many-to-many)
- [x] ClusterAlert model with date-based activation
- [x] Admin interface with inlines and custom actions
- [x] Helper methods for bunker counting and filtering
- [x] 19 unit tests for cluster models (all passing)

### ✅ Phase 4: Activations App (COMPLETED - November 4, 2025)
- [x] ActivationKey model with auto-generation
- [x] ActivationLog model with QSO and B2B tracking
- [x] License model for special events
- [x] Secure key generation (no ambiguous characters)
- [x] Validation methods and usage tracking
- [x] Admin interface with custom actions
- [x] 26 unit tests for activation models (all passing)

### ✅ Phase 5: Diplomas App (COMPLETED - November 4, 2025)
- [x] DiplomaType model with bilingual fields
- [x] Diploma model with unique numbering system
- [x] DiplomaProgress model with automatic calculation
- [x] DiplomaVerification model with audit trail
- [x] Category system (hunter, activator, b2b, special_event, cluster)
- [x] Point-based requirements system (activator, hunter, B2B points)
- [x] Admin interface with visual progress bars
- [x] 25 unit tests for diploma models (all passing)

### ✅ Phase 5.1: Extended Diploma System (COMPLETED - November 5, 2025)
- [x] **Bunker count requirements** - unique and total activations/hunts
- [x] **7 requirement types** - 3 point-based + 4 bunker count-based
- [x] **Flexible diploma creation** - mix points and counts freely
- [x] **Smart progress calculation** - averages only active requirements
- [x] **Updated API serializers** - new fields in REST responses
- [x] **Enhanced templates** - display all requirement types
- [x] **Comprehensive tests** - 9 new test cases for count requirements
- [x] **Full documentation** - DIPLOMA_SYSTEM.md and IMPLEMENTATION_GUIDE.md updated

**New Diploma Types Possible:**
- **Explorer**: Activate X different bunkers (unique count)
- **Marathon**: Complete Y total activations (with repeats)
- **Versatile**: Mix of points AND counts (e.g., 50 points + 10 unique bunkers)
- **Specialist**: Any combination of 7 requirement types

### 🔄 Phase 6: REST API (NEXT)
- [ ] Django REST Framework integration
- [ ] Serializers for all models
- [ ] JWT authentication
- [ ] API documentation with drf-spectacular
- [ ] Pagination and filtering

### ⏳ Future Phases
- Phase 7: Cookie Consent & GDPR
- Phase 8: Frontend & Templates
- Phase 9: Testing & QA
- Phase 10: Deployment
- Phase 10: Production Deployment

**Current Progress**: 85% complete (Phases 1-9 ~90% complete, 299+ tests passing, user testing in progress)

---

## 👥 Contributing

### Development Workflow
1. Create a feature branch: `git checkout -b feature/your-feature`
2. Write tests for your changes
3. Ensure all tests pass: `python manage.py test`
4. Follow PEP 8 style guidelines
5. Write clear commit messages
6. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Write docstrings for all functions/classes
- Keep functions small and focused
- Write meaningful variable names
- Add comments for complex logic

### Testing Requirements
- All new features must have unit tests
- All tests must pass before merging
- Maintain 80%+ code coverage
- Test both success and error cases

---

## 📝 License

[To be determined - Add license information here]

---

## 📞 Contact & Support

- **Project Manager**: [To be assigned]
- **Lead Developer**: [To be assigned]
- **Documentation**: See `/docs/` directory
- **Issue Tracking**: [To be configured]

---

## 🙏 Acknowledgments

- Django framework and community
- Cyber Folks for hosting platform
- All contributors and testers

---

## 📅 Project Timeline

- **Project Started**: November 3, 2025
- **Phase 1 Completed**: November 3, 2025
- **Phase 2 Completed**: November 3, 2025
- **Phase 3 Completed**: November 4, 2025
- **Phase 4 Completed**: November 4, 2025
- **Phase 5 Start**: November 4, 2025
- **Estimated Completion**: January 5, 2026

---

## 🔗 Useful Links

- [Django Documentation](https://docs.djangoproject.com/)
- [Python Documentation](https://docs.python.org/)
- [Cyber Folks Hosting](https://cyberfolks.pl/)

---

*Last Updated: November 5, 2025*
*Version: 0.8.5 (Phases 1-9 ~90% Complete - Spotting System, Translations, GDPR Legal Pages)*
