# BOTA PROJECT - Complete Specification Document

## Project Overview
**BOTA Project** is a Django-based web application for managing bunkers, user accounts, activations, clusters, and diplomas/certificates. This document provides a comprehensive specification of all applications, their models, relationships, and functionality.

**Official Website**: [spbota.pl](https://spbota.pl)  
**Official Community**: Bunkers on the Air Polska - Polish community of amateur radio operators activating fortifications

---

## Branding & Design Guidelines

### Primary Website Integration
This application is designed to run on **spbota.pl** and must follow the existing website's design theme and branding:

#### Brand Identity
- **Program Name**: Bunkers on the Air Polska (SP BOTA)
- **Target Audience**: Amateur radio enthusiasts (ham radio operators) who enjoy outdoor activities and have interest in fortifications, military history, and militaria
- **Community Mission**: Connect radio communication enthusiasts with lovers of military history through fortification activation

#### Design Requirements
- **Theme Consistency**: The application must match the visual design, color scheme, and typography of the main spbota.pl website
- **Navigation Integration**: 
  - Include existing menu items: "O programie" (About), "Materiały do pobrania" (Downloads), "Kontakt" (Contact), "Mapa referencji" (Reference Map), "Zespół prowadzący" (Team)
  - Maintain the same navigation structure and user flow
- **Branding**: Use the same logo, color palette, and design elements as the main site
- **Language Tone**: 
  - Primary language: Polish (with English translations)
  - Friendly, community-focused tone
  - Use terminology familiar to ham radio operators and fortification enthusiasts
- **Responsive Design**: Follow the same mobile/tablet/desktop breakpoints and layouts as spbota.pl

#### Content Guidelines
- Use ham radio terminology (krótkofalarstwo, referencje, aktywacja)
- Maintain focus on fortifications, bunkers, and military structures
- Emphasize outdoor activity and community engagement
- Reference existing sections: RODO, Regulamin (Rules), Polityka prywatności (Privacy Policy)

#### Technical Integration
- The application should integrate with existing Google Forms for reference submissions: `https://forms.gle/r6rN2HkfjUD7XeQr5`
- Maintain compatibility with existing reference map functionality
- Follow the same URL structure and naming conventions as spbota.pl

---

## Technology Stack
- **Framework**: Django 5.2.7
- **Language**: Python 3.x
- **Database**: SQLite (development) / MySQL/MariaDB (production - Cyber Folks VPS)
- **Admin Interface**: Django Admin (customizable)
- **Internationalization**: Django i18n (Polish & English)
- **Responsive Design**: Mobile-first approach, optimized for phones and tablets
- **Image Processing**: Pillow for photo uploads and thumbnails

---

## Project Structure

```
bota_project/
├── manage.py                 # Django management script
├── bota_project/            # Main project configuration
│   ├── settings.py          # Project settings
│   ├── urls.py              # Main URL configuration
│   ├── wsgi.py              # WSGI configuration
│   └── asgi.py              # ASGI configuration
├── accounts/                # User account management
├── bunkers/                 # Bunker management system
├── cluster/                 # Cluster management
├── activations/             # Activation/license management
├── diplomas/                # Diploma/certificate system
└── docs/                    # Documentation
```

---

## Application Specifications

### 1. **ACCOUNTS APP** (`accounts/`)

#### Purpose
Manage user authentication, profiles, roles, and permissions.

#### Models

##### **User** (Custom User Model)
- **Primary Authentication Fields**:
  - `email` (EmailField, unique) - Used as username for authentication
  - `password` (CharField) - Hashed password (Django default)
  - `callsign` (CharField, max_length=50, unique) - User's callsign/display name
- **System Fields**:
  - `is_active` (BooleanField, default=True)
  - `is_staff` (BooleanField, default=False)
  - `is_superuser` (BooleanField, default=False)
  - `date_joined` (DateTimeField, auto_now_add)
  - `last_login` (DateTimeField, nullable)

**Note**: Simplified user model for regular use - only email, password, and callsign required.

##### **UserStatistics**
- **Fields**:
  - `user` (OneToOne with User)
  - **Activator Statistics**:
    - `total_activator_qso` (PositiveIntegerField, default=0) - Total QSOs from bunkers as activator
    - `unique_activations` (PositiveIntegerField, default=0) - Unique bunkers activated
    - `activator_b2b_qso` (PositiveIntegerField, default=0) - Bunker-to-Bunker QSOs as activator
  - **Hunter Statistics**:
    - `total_hunter_qso` (PositiveIntegerField, default=0) - Total hunted QSOs
    - `unique_bunkers_hunted` (PositiveIntegerField, default=0) - Unique bunkers hunted
  - **General Statistics**:
    - `total_b2b_qso` (PositiveIntegerField, default=0) - Total Bunker-to-Bunker connections
  - **Points System**:
    - `total_points` (PositiveIntegerField, default=0) - Total points earned from all activities
    - `hunter_points` (PositiveIntegerField, default=0) - Points from hunting
    - `activator_points` (PositiveIntegerField, default=0) - Points from activating
    - `b2b_points` (PositiveIntegerField, default=0) - Points from B2B connections
    - `event_points` (PositiveIntegerField, default=0) - Points from special events
    - `diploma_points` (PositiveIntegerField, default=0) - Points from earned diplomas
  - **Timestamps**:
    - `last_updated` (DateTimeField, auto_now)
    - `created_at` (DateTimeField, auto_now_add)

**Note**: Tracks user progress toward diploma achievements. Updated automatically with each QSO entry.

##### **UserRole** (Role-based access control)
- **Fields**:
  - `name` (CharField, max_length=50, unique) - e.g., 'Admin', 'Manager', 'Operator', 'Viewer'
  - `description` (TextField)
  - `permissions` (JSONField) - Custom permissions dictionary
  - `created_at` (DateTimeField, auto_now_add)

##### **UserRoleAssignment**
- **Fields**:
  - `user` (ForeignKey to User)
  - `role` (ForeignKey to UserRole)
  - `assigned_by` (ForeignKey to User)
  - `assigned_at` (DateTimeField, auto_now_add)
  - `is_active` (BooleanField, default=True)

#### Features
- Custom user registration with email (as username) and callsign
- Email-based authentication
- Role-based access control (RBAC)
- Password reset functionality
- User activity logging
- Multi-role support per user

#### Admin Features
- User list with filtering (by role, status, date joined)
- Bulk role assignment
- User activation/deactivation
- Export user data (CSV/Excel)

---

### 2. **BUNKERS APP** (`bunkers/`)

#### Purpose
Manage bunker facilities, their locations, capacities, and operational status. Support bulk import via CSV files and export for mapping applications.

#### CSV Import/Export System

##### **CSV Template Structure**
Admin-maintained template for bunker data import/export with following columns:
- `code` - Unique bunker identifier (required)
- `name` - Bunker name (required)
- `category` - Category code/name (required)
- `cluster` - Cluster code/name (optional)
- `latitude` - GPS latitude coordinate (required for mapping)
- `longitude` - GPS longitude coordinate (required for mapping)
- `location_address` - Full address (optional)
- `capacity` - Maximum occupancy (optional, default: 0)
- `status` - Operational status (optional, default: OPERATIONAL)
- `description` - Bunker description (optional)
- `construction_date` - Date in YYYY-MM-DD format (optional)
- `manager_email` - Manager's email (optional, must exist in system)

**Example CSV Template:**
```csv
code,name,category,cluster,latitude,longitude,location_address,capacity,status,description,construction_date,manager_email
BNK001,Central Fortress,Military,NORTH,52.237049,21.017532,"Warsaw, Poland",150,OPERATIONAL,"Main military facility",2020-05-15,manager@example.com
BNK002,Eastern Shelter,Civilian,EAST,51.107885,17.038538,"Wroclaw, Poland",80,OPERATIONAL,"Civilian emergency shelter",2019-03-20,
```

##### **CSV Import Features**
- **Template Download**: Admin can download current CSV template with headers
- **Bulk Import**: Upload CSV file to create/update multiple bunkers
- **Validation**: Pre-import validation with detailed error reporting
  - Check for duplicate codes
  - Verify required fields
  - Validate GPS coordinates format
  - Check category/cluster existence
  - Verify manager email exists
- **Import Preview**: Show what will be imported before confirming
- **Error Handling**: 
  - Skip invalid rows with detailed error messages
  - Continue processing valid rows
  - Generate import report (success/failed counts)
- **Update vs Create**: 
  - If `code` exists: Update existing bunker
  - If `code` is new: Create new bunker

##### **CSV Export Features**
- **Full Export**: Export all bunkers to CSV
- **Filtered Export**: Export based on filters (category, cluster, status)
- **Custom Fields**: Admin can select which columns to include
- **Export for Mapping**: Special export format for GIS/mapping tools
  - Include only active bunkers
  - Ensure coordinates are valid
  - Add additional metadata for map markers

#### Models

##### **BunkerCategory**
- **Fields**:
  - `name` (CharField, max_length=100, unique) - e.g., 'Bunker', 'Fort', 'Fortress', 'Shelter', 'Military Base', 'Observation Tower'
  - `name_pl` (CharField, max_length=100) - Polish translation of name
  - `name_en` (CharField, max_length=100) - English translation of name
  - `description` (TextField)
  - `description_pl` (TextField) - Polish description
  - `description_en` (TextField) - English description
  - `icon` (CharField, max_length=50) - Icon identifier for UI
  - `is_active` (BooleanField, default=True)
  - `display_order` (PositiveIntegerField, default=0) - Sort order for display
  - `created_by` (ForeignKey to User, nullable)
  - `created_at` (DateTimeField, auto_now_add)
  - `updated_at` (DateTimeField, auto_now)

**Note**: Admin can create custom categories for different types of military buildings and structures.

##### **Bunker**
- **Fields**:
  - `name` (CharField, max_length=200)
  - `code` (CharField, max_length=50, unique) - Unique bunker identifier
  - `category` (ForeignKey to BunkerCategory)
  - `cluster` (ForeignKey to Cluster, nullable) - Associated cluster
  - `description` (TextField, blank=True)
  - `description_pl` (TextField, blank=True) - Polish description
  - `description_en` (TextField, blank=True) - English description
  - `location_address` (TextField, blank=True)
  - `latitude` (DecimalField, max_digits=9, decimal_places=6, nullable)
  - `longitude` (DecimalField, max_digits=9, decimal_places=6, nullable)
  - `capacity` (PositiveIntegerField, default=0) - Maximum occupancy
  - `current_occupancy` (PositiveIntegerField, default=0)
  - `status` (CharField, choices=['OPERATIONAL', 'MAINTENANCE', 'INACTIVE', 'EMERGENCY'], default='OPERATIONAL')
  - `construction_date` (DateField, nullable)
  - `last_inspection_date` (DateField, nullable)
  - `next_inspection_date` (DateField, nullable)
  - `manager` (ForeignKey to User, related_name='managed_bunkers', nullable)
  - `created_by` (ForeignKey to User, related_name='created_bunkers')
  - `imported_from_csv` (BooleanField, default=False) - Track if created via CSV import
  - `created_at` (DateTimeField, auto_now_add)
  - `updated_at` (DateTimeField, auto_now)
  - `is_active` (BooleanField, default=True)

##### **BunkerPhoto**
- **Fields**:
  - `bunker` (ForeignKey to Bunker, related_name='photos')
  - `photo` (ImageField, upload_to='bunker_photos/%Y/%m/') - Bunker photograph
  - `title` (CharField, max_length=200, blank=True)
  - `title_pl` (CharField, max_length=200, blank=True) - Polish title
  - `title_en` (CharField, max_length=200, blank=True) - English title
  - `description` (TextField, blank=True)
  - `description_pl` (TextField, blank=True) - Polish description
  - `description_en` (TextField, blank=True) - English description
  - `is_primary` (BooleanField, default=False) - Mark as main photo for bunker
  - `display_order` (PositiveIntegerField, default=0) - Sort order
  - `uploaded_by` (ForeignKey to User)
  - `uploaded_at` (DateTimeField, auto_now_add)
  - `is_approved` (BooleanField, default=False) - Admin approval required
  - `approved_by` (ForeignKey to User, nullable, related_name='approved_photos')
  - `approved_at` (DateTimeField, nullable)

**Note**: Multiple photos per bunker supported. Only approved photos are publicly visible.

##### **BunkerImportLog**
- **Fields**:
  - `import_id` (UUIDField, unique) - Unique identifier for import batch
  - `file_name` (CharField, max_length=255) - Original CSV filename
  - `uploaded_by` (ForeignKey to User)
  - `uploaded_at` (DateTimeField, auto_now_add)
  - `total_rows` (PositiveIntegerField) - Total rows in CSV
  - `successful_imports` (PositiveIntegerField, default=0)
  - `failed_imports` (PositiveIntegerField, default=0)
  - `updated_bunkers` (PositiveIntegerField, default=0)
  - `created_bunkers` (PositiveIntegerField, default=0)
  - `status` (CharField, choices=['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'])
  - `error_log` (TextField, blank=True) - Detailed error messages
  - `success_log` (TextField, blank=True) - Success details
  - `processing_time` (DurationField, nullable) - Time taken to process

##### **CSVTemplate**
- **Fields**:
  - `name` (CharField, max_length=100) - Template name (e.g., "Bunker Import Template v2")
  - `template_type` (CharField, choices=['BUNKER_IMPORT', 'BUNKER_EXPORT', 'MAPPING_EXPORT'])
  - `description` (TextField)
  - `field_mapping` (JSONField) - Column names and their mapping to model fields
  - `required_fields` (JSONField) - List of required columns
  - `optional_fields` (JSONField) - List of optional columns
  - `sample_data` (JSONField, nullable) - Sample rows for template generation
  - `is_active` (BooleanField, default=True)
  - `created_by` (ForeignKey to User)
  - `created_at` (DateTimeField, auto_now_add)
  - `updated_at` (DateTimeField, auto_now)

**Note**: Admin can create multiple template versions for different purposes (standard import, mapping export, etc.)

##### **BunkerResource**
- **Fields**:
  - `bunker` (ForeignKey to Bunker)
  - `resource_type` (CharField, choices=['WATER', 'FOOD', 'MEDICAL', 'FUEL', 'POWER', 'OTHER'])
  - `resource_name` (CharField, max_length=100)
  - `quantity` (DecimalField, max_digits=10, decimal_places=2)
  - `unit` (CharField, max_length=50) - e.g., 'liters', 'kg', 'units'
  - `minimum_threshold` (DecimalField) - Alert threshold
  - `last_updated` (DateTimeField, auto_now)
  - `updated_by` (ForeignKey to User)

##### **BunkerInspection**
- **Fields**:
  - `bunker` (ForeignKey to Bunker)
  - `inspector` (ForeignKey to User)
  - `inspection_date` (DateField)
  - `inspection_type` (CharField, choices=['ROUTINE', 'EMERGENCY', 'MAINTENANCE', 'SAFETY'])
  - `status` (CharField, choices=['PASSED', 'FAILED', 'NEEDS_ATTENTION'])
  - `notes` (TextField)
  - `issues_found` (TextField, nullable)
  - `recommendations` (TextField, nullable)
  - `next_inspection_date` (DateField)
  - `created_at` (DateTimeField, auto_now_add)

#### Features
- Bunker CRUD operations
- Real-time occupancy tracking
- GPS location mapping integration
- Resource inventory management
- Inspection scheduling and tracking
- Status change notifications
- Search and filter by location, category, status
- Capacity utilization analytics
- Maintenance scheduling
- **Multi-language support** (Polish/English) for names and descriptions
- **Photo gallery** - Multiple photos per bunker with approval workflow
- **Bulk CSV import/export**
- **Map data generation**
- **Responsive mobile-friendly interface**

#### Admin Features
- Bunker list with advanced filtering
- Bulk status updates
- Resource level alerts
- Inspection report generation
- **Category Management**:
  - Create custom bunker/building categories (Fort, Fortress, Shelter, Tower, etc.)
  - Manage category translations (Polish/English)
  - Set category display order and icons
  - Activate/deactivate categories
- **Photo Management**:
  - Upload multiple photos per bunker
  - Set primary/featured photo
  - Approve/reject user-submitted photos
  - Manage photo gallery order
  - Bulk photo operations
  - Add translated titles and descriptions
- **Translation Management**:
  - Edit Polish and English translations for all content
  - Translate bunker descriptions, categories, and photo captions
- **CSV Template Management**:
  - Download CSV import template
  - Customize template fields
  - Generate sample CSV with test data
- **CSV Import**:
  - Upload CSV file for bulk bunker creation/update
  - Pre-import validation and preview
  - Import with error handling and reporting
  - View import history and logs
- **CSV Export**:
  - Export all bunkers to CSV
  - Export filtered bunkers
  - Custom field selection for export
  - Export formats: Standard CSV, Mapping CSV (GIS-ready)
- **Mapping Data**:
  - Generate map-ready data files (GeoJSON, KML)
  - Export coordinates for external mapping tools
  - Preview bunkers on integrated map
- Export bunker data (CSV/Excel/PDF)
- Map view of all bunkers (mobile-responsive)

---

### 3. **CLUSTER APP** (`cluster/`)

#### Purpose
Manage groups/clusters of bunkers for organizational and operational purposes.

#### Models

##### **Cluster**
- **Fields**:
  - `name` (CharField, max_length=200)
  - `code` (CharField, max_length=50, unique)
  - `description` (TextField)
  - `region` (CharField, max_length=100) - Geographic region
  - `manager` (ForeignKey to User, related_name='managed_clusters')
  - `total_capacity` (PositiveIntegerField) - Sum of all bunkers
  - `current_total_occupancy` (PositiveIntegerField, default=0)
  - `headquarters_location` (TextField, nullable)
  - `emergency_contact` (CharField, max_length=100)
  - `status` (CharField, choices=['ACTIVE', 'INACTIVE', 'PLANNING'])
  - `created_by` (ForeignKey to User)
  - `created_at` (DateTimeField, auto_now_add)
  - `updated_at` (DateTimeField, auto_now)
  - `is_active` (BooleanField, default=True)

##### **ClusterMember** (Many-to-Many through model)
- **Fields**:
  - `cluster` (ForeignKey to Cluster)
  - `bunker` (ForeignKey to Bunker)
  - `joined_date` (DateField)
  - `role` (CharField, choices=['PRIMARY', 'SECONDARY', 'BACKUP'])
  - `priority` (PositiveIntegerField) - Order of activation
  - `is_active` (BooleanField, default=True)

##### **ClusterAlert**
- **Fields**:
  - `cluster` (ForeignKey to Cluster)
  - `alert_type` (CharField, choices=['CAPACITY', 'EMERGENCY', 'MAINTENANCE', 'SYSTEM'])
  - `severity` (CharField, choices=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
  - `message` (TextField)
  - `created_at` (DateTimeField, auto_now_add)
  - `acknowledged_by` (ForeignKey to User, nullable)
  - `acknowledged_at` (DateTimeField, nullable)
  - `resolved` (BooleanField, default=False)
  - `resolved_at` (DateTimeField, nullable)

#### Features
- Cluster CRUD operations
- Bunker grouping and management
- Cluster-wide statistics and analytics
- Alert management system
- Hierarchical cluster organization
- Resource aggregation across cluster
- Emergency coordination
- Multi-level access control

#### Admin Features
- Cluster dashboard with metrics
- Bunker assignment to clusters
- Alert management and notifications
- Capacity planning tools
- Export cluster reports

---

### 4. **ACTIVATIONS APP** (`activations/`)

#### Purpose
Manage activation keys, licenses, and access permissions for bunkers and systems.

#### Models

##### **ActivationKey**
- **Fields**:
  - `key` (CharField, max_length=100, unique) - Generated activation key
  - `key_type` (CharField, choices=['BUNKER_ACCESS', 'SYSTEM_LICENSE', 'FEATURE_UNLOCK', 'ADMIN_ACCESS'])
  - `bunker` (ForeignKey to Bunker, nullable) - If bunker-specific
  - `cluster` (ForeignKey to Cluster, nullable) - If cluster-specific
  - `user` (ForeignKey to User, nullable) - Assigned user
  - `issued_by` (ForeignKey to User, related_name='issued_keys')
  - `issued_at` (DateTimeField, auto_now_add)
  - `valid_from` (DateTimeField)
  - `valid_until` (DateTimeField, nullable) - Null for permanent keys
  - `max_uses` (PositiveIntegerField, nullable) - Null for unlimited
  - `current_uses` (PositiveIntegerField, default=0)
  - `status` (CharField, choices=['ACTIVE', 'INACTIVE', 'EXPIRED', 'REVOKED', 'SUSPENDED'])
  - `notes` (TextField, nullable)
  - `created_at` (DateTimeField, auto_now_add)
  - `updated_at` (DateTimeField, auto_now)

##### **ActivationLog**
- **Fields**:
  - `activation_key` (ForeignKey to ActivationKey)
  - `user` (ForeignKey to User) - Hunter user (who made the QSO)
  - `activator` (ForeignKey to User, related_name='activator_logs', nullable) - Activator user (added for ADIF import)
  - `action` (CharField, choices=['ACTIVATED', 'USED', 'REVOKED', 'EXPIRED', 'RENEWED'])
  - `mode` (CharField, max_length=20, blank=True) - Radio mode (SSB, CW, FM, etc.) for ADIF logs
  - `band` (CharField, max_length=20, blank=True) - Radio band (40m, 20m, etc.) for ADIF logs
  - `ip_address` (GenericIPAddressField, nullable)
  - `device_info` (TextField, nullable)
  - `location` (CharField, max_length=200, nullable)
  - `success` (BooleanField, default=True)
  - `error_message` (TextField, nullable)
  - `timestamp` (DateTimeField, auto_now_add)

**Note**: Extended with ADIF log import fields (activator, mode, band) to support amateur radio log uploads.

##### **License**
- **Fields**:
  - `license_name` (CharField, max_length=200)
  - `license_key` (CharField, max_length=200, unique)
  - `license_type` (CharField, choices=['TRIAL', 'BASIC', 'PROFESSIONAL', 'ENTERPRISE'])
  - `organization` (CharField, max_length=200, nullable)
  - `contact_email` (EmailField)
  - `issued_at` (DateTimeField, auto_now_add)
  - `valid_from` (DateField)
  - `valid_until` (DateField)
  - `max_bunkers` (PositiveIntegerField) - Maximum bunkers allowed
  - `max_users` (PositiveIntegerField) - Maximum users allowed
  - `features` (JSONField) - List of enabled features
  - `status` (CharField, choices=['ACTIVE', 'EXPIRED', 'SUSPENDED', 'CANCELLED'])
  - `created_by` (ForeignKey to User)
  - `created_at` (DateTimeField, auto_now_add)
  - `updated_at` (DateTimeField, auto_now)

#### Features
- Activation key generation (UUID/custom format)
- Key validation and verification
- Usage tracking and limits
- Automatic expiration handling
- Key revocation and suspension
- License management
- Activity logging and audit trail
- Bulk key generation
- Email notifications for expiring keys
- **ADIF Log Import System**:
  - Upload .adi log files (ADIF 3.1.5 format)
  - Parse amateur radio QSO logs
  - Extract bunker references (B/SP-xxxx format)
  - Identify activator and hunter callsigns
  - Auto-create placeholder hunter accounts
  - Award points to activators and hunters
  - Track B2B (bunker-to-bunker) connections
  - Record radio mode and band for each QSO
  - Update UserStatistics automatically
  - Security: Users can only upload their own logs
  - UTC time display in API responses

#### Admin Features
- Key management dashboard
- Usage analytics
- Bulk key operations (generate, revoke, extend)
- License overview and renewal
- Export activation logs
- Alert system for expiring licenses

---

### 5. **DIPLOMAS APP** (`diplomas/`)

#### Purpose
Manage achievement-based diplomas for Hunters, Activators, and Bunker-to-Bunker connections. Track user progress and award diplomas based on activity milestones.

#### Diploma Categories
Users can earn diplomas in four main categories:
1. **HUNTER** - For hunting bunker activations
2. **ACTIVATOR** - For activating bunkers
3. **BUNKER_TO_BUNKER** - For bunker-to-bunker connections
4. **SPECIAL_EVENT** - For time-limited events and special achievements

#### Points System
Users earn points from various activities:
- QSO completions (configurable points per QSO)
- Unique bunker activations/hunting
- B2B connections
- Earning diplomas (each diploma awards points)
- Special event participation

Points can be used as requirements for advanced diplomas (e.g., "Master Hunter" requires 10,000 points)

#### Models

##### **DiplomaType**
- **Fields**:
  - `name` (CharField, max_length=200) - e.g., "Hunter Bronze", "Activator Silver", "Summer Contest 2025"
  - `code` (CharField, max_length=50, unique) - e.g., "HUNTER_BRONZE", "ACTIVATOR_GOLD", "EVENT_SUMMER_2025"
  - `category` (CharField, choices=['HUNTER', 'ACTIVATOR', 'BUNKER_TO_BUNKER', 'SPECIAL_EVENT'])
  - `level` (PositiveIntegerField, nullable) - Diploma level (1=Bronze, 2=Silver, 3=Gold, etc.) - Not used for special events
  - `description` (TextField)
  - `requirement_type` (CharField, choices=['TOTAL_QSO', 'UNIQUE_BUNKERS', 'B2B_QSO', 'POINTS', 'EVENT_ACTIVATION', 'EVENT_HUNTING', 'CUSTOM'])
  - `requirement_value` (PositiveIntegerField) - Threshold to achieve this diploma (or points required)
  - `points_awarded` (PositiveIntegerField) - Points awarded for earning this diploma
  - `is_special_event` (BooleanField, default=False) - Mark as special event diploma
  - `event_start_date` (DateTimeField, nullable) - For special event diplomas
  - `event_end_date` (DateTimeField, nullable) - For special event diplomas
  - `event_description` (TextField, nullable) - Special event details
  - `specific_bunkers` (ManyToMany to Bunker, blank=True) - Required bunkers for special events
  - `badge_image` (ImageField, upload_to='diploma_badges/', nullable)
  - `template_file` (FileField, upload_to='diploma_templates/', nullable) - PDF/Image template
  - `template_callsign_x` (PositiveIntegerField, nullable) - X coordinate for callsign placement
  - `template_callsign_y` (PositiveIntegerField, nullable) - Y coordinate for callsign placement
  - `template_date_x` (PositiveIntegerField, nullable) - X coordinate for date placement
  - `template_date_y` (PositiveIntegerField, nullable) - Y coordinate for date placement
  - `template_font_size` (PositiveIntegerField, default=24) - Font size for text
  - `template_font_name` (CharField, max_length=50, default='Helvetica') - Font name
  - `is_active` (BooleanField, default=True)
  - `created_by` (ForeignKey to User, related_name='created_diploma_types')
  - `created_at` (DateTimeField, auto_now_add)
  - `updated_at` (DateTimeField, auto_now)

**Examples**:
- Hunter diploma based on total hunted QSOs: requirement_type='TOTAL_QSO', requirement_value=100
- Activator diploma based on unique bunkers: requirement_type='UNIQUE_BUNKERS', requirement_value=50
- B2B diploma based on B2B connections: requirement_type='B2B_QSO', requirement_value=25

**Template Placeholders**:
Admin users can upload diploma templates and define positions where dynamic data will be placed:
- `{CALLSIGN}` - User's callsign
- `{DATE}` - Date when diploma was earned
- `{CERTIFICATE_NUMBER}` - Unique certificate number
- `{ACHIEVEMENT_VALUE}` - The value achieved (e.g., "150 QSOs")

##### **Diploma**
- **Fields**:
  - `certificate_number` (CharField, max_length=100, unique)
  - `user` (ForeignKey to User, related_name='diplomas')
  - `diploma_type` (ForeignKey to DiplomaType)
  - `achievement_value` (PositiveIntegerField) - The actual value when diploma was earned
  - `earned_date` (DateTimeField, auto_now_add) - When achievement was reached
  - `generated_date` (DateTimeField, nullable) - When PDF was generated by user
  - `certificate_file` (FileField, upload_to='diplomas/', nullable) - Generated PDF certificate
  - `qr_code` (ImageField, upload_to='diploma_qr/', nullable) - For verification
  - `verification_code` (CharField, max_length=100, unique)
  - `generation_count` (PositiveIntegerField, default=0) - Times user downloaded this diploma
  - `status` (CharField, choices=['VALID', 'REVOKED'], default='VALID')
  - `notes` (TextField, nullable)
  - `created_at` (DateTimeField, auto_now_add)

**Note**: Diplomas are automatically created (earned) when user reaches the requirement threshold. PDF generation happens on-demand when user clicks "Get Diploma" button.

##### **DiplomaProgress**
- **Fields**:
  - `user` (ForeignKey to User, related_name='diploma_progress')
  - `diploma_type` (ForeignKey to DiplomaType)
  - `current_value` (PositiveIntegerField, default=0) - Current achievement count
  - `required_value` (PositiveIntegerField) - Target value (from DiplomaType)
  - `percentage_complete` (DecimalField, max_digits=5, decimal_places=2, default=0.00) - Progress percentage
  - `is_achieved` (BooleanField, default=False)
  - `achieved_at` (DateTimeField, nullable)
  - `diploma` (ForeignKey to Diploma, nullable) - Linked when achieved
  - `last_updated` (DateTimeField, auto_now)
  - `created_at` (DateTimeField, auto_now_add)

**Note**: Automatically tracks progress toward each diploma. Updated with each QSO. Percentage = (current_value / required_value) * 100

##### **DiplomaVerification**
- **Fields**:
  - `diploma` (ForeignKey to Diploma)
  - `verified_by` (ForeignKey to User, nullable) - If verified by user
  - `verification_date` (DateTimeField, auto_now_add)
  - `verification_method` (CharField, choices=['QR_CODE', 'CERTIFICATE_NUMBER', 'MANUAL', 'API'])
  - `ip_address` (GenericIPAddressField, nullable)
  - `result` (CharField, choices=['VALID', 'INVALID', 'EXPIRED', 'REVOKED'])
  - `notes` (TextField, nullable)

#### Diploma Achievement Criteria

##### **ACTIVATOR Diplomas**
1. **Total QSO from Bunkers** - Based on `total_activator_qso`
   - Example levels: Bronze (100), Silver (250), Gold (500), Platinum (1000)
2. **Unique Activations** - Based on `unique_activations` (unique bunkers activated)
   - Example levels: Bronze (10), Silver (25), Gold (50), Platinum (100)
3. **Bunker-to-Bunker** - Based on `activator_b2b_qso`
   - Example levels: Bronze (25), Silver (50), Gold (100), Platinum (250)

##### **HUNTER Diplomas**
1. **Total Hunted QSO** - Based on `total_hunter_qso`
   - Example levels: Bronze (100), Silver (250), Gold (500), Platinum (1000)
2. **Unique Bunkers Hunted** - Based on `unique_bunkers_hunted`
   - Example levels: Bronze (10), Silver (25), Gold (50), Platinum (100)

##### **BUNKER_TO_BUNKER Diplomas**
##### **B2B Connections** - Based on `total_b2b_qso`
   - Example levels: Bronze (50), Silver (100), Gold (250), Platinum (500)

##### **POINTS-BASED Diplomas**
1. **Total Points** - Based on `total_points` accumulated
   - Example levels: Bronze (1,000 pts), Silver (5,000 pts), Gold (10,000 pts), Diamond (25,000 pts)
2. **Category-Specific Points** - Based on specific point categories
   - Hunter Master (10,000 hunter_points)
   - Activator Master (10,000 activator_points)

##### **SPECIAL EVENT Diplomas**
Custom diplomas for special occasions, contests, or campaigns:

1. **Time-Limited Event Diplomas**:
   - **Event Activation**: Activate bunkers during specific date range
     - Example: "Summer Bunker Fest 2025" - Activate 10 unique bunkers between June 1-30
   - **Event Hunting**: Hunt bunkers during specific date range
     - Example: "Winter Hunt 2025" - Hunt 50 QSOs between Dec 1-31
   - **Combined Requirements**: Multiple criteria during event period
     - Example: "Anniversary Contest" - 100 QSOs + 5 unique bunkers + 10 B2B during event week

2. **Special Bunker Diplomas**:
   - Activate/Hunt specific bunkers (historical, rare, or special significance)
   - Example: "Fortress Five" - Activate all 5 designated fortress bunkers

3. **Custom Challenge Diplomas**:
   - Admin-defined custom requirements
   - Example: "Night Operator" - 100 QSOs between 22:00-06:00 UTC

#### Diploma Template System

##### **Template Creation Workflow (Admin Users)**
1. **Upload Template**: Admin uploads a base diploma template (PDF or high-res image)
2. **Define Placeholders**: Admin specifies X/Y coordinates for:
   - Callsign placement
   - Date placement
   - Certificate number placement (optional)
   - Achievement value placement (optional)
3. **Configure Font**: Set font name, size, and color for overlayed text
4. **Test Generation**: Admin can generate a test diploma with sample data to verify positioning
5. **Activate Template**: Once satisfied, set diploma type as active

##### **Template Placement Tools (Admin Panel)**
- Visual template editor with coordinate picker
- Preview mode showing template with placeholder positions
- "Generate Test Diploma" button to create sample with:
  - Test callsign (e.g., "TEST123")
  - Current date
  - Sample certificate number
  - Sample achievement value
- Save coordinates and font settings

##### **Diploma Generation Workflow (Users)**
1. **View Earned Diplomas**: User sees list of earned diplomas in profile
2. **Request Diploma**: User clicks "Get Diploma" button next to earned diploma
3. **Generate PDF**: System generates PDF by:
   - Taking diploma template
   - Overlaying user's callsign at defined position
   - Overlaying earned date at defined position
   - Adding certificate number
   - Adding QR code for verification
4. **Download**: User receives generated PDF file
5. **Regeneration**: User can regenerate diploma multiple times if needed

#### Features
- Automatic diploma awarding based on achievements (earned status only)
- On-demand PDF generation (not pre-generated)
- Real-time progress tracking with percentage completion
- Multiple diploma categories (Hunter, Activator, B2B)
- Level-based progression system
- Customizable PDF certificate generation with admin-defined templates
- Coordinate-based text placement on templates
- QR code generation for verification
- Online verification system
- User statistics dashboard showing progress to next levels
- Achievement history tracking
- Points system for gamification
- Generation tracking (count how many times user downloaded)
- Digital signature integration

#### Admin Features
- **Diploma Template Management**:
  - Upload diploma templates (PDF/Image)
  - Visual coordinate picker for text placement
  - Font and style configuration
  - Test diploma generation with sample data
  - Template preview with placeholder positions
- **Diploma Type Management**: 
  - Create standard diplomas with levels (Bronze, Silver, Gold, etc.)
  - Define point requirements for advanced diplomas
  - Create special event diplomas with date ranges
  - Set specific bunker requirements for special events
  - Configure points awarded for each diploma
  - Set achievement thresholds (QSO count, unique bunkers, points, etc.)
  - Activate/deactivate diplomas
  - Duplicate existing diplomas for quick creation
- **Special Event Management**:
  - Create time-limited event diplomas
  - Set event start and end dates
  - Define event-specific requirements (activation/hunting in date range)
  - Assign specific bunkers for event challenges
  - Monitor event participation in real-time
  - Auto-award diplomas when event ends
- **Points System Management**:
  - Configure point values for different activities
  - View user point leaderboards
  - Manually adjust points if needed
  - Export points history
- **User Achievement Overview**: See all users' earned diplomas
- **Manual Diploma Issuance** (if needed for special cases)
- **Verification Portal**: Public diploma verification
- **Analytics**: 
  - Most earned diplomas
  - User rankings by points/achievements
  - Download statistics
  - Event participation rates
  - Diploma completion rates by level
- **Export Certificates and Reports**
- **Revocation Management**: Revoke diplomas if needed
- **Progress Monitoring**: Track all users' progress
- **Template Version Control**: Keep history of template changes

---

## Database Relationships

### Primary Relationships
1. **User → UserStatistics** (One-to-One) - User activity statistics and points
2. **User → UserRoleAssignment** (One-to-Many)
3. **UserRole → UserRoleAssignment** (One-to-Many)
4. **Cluster → Bunker** (One-to-Many)
5. **BunkerCategory → Bunker** (One-to-Many)
6. **Bunker → BunkerResource** (One-to-Many)
7. **Bunker → BunkerInspection** (One-to-Many)
8. **Bunker → BunkerPhoto** (One-to-Many) - Photo gallery
9. **User → BunkerImportLog** (One-to-Many) - Track CSV imports
10. **User → BunkerPhoto** (uploaded_by) (One-to-Many) - Track photo uploads
11. **User → CSVTemplate** (One-to-Many) - Template creators
12. **Cluster → ClusterMember → Bunker** (Many-to-Many through)
13. **Cluster → ClusterAlert** (One-to-Many)
14. **ActivationKey → ActivationLog** (One-to-Many)
15. **ActivationKey → Bunker** (Many-to-One, optional)
16. **ActivationKey → Cluster** (Many-to-One, optional)
17. **User → Diploma** (One-to-Many) - Earned diplomas
18. **DiplomaType → Diploma** (One-to-Many)
19. **DiplomaType → Bunker** (Many-to-Many) - For special event bunker requirements
20. **User → DiplomaProgress** (One-to-Many) - Progress tracking for each diploma type
21. **DiplomaType → DiplomaProgress** (One-to-Many)
22. **DiplomaProgress → Diploma** (One-to-One) - When achieved
23. **Diploma → DiplomaVerification** (One-to-Many)

---

## API Endpoints (REST API - Future Implementation)

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/password-reset/` - Password reset request
- `POST /api/auth/password-reset-confirm/` - Confirm password reset

### Accounts
- `GET /api/accounts/profile/` - Get current user profile
- `PUT /api/accounts/profile/` - Update user profile
- `GET /api/accounts/statistics/` - Get current user statistics
- `GET /api/accounts/users/` - List users (admin)
- `GET /api/accounts/users/{id}/` - Get user details
- `GET /api/accounts/users/{id}/statistics/` - Get user statistics
- `POST /api/accounts/users/` - Create user (admin)
- `PUT /api/accounts/users/{id}/` - Update user (admin)
- `DELETE /api/accounts/users/{id}/` - Delete user (admin)

### Bunkers
- `GET /api/bunkers/` - List bunkers (with language parameter)
- `POST /api/bunkers/` - Create bunker
- `GET /api/bunkers/{id}/` - Get bunker details
- `PUT /api/bunkers/{id}/` - Update bunker
- `DELETE /api/bunkers/{id}/` - Delete bunker
- `GET /api/bunkers/{id}/resources/` - Get bunker resources
- `POST /api/bunkers/{id}/inspections/` - Create inspection
- `GET /api/bunkers/{id}/occupancy/` - Get occupancy stats
- `GET /api/bunkers/{id}/photos/` - Get bunker photos (approved only)
- `POST /api/bunkers/{id}/photos/upload/` - Upload photo (requires approval)
- `GET /api/bunkers/categories/` - List bunker categories
- `GET /api/bunkers/export/csv/` - Export bunkers to CSV
- `GET /api/bunkers/export/geojson/` - Export bunkers as GeoJSON for mapping
- `GET /api/bunkers/map-data/` - Get map-ready bunker data

#### Admin-Only Bunker Endpoints
- `GET /api/admin/bunkers/csv-template/` - Download CSV import template
- `POST /api/admin/bunkers/csv-validate/` - Validate CSV file before import
- `POST /api/admin/bunkers/csv-import/` - Import bunkers from CSV file
- `GET /api/admin/bunkers/csv-import-history/` - View CSV import history and logs
- `POST /api/admin/bunkers/csv-export/` - Export bunkers with custom fields
- `GET /api/admin/bunkers/generate-sample-csv/` - Generate sample CSV with test data
- `POST /api/admin/bunkers/categories/` - Create bunker category
- `PUT /api/admin/bunkers/categories/{id}/` - Update category with translations
- `DELETE /api/admin/bunkers/categories/{id}/` - Delete category
- `GET /api/admin/bunkers/photos/pending/` - List photos pending approval
- `POST /api/admin/bunkers/photos/{id}/approve/` - Approve photo
- `POST /api/admin/bunkers/photos/{id}/reject/` - Reject/delete photo
- `PUT /api/admin/bunkers/photos/{id}/set-primary/` - Set as primary photo
- `POST /api/admin/bunkers/{id}/photos/bulk-upload/` - Upload multiple photos

### Clusters
- `GET /api/clusters/` - List clusters
- `POST /api/clusters/` - Create cluster
- `GET /api/clusters/{id}/` - Get cluster details
- `PUT /api/clusters/{id}/` - Update cluster
- `DELETE /api/clusters/{id}/` - Delete cluster
- `GET /api/clusters/{id}/bunkers/` - Get cluster bunkers
- `POST /api/clusters/{id}/alerts/` - Create alert
- `GET /api/clusters/{id}/statistics/` - Get cluster stats

### Activations
- `GET /api/activations/keys/` - List activation keys
- `POST /api/activations/keys/` - Generate activation key
- `GET /api/activations/keys/{key}/` - Validate key
- `POST /api/activations/keys/{key}/activate/` - Activate key
- `PUT /api/activations/keys/{key}/revoke/` - Revoke key
- `GET /api/activations/licenses/` - List licenses
- `POST /api/activations/licenses/` - Create license
- `GET /api/activations/logs/` - Get activation logs
- `POST /api/activation-logs/upload_adif/` - **Upload ADIF log file** (.adi format)
  - **Multipart file upload** (activator uploads their activation logs)
  - **Validates**: Bunker ID format (B/SP-xxxx), ADIF structure, activator callsign
  - **Processes**: Extracts QSOs, creates hunter accounts, awards points
  - **Returns**: QSO count, processing summary, warnings
  - **Security**: User can only upload logs with their own callsign
  - **Fields extracted**: CALL, MY_SIG_INFO, QSO_DATE, TIME_ON, MODE, BAND, OPERATOR/STATION_CALLSIGN

### Diplomas
- `GET /api/diplomas/` - List user's earned diplomas with generation status
- `GET /api/diplomas/my-diplomas/` - Get current user's diplomas
- `GET /api/diplomas/{id}/` - Get diploma details
- `POST /api/diplomas/{id}/generate/` - Generate/download PDF certificate
- `GET /api/diplomas/{id}/download/` - Download previously generated certificate
- `GET /api/diplomas/{id}/verify/` - Verify diploma authenticity
- `GET /api/diplomas/verify/{code}/` - Verify by code/certificate number
- `GET /api/diplomas/types/` - List all diploma types and levels
- `GET /api/diplomas/types/{category}/` - Get diploma types by category (hunter/activator/b2b)
- `GET /api/diplomas/progress/` - Get current user's progress toward all diplomas
- `GET /api/diplomas/progress/{diploma_type_id}/` - Get progress for specific diploma type
- `GET /api/diplomas/leaderboard/` - Get user rankings by achievements
- `GET /api/diplomas/leaderboard/{category}/` - Get rankings by category

#### Admin-Only Endpoints
- `POST /api/admin/diplomas/types/` - Create new diploma type (standard or event)
- `POST /api/admin/diplomas/types/duplicate/{id}/` - Duplicate existing diploma type
- `PUT /api/admin/diplomas/types/{id}/` - Update diploma type
- `POST /api/admin/diplomas/types/{id}/upload-template/` - Upload diploma template
- `PUT /api/admin/diplomas/types/{id}/set-coordinates/` - Set text placement coordinates
- `POST /api/admin/diplomas/types/{id}/test-generate/` - Generate test diploma with sample data
- `GET /api/admin/diplomas/types/{id}/preview/` - Preview template with placeholders
- `DELETE /api/admin/diplomas/types/{id}/` - Delete diploma type (if no diplomas earned)
- `POST /api/admin/diplomas/{id}/revoke/` - Revoke a diploma
- `GET /api/admin/diplomas/statistics/` - Get generation statistics
- `GET /api/admin/diplomas/events/` - List all special event diplomas
- `GET /api/admin/diplomas/events/{id}/participants/` - Get event participation data
- `POST /api/admin/diplomas/events/{id}/end/` - Manually end event and process awards
- `GET /api/admin/points/configuration/` - Get points system configuration
- `PUT /api/admin/points/configuration/` - Update points system configuration
- `POST /api/admin/points/adjust/` - Manually adjust user points
- `GET /api/admin/points/leaderboard/` - Get points leaderboard

---

## Security & Permissions

### Permission Levels
1. **Super Admin** - Full system access
2. **Admin** - Manage users, bunkers, clusters, diplomas
3. **Manager** - Manage assigned bunkers/clusters
4. **Operator** - View and update assigned bunkers
5. **Viewer** - Read-only access
6. **User** - Access own profile and assigned resources

### Security Features
- JWT/Token-based authentication (DRF)
- Role-based access control (RBAC)
- Object-level permissions
- API rate limiting
- Activity logging and audit trail
- Secure password storage (Django default)
- HTTPS enforcement (production)
- CSRF protection
- Input validation and sanitization

---

## Internationalization & Localization (i18n/l10n)

### Supported Languages
- **English (en)** - Default language
- **Polish (pl)** - Primary target language

### Language Detection Strategy
1. **IP-based Geolocation** (Primary):
   - Use GeoIP2 database to detect user's country
   - Automatically set Polish for Poland-based IPs
   - Default to English for other countries
2. **Manual Language Selection** (Override):
   - User can manually switch language via UI selector
   - Choice stored in session/cookie
   - Persists across visits
3. **Browser Language** (Fallback):
   - Check Accept-Language header if GeoIP unavailable

### Translatable Content
- **Database Content**:
  - Bunker categories (names and descriptions)
  - Bunker descriptions
  - Photo titles and captions
  - Diploma names and descriptions
  - System messages and labels
- **Static Content**:
  - UI labels and buttons
  - Form fields and placeholders
  - Error messages and validations
  - Help text and tooltips
  - Email templates

### Implementation
- Use Django's built-in i18n framework
- Use django-modeltranslation for model field translations
- Translation files: locale/pl/LC_MESSAGES/django.po
- Admin interface for managing translations
- API supports `?lang=pl` or `?lang=en` parameter

## Mobile Responsiveness

### Design Philosophy
- **Mobile-First Approach**: Design for small screens first, scale up
- **Touch-Friendly**: Large buttons, appropriate spacing for touch targets
- **Optimized Performance**: Fast loading on mobile networks

### Responsive Features
- **Adaptive Layouts**:
  - Single-column layouts on phones
  - Multi-column on tablets and desktops
  - Collapsible navigation menus
  - Bottom navigation bar for mobile
- **Optimized Images**:
  - Automatic thumbnail generation
  - Responsive image serving (different sizes for different screens)
  - Lazy loading for photos
  - WebP format support for better compression
- **Touch Interactions**:
  - Swipe gestures for photo galleries
  - Pull-to-refresh on lists
  - Touch-friendly map controls
  - Mobile-optimized forms
- **Mobile-Specific Features**:
  - GPS location detection
  - Camera integration for photo uploads
  - Offline capability (PWA)
  - Installation as home screen app

### Breakpoints
- **Mobile**: < 768px (phones)
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

### Testing
- Test on multiple devices (iOS, Android)
- Chrome DevTools responsive mode
- Real device testing for critical features

## Additional Features to Implement

### Notifications
- Email notifications (activation expiry, inspection due, alerts)
- In-app notifications
- SMS integration (optional)
- Push notifications (mobile app/PWA)
- Multi-language notification templates

### Reporting
- Custom report builder
- Scheduled reports
- Export formats: PDF, Excel, CSV
- Graphical dashboards
- Mobile-friendly report viewing

### Integration
- GIS/Mapping integration (Google Maps, OpenStreetMap)
- QR code generation and scanning
- Email service integration (SendGrid, Mailgun)
- External API integration capabilities
- GeoIP database for location detection

### Mobile App Support
- RESTful API (Django REST Framework)
- Mobile-responsive admin interface
- Progressive Web App (PWA) support
- Native mobile app potential (React Native/Flutter)

---

## Development Roadmap

### Phase 1: Core Setup (Week 1-2)
- [x] Project initialization
- [x] Project specification document created
- [x] Configure internationalization (i18n)
- [x] Create custom User model (email, password, callsign only)
- [x] Create UserStatistics model (track activator/hunter stats + points system)
- [x] Configure settings for email authentication
- [x] Update accounts app models (UserRole, UserRoleAssignment)
- [x] Create bunker app models
- [x] Create cluster and activations app models
- [x] Create diploma models
- [x] Generate and run migrations
- [x] Configure Django admin for all models
- [x] Create superuser account

### Phase 2: Admin Interface (Week 3-4)
- [x] Customize Django admin for each app
- [x] Add inline editing
- [x] Create custom admin actions
- [x] Add filters, search, and sorting
- [x] Implement list displays

### Phase 3: Business Logic (Week 5-6)
- [x] Implement model methods and properties
- [x] Create signals for automatic updates
- [x] Add validation logic
- [x] Implement permissions and access control
- [x] Create management commands

### Phase 4: REST API (Week 7-9)
- [x] Install Django REST Framework
- [x] Create serializers for all models
- [x] Create viewsets and routers
- [x] Implement authentication (JWT)
- [x] Add pagination and filtering
- [x] Write API tests

### Phase 5: Frontend (Week 10-12)
- [ ] Create templates (optional)
- [ ] Design dashboard
- [ ] Implement reporting views
- [ ] Add charts and analytics
- [ ] Create verification portal

### Phase 6: REST API Completion (November 4, 2025)
- [x] **Complete REST API Implementation**:
  - [x] 21 API endpoints implemented
  - [x] JWT authentication with refresh tokens
  - [x] Swagger/OpenAPI documentation (drf-spectacular)
  - [x] Full CRUD operations for all models
  - [x] Pagination and filtering
  - [x] 159 tests passing (114 original + 45 new API tests)
  - [x] API documentation available at `/api/schema/swagger-ui/`

- [x] **ADIF Log Import System**:
  - [x] ADIF parser implementation (activations/adif_parser.py):
    - [x] Parse ADIF 3.1.5 format log files
    - [x] Extract QSO data: callsigns, bunker references, date/time, mode, band
    - [x] Validate bunker ID format (B/SP-xxxx)
    - [x] Detect B2B (bunker-to-bunker) QSOs
    - [x] Parse MY_SIG_INFO, MY_SIG (WWBOTA), OPERATOR/STATION_CALLSIGN fields
  - [x] Log import service (activations/log_import_service.py):
    - [x] Process ADIF uploads for activators
    - [x] Create placeholder hunter accounts automatically
    - [x] Award points to activators and hunters (1pt per QSO, 2x for B2B)
    - [x] Update UserStatistics (total_hunter_qso, total_activator_qso, activator_b2b_qso)
    - [x] Create ActivationLog records with mode, band, activator fields
    - [x] Security: Users can only upload their own logs
  - [x] API endpoint: POST `/api/activation-logs/upload_adif/`:
    - [x] Multipart file upload (.adi files)
    - [x] Returns QSO count and processing summary
    - [x] Validates file format and bunker references
  - [x] Database changes:
    - [x] ActivationLog.activator (ForeignKey to User, nullable)
    - [x] ActivationLog.mode (CharField for radio mode)
    - [x] ActivationLog.band (CharField for radio band)
    - [x] Migration: activations/0002_activationlog_activator_activationlog_band_and_more
  - [x] UTC time display:
    - [x] Serializers include *_utc fields (e.g., activation_date_utc)
    - [x] Format: "YYYY-MM-DD HH:MM UTC"
  - [x] Testing:
    - [x] 11 ADIF tests (7 parser tests, 4 import service tests)
    - [x] Total: 170 tests passing

### Phase 7: Testing & Deployment (Week 13-14)
- [x] Write unit tests (170 tests passing)
- [x] Write integration tests
- [ ] Performance optimization
- [ ] Security audit
- [ ] Documentation
- [ ] Deployment setup

---

## Configuration Requirements

### Required Python Packages
```
Django==5.2.7
djangorestframework
djangorestframework-simplejwt
django-filter
Pillow  # For image handling and photo processing
reportlab  # For PDF generation and text overlay
PyPDF2  # For PDF manipulation
qrcode  # For QR code generation
python-decouple  # For environment variables
mysqlclient  # MySQL adapter (for Cyber Folks VPS) - replaces psycopg2-binary
# psycopg2-binary  # PostgreSQL adapter (only if using PostgreSQL on VPS Root)
celery  # For async tasks (diploma generation, CSV import queue, image processing)
redis  # For caching and celery broker (if available on VPS)
django-cors-headers  # For CORS
pdf2image  # For template preview generation (optional)
pandas  # For CSV processing and validation
openpyxl  # For Excel export support
geojson  # For GeoJSON export
django-modeltranslation  # For model field translations
geoip2  # For IP-based geolocation (language detection)
django-imagekit  # For image thumbnails and optimization
django-cleanup  # For automatic cleanup of old media files
django-cookie-consent  # For GDPR cookie consent management (or django-gdpr-cookie-consent)
gunicorn  # WSGI server for production deployment
whitenoise  # Static file serving
```

### Environment Variables (.env)
```
SECRET_KEY=<your-secret-key>
DEBUG=True
DATABASE_URL=<database-connection-string>
ALLOWED_HOSTS=localhost,127.0.0.1
EMAIL_HOST=<smtp-host>
EMAIL_PORT=587
EMAIL_HOST_USER=<email>
EMAIL_HOST_PASSWORD=<password>
DEFAULT_LANGUAGE=en  # or 'pl'
GEOIP_PATH=/path/to/geoip/database  # For IP-based language detection
MAX_UPLOAD_SIZE=10485760  # 10MB max photo size
MEDIA_ROOT=/path/to/media/
MEDIA_URL=/media/
```

---

## Testing Strategy

### Overview
All components of the BOTA Project must be thoroughly tested to ensure reliability, security, and maintainability. We aim for **80%+ code coverage** across all modules.

### Testing Framework
- **Unit Tests**: Django's built-in `django.test.TestCase`
- **Integration Tests**: Django `TestCase` with database transactions
- **API Tests**: Django REST Framework's `APITestCase`
- **Coverage Tool**: `coverage.py`
- **Mock Library**: `unittest.mock` for external dependencies

### Unit Tests

#### Accounts App Tests
**File**: `accounts/tests/test_models.py`
- Test User model creation with email as username
- Test User authentication with email
- Test callsign uniqueness validation
- Test email validation and normalization
- Test password hashing and verification
- Test UserStatistics creation (OneToOne signal)
- Test UserStatistics points calculation
- Test UserStatistics update methods
- Test UserRole permissions
- Test UserRoleAssignment validation

**File**: `accounts/tests/test_views.py`
- Test user registration flow
- Test login/logout functionality
- Test password reset flow
- Test profile update
- Test permission-based access control

**File**: `accounts/tests/test_serializers.py`
- Test User serialization
- Test UserStatistics serialization
- Test validation rules
- Test nested serializers

#### Bunkers App Tests
**File**: `bunkers/tests/test_models.py`
- Test Bunker model creation
- Test BunkerCategory translation fields
- Test GPS coordinate validation
- Test Bunker status transitions
- Test BunkerPhoto approval workflow
- Test photo ordering and primary photo selection
- Test BunkerResource tracking
- Test BunkerInspection scheduling
- Test CSV import flag tracking

**File**: `bunkers/tests/test_csv_import.py`
- Test CSV template generation
- Test CSV validation (valid and invalid data)
- Test bulk import (create and update)
- Test error handling for malformed CSV
- Test import logging and reporting
- Test rollback on critical errors
- Test large file handling (performance)

**File**: `bunkers/tests/test_csv_export.py`
- Test full export
- Test filtered export
- Test custom field selection
- Test GeoJSON export format
- Test mapping data export

**File**: `bunkers/tests/test_photo_upload.py`
- Test photo upload
- Test photo approval/rejection
- Test primary photo designation
- Test photo deletion and cleanup
- Test thumbnail generation

#### Cluster App Tests
**File**: `cluster/tests/test_models.py`
- Test Cluster model creation
- Test ClusterMember assignment
- Test cluster capacity calculation
- Test ClusterAlert creation and acknowledgment
- Test bunker-cluster relationships

#### Activations App Tests
**File**: `activations/tests/test_models.py`
- Test ActivationKey generation
- Test key validation and expiration
- Test usage tracking and limits
- Test License model validation
- Test ActivationLog creation

**File**: `activations/tests/test_key_generation.py`
- Test unique key generation
- Test key format validation
- Test bulk key generation
- Test key revocation

#### Diplomas App Tests
**File**: `diplomas/tests/test_models.py`
- Test DiplomaType creation (all categories)
- Test achievement threshold validation
- Test Diploma automatic creation on achievement
- Test DiplomaProgress tracking and percentage calculation
- Test points system updates
- Test special event diploma validation (date ranges)
- Test specific bunker requirements for events

**File**: `diplomas/tests/test_achievement_tracking.py`
- Test automatic progress updates on QSO
- Test diploma awarding when threshold reached
- Test multiple diploma tracking simultaneously
- Test points accumulation
- Test category-specific points (hunter, activator, b2b)

**File**: `diplomas/tests/test_pdf_generation.py`
- Test PDF generation from template
- Test coordinate-based text placement
- Test callsign and date overlay
- Test QR code generation
- Test certificate number uniqueness
- Test generation count tracking
- Test regeneration capability
- Test test diploma generation for admin

**File**: `diplomas/tests/test_special_events.py`
- Test event diploma creation
- Test date range validation
- Test event-specific bunker requirements
- Test event participation tracking
- Test automatic awarding when event ends

**File**: `diplomas/tests/test_verification.py`
- Test diploma verification by QR code
- Test verification by certificate number
- Test verification logging
- Test revoked diploma handling

### Integration Tests

#### Authentication Flow Tests
**File**: `tests/integration/test_auth_flow.py`
- Test complete registration → login → profile access flow
- Test email authentication workflow
- Test password reset end-to-end
- Test role-based access control across apps

#### Bunker Management Flow Tests
**File**: `tests/integration/test_bunker_workflow.py`
- Test bunker creation → photo upload → approval → display
- Test CSV import → validation → bunker creation → export
- Test bunker assignment to cluster
- Test inspection scheduling and reminders

#### Diploma Achievement Flow Tests
**File**: `tests/integration/test_diploma_workflow.py`
- Test QSO entry → progress update → diploma award → PDF generation
- Test template upload → coordinate setting → test generation → user download
- Test special event creation → participation → automatic awarding
- Test multiple diploma categories simultaneously

#### Admin Workflow Tests
**File**: `tests/integration/test_admin_workflows.py`
- Test admin CSV import workflow
- Test admin photo approval workflow
- Test admin diploma template management
- Test admin category management with translations

### API Tests

#### Accounts API Tests
**File**: `accounts/tests/test_api.py`
- Test user registration endpoint
- Test login endpoint (JWT token generation)
- Test profile retrieval and update
- Test statistics retrieval
- Test authentication required responses
- Test permission-based endpoint access

#### Bunkers API Tests
**File**: `bunkers/tests/test_api.py`
- Test bunker list endpoint (pagination, filtering)
- Test bunker detail endpoint
- Test bunker creation (admin only)
- Test photo upload endpoint
- Test CSV export endpoint
- Test GeoJSON export endpoint
- Test language parameter handling (Polish/English)

#### Diplomas API Tests
**File**: `diplomas/tests/test_api.py`
- Test diploma list endpoint
- Test progress tracking endpoint
- Test PDF generation endpoint
- Test verification endpoint
- Test leaderboard endpoint
- Test admin-only endpoints (template management)

### End-to-End Tests

#### User Journey Tests
**File**: `tests/e2e/test_user_journeys.py`
- Test new user registration → bunker hunting → diploma earning → PDF download
- Test activator journey: activation → B2B QSO → diploma progress
- Test admin journey: create event diploma → monitor participation → end event

#### Mobile Responsiveness Tests
**File**: `tests/e2e/test_mobile_responsive.py`
- Test mobile navigation
- Test mobile photo upload
- Test mobile-friendly forms
- Test touch interactions
- Test responsive layouts at different breakpoints

#### Internationalization Tests
**File**: `tests/e2e/test_i18n.py`
- Test automatic language detection (Polish IP → Polish interface)
- Test manual language switching
- Test translated content display
- Test admin translation management

### Performance Tests

#### Load Testing
**File**: `tests/performance/test_load.py`
- Test API response times under load
- Test database query optimization
- Test PDF generation performance
- Test CSV import with large files (10,000+ rows)
- Test concurrent user access

#### Database Query Tests
**File**: `tests/performance/test_queries.py`
- Test N+1 query problems
- Test query count for list views
- Test database indexing effectiveness

### Security Tests

#### Security Audit Tests
**File**: `tests/security/test_security.py`
- Test SQL injection prevention
- Test XSS prevention
- Test CSRF protection
- Test authentication bypass attempts
- Test file upload security (malicious files)
- Test API rate limiting
- Test sensitive data exposure

### Test Data & Fixtures

#### Test Fixtures
**File**: `tests/fixtures/`
- `users.json` - Sample users with various roles
- `bunkers.json` - Sample bunkers with categories
- `diplomas.json` - Sample diploma types and achievements
- `test_csv.csv` - Sample CSV file for import testing

#### Factory Classes
**File**: `tests/factories.py`
- `UserFactory` - Create test users
- `BunkerFactory` - Create test bunkers
- `DiplomaTypeFactory` - Create test diploma types
- Use `factory_boy` for test data generation

### Coverage Goals

#### Minimum Coverage Requirements
- **Models**: 90%+
- **Views/ViewSets**: 85%+
- **Serializers**: 90%+
- **Business Logic**: 95%+
- **Overall Project**: 80%+

#### Coverage Reporting
```bash
# Run tests with coverage
coverage run --source='.' manage.py test

# Generate coverage report
coverage report

# Generate HTML coverage report
coverage html

# View coverage report
# Open htmlcov/index.html in browser
```

### Continuous Integration

#### CI/CD Pipeline (Future)
- Run all tests on every commit
- Check code coverage threshold
- Run linting and code quality checks (flake8, black, pylint)
- Security scanning (bandit)
- Dependency vulnerability scanning

### Test Execution

#### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts
python manage.py test bunkers

# Run specific test file
python manage.py test accounts.tests.test_models

# Run specific test case
python manage.py test accounts.tests.test_models.UserModelTest

# Run with verbosity
python manage.py test --verbosity=2

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

#### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `*Test` or `*TestCase`
- Test methods: `test_*`
- Descriptive names: `test_user_creation_with_email_and_callsign`

### Mocking Strategy

#### External Services to Mock
- Email sending (SMTP)
- File storage (S3 in production)
- GeoIP database lookups
- Payment processing (if implemented)
- External API calls

#### Example Mock Usage
```python
from unittest.mock import patch, MagicMock

class DiplomaGenerationTest(TestCase):
    @patch('diplomas.utils.generate_pdf')
    def test_diploma_generation(self, mock_pdf):
        mock_pdf.return_value = b'fake_pdf_content'
        diploma = Diploma.objects.create(...)
        result = diploma.generate_certificate()
        self.assertTrue(result)
        mock_pdf.assert_called_once()
```

### Test Documentation

Each test file should include:
- Module docstring explaining what is being tested
- Test class docstrings explaining test scope
- Test method docstrings explaining specific test case
- Comments for complex setup or assertions

### Quality Metrics

#### Code Quality Checks
- **Linting**: flake8 (PEP 8 compliance)
- **Formatting**: black (consistent code style)
- **Type Hints**: mypy (optional, for critical functions)
- **Security**: bandit (security vulnerability scanning)
- **Complexity**: radon (cyclomatic complexity < 10)

#### Test Quality Metrics
- Test execution time (target: < 2 minutes for full suite)
- Test isolation (no dependencies between tests)
- Test stability (no flaky tests)
- Test maintainability (DRY principle)

---

## Deployment Considerations

### Production Hosting: Cyber Folks (Poland)

#### Hosting Environment
**Provider**: cyber_Folks S.A., Poznań, Poland (https://cyberfolks.pl/)
**Service Type**: VPS Root or VPS Managed (Zarządzany)

#### Recommended Plan: VPS Zarządzany (Managed VPS)
**Why Managed VPS**:
- DirectAdmin panel included
- MySQL database management via DirectAdmin
- Daily backups (up to 28 days retention)
- Python and Node.js application support confirmed
- SSH access available
- Email support and technical assistance
- LiteSpeed Web Server with LSCache
- Let's Encrypt SSL certificates (free with manual renewal)
- 99.2% - 99.9% SLA depending on plan

**Available Plans** (SSD NVMe storage):
1. **vManaged Basic**: 30 GB NVMe, 4 GB RAM, 1 CPU core, 30GB/month - Starting plan
2. **vManaged Standard**: 60 GB NVMe, 4 GB RAM, 2 CPU cores - **Recommended for BOTA Project**
3. **vManaged Pro**: 100 GB NVMe, 8 GB RAM, 4 CPU cores - For scaling
4. **vManaged Enterprise**: 160 GB NVMe, 16 GB RAM, 8 CPU cores - For high traffic

**Alternative: VPS Root** (Self-managed):
- Full root access
- KVM virtualization
- Same hardware specs as Managed VPS
- Self-administered (no DirectAdmin, no support)
- Lower cost but requires server administration expertise
- Manual backup restoration (charged at 249 PLN/hour)

#### Technical Specifications (VPS Managed)
- **Operating System**: Linux (managed by Cyber Folks)
- **Control Panel**: DirectAdmin
- **Web Server**: LiteSpeed (Apache/Nginx configuration via DirectAdmin)
- **Database**: MySQL/MariaDB (PostgreSQL NOT confirmed - **requires verification**)
- **PHP Versions**: 5.2 to latest (MultiPHP support)
- **Python Support**: ✅ Confirmed (version TBD - requires verification with support)
- **Node.js Support**: ✅ Confirmed
- **SSH Access**: ✅ Available (on Medium+ plans)
- **CRON Jobs**: ✅ Supported (max 60 min execution time)
- **Max PHP Memory**: 1024 MB (128 MB minimum)
- **HTTP Timeout**: 300 seconds
- **Daily Backups**: ✅ Automated (28 days retention on Pro+ plans)
- **SSL Certificates**: Let's Encrypt (free, manual renewal or paid auto-renewal)
- **Network**: 100 Mbps, IPv4 + IPv6 support
- **Location**: Gdańsk, Poland

#### Database Considerations
**IMPORTANT**: Cyber Folks shared hosting and VPS Managed plans primarily support **MySQL/MariaDB**, not PostgreSQL.

**Options**:
1. **Use MySQL instead of PostgreSQL** (Recommended):
   - Django fully supports MySQL/MariaDB
   - Change `psycopg2-binary` to `mysqlclient` in requirements
   - Update `settings.py` database configuration
   - MySQL is fully compatible with Django ORM
   
2. **Install PostgreSQL on VPS Root**:
   - Requires VPS Root plan (self-managed)
   - Manual PostgreSQL installation and configuration
   - Self-managed backups and maintenance
   - Not recommended unless you have server admin expertise

3. **Contact Cyber Folks Support**:
   - Verify if PostgreSQL is available on Managed VPS with custom configuration
   - Some managed plans may support it on request

**Recommended**: Use MySQL/MariaDB for simplicity and compatibility with Cyber Folks infrastructure.

#### Django Deployment on Cyber Folks VPS

##### Deployment Stack
- **Web Server**: LiteSpeed (reverse proxy to Gunicorn)
- **WSGI Server**: Gunicorn
- **Database**: MySQL/MariaDB
- **Cache**: Redis (if available, check with support) or file-based cache
- **Task Queue**: Celery with Redis or database backend
- **Static Files**: Served via LiteSpeed with WhiteNoise
- **Media Files**: Local storage on VPS NVMe disk

##### Deployment Steps
1. **Prepare VPS**:
   - Order VPS Managed Standard or higher
   - Access DirectAdmin panel
   - Enable SSH access
   - Set up Python environment (verify Python 3.x availability)

2. **Install Django Application**:
   ```bash
   # SSH into VPS
   ssh user@your-vps-ip
   
   # Create project directory
   mkdir /home/username/bota_project
   cd /home/username/bota_project
   
   # Create Python virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configure Database** (MySQL):
   - Create MySQL database via DirectAdmin
   - Create database user with full privileges
   - Update Django settings:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'bota_db',
           'USER': 'bota_user',
           'PASSWORD': 'secure_password',
           'HOST': 'localhost',
           'PORT': '3306',
           'OPTIONS': {
               'charset': 'utf8mb4',
               'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
           },
       }
   }
   ```

4. **Configure Gunicorn**:
   - Install: `pip install gunicorn`
   - Create systemd service or use supervisor
   - Run: `gunicorn bota_project.wsgi:application --bind 127.0.0.1:8000`

5. **Configure Web Server**:
   - Set up reverse proxy in DirectAdmin/LiteSpeed
   - Configure to forward requests to Gunicorn
   - Enable HTTPS with Let's Encrypt certificate

6. **Static and Media Files**:
   - Run `python manage.py collectstatic`
   - Configure LiteSpeed to serve `/static/` and `/media/` directories
   - Set proper permissions

7. **Set up Backups**:
   - Daily automated backups included in Managed VPS
   - Additional backup: Set up CRON job for database dumps
   - Store backups in separate location if critical

8. **Configure Email**:
   - Use SMTP from Cyber Folks (included in hosting)
   - Or configure external SMTP (SendGrid, Mailgun)

##### Production Settings
- Set `DEBUG=False`
- Configure MySQL database connection
- Set `ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']`
- Enable HTTPS enforcement
- Set up logging to file
- Configure email backend (SMTP)
- Set `SECRET_KEY` from environment variable
- Use file-based cache or Redis if available

#### Security Considerations
- Change default DirectAdmin password immediately
- Disable root SSH login (if using VPS Root)
- Configure firewall (if VPS Root)
- Enable Let's Encrypt SSL certificate
- Regular security updates (automatic on Managed VPS)
- Use strong database passwords
- Implement Django security best practices:
  - CSRF protection enabled
  - Secure cookies
  - Content Security Policy headers
  - XSS protection

#### Monitoring & Maintenance
- **Included with Managed VPS**:
  - Server monitoring 24/7
  - Email notifications for issues
  - DirectAdmin resource usage tracking
- **Application Monitoring**:
  - Set up Sentry for error tracking (optional)
  - Configure Django logging
  - Monitor disk space and database size
  - Track application performance

#### Scaling Options
- Start with VPS Managed Standard (60GB, 4GB RAM, 2 CPU)
- Upgrade to Pro or Enterprise as traffic grows
- Optimize database with indexes and query optimization
- Enable caching (Redis or file-based)
- Consider CDN for static assets (Cyber Folks offers CDN service)

#### Support & Contact
- **Technical Support**: Available through DirectAdmin panel tickets
- **Support Response Time**: 2-4 hours (depending on plan)
- **Documentation**: https://cyberfolks.pl/pomoc/
- **Contact**: https://cyberfolks.pl/kontakt/
- **Phone Support**: Available for higher tier plans

#### Cost Estimation (Indicative - verify current pricing)
- **VPS Managed Standard**: ~50-70 PLN/month (~$13-18 USD)
- **VPS Managed Pro**: ~100-120 PLN/month (~$25-30 USD)
- **Domain Registration**: ~40-60 PLN/year
- **SSL Certificate**: Free (Let's Encrypt manual) or ~50 PLN/year (auto-renewal)

**Total Estimated Monthly Cost**: 50-120 PLN (~$13-30 USD) depending on plan

---

### Cookie Policy & GDPR Compliance

#### Legal Requirements (EU & Poland)
The BOTA Project must comply with:
1. **GDPR** (General Data Protection Regulation - EU Regulation 2016/679)
2. **ePrivacy Directive** (Cookie Law - Directive 2002/58/EC)
3. **Polish Personal Data Protection Act** (if applicable)

#### Cookie Usage in BOTA Project
The application uses cookies for:
- **Session Management**: Django session cookies (essential)
- **Authentication**: Remember logged-in users (essential)
- **Language Preference**: Store user's language choice (functional)
- **CSRF Protection**: Security tokens (essential)

#### Cookie Categories
1. **Strictly Necessary Cookies** (No consent required):
   - `sessionid` - Django session cookie
   - `csrftoken` - CSRF protection
   - Purpose: Essential for website functionality
   - Duration: Session or until logout
   
2. **Functional Cookies** (Consent required):
   - `django_language` - User's language preference
   - Purpose: Remember user preferences
   - Duration: 1 year
   
3. **Analytics Cookies** (If implemented - Consent required):
   - Google Analytics or similar (if added)
   - Purpose: Track usage and improve service
   - Duration: Variable

#### Cookie Consent Implementation

##### Required Components
1. **Cookie Banner**:
   - Display on first visit
   - Clear information about cookie usage
   - Options: Accept All, Reject Non-Essential, Customize
   - Available in Polish and English

2. **Cookie Policy Page**:
   - Detailed list of all cookies used
   - Purpose of each cookie
   - Duration and type
   - How to manage/delete cookies
   - Contact information for data privacy questions

3. **Consent Storage**:
   - Store user's consent choices
   - Allow users to withdraw consent
   - Document consent for audit purposes

##### Implementation Steps
1. **Install Cookie Consent Package**:
   ```bash
   pip install django-cookie-consent
   # or
   pip install django-gdpr-cookie-consent
   ```

2. **Create Cookie Banner Template**:
   - Overlay or bottom banner
   - Multilingual (Polish/English)
   - Buttons: Accept All, Settings, Reject

3. **Create Cookie Policy Page** (`/cookies-policy/`):
   ```markdown
   ## Cookie Policy / Polityka Plików Cookie
   
   ### What are cookies? / Czym są pliki cookie?
   [Explanation in both languages]
   
   ### Cookies we use / Używane pliki cookie
   [Table with cookie details]
   
   ### How to manage cookies / Jak zarządzać plikami cookie
   [Instructions for different browsers]
   ```

4. **Update Privacy Policy** (`/privacy-policy/`):
   - Add section about cookies
   - Explain data processing
   - User rights under GDPR
   - Contact information for data protection officer

5. **Implement Consent Logic**:
   ```python
   # Check consent before setting non-essential cookies
   if user_has_consented('functional'):
       response.set_cookie('django_language', language)
   ```

#### Cookie Banner Example Text

**Polish Version**:
```
Ta strona używa plików cookie w celu zapewnienia prawidłowego działania 
serwisu oraz poprawy jakości usług. Klikając "Akceptuj wszystkie", 
wyrażasz zgodę na używanie wszystkich plików cookie. Możesz również 
wybrać "Ustawienia", aby zarządzać swoimi preferencjami.

[Akceptuj wszystkie] [Ustawienia] [Tylko niezbędne]

Więcej informacji: [Polityka Plików Cookie]
```

**English Version**:
```
This website uses cookies to ensure proper functionality and improve 
service quality. By clicking "Accept All", you consent to the use of 
all cookies. You can also choose "Settings" to manage your preferences.

[Accept All] [Settings] [Essential Only]

More information: [Cookie Policy]
```

#### Required Documentation

##### 1. Cookie Policy Page (Required)
- **URL**: `/cookies-policy/` or `/polityka-cookies/`
- **Content**:
  - List of all cookies
  - Cookie categories (essential, functional, analytics)
  - Purpose and duration of each cookie
  - How to disable cookies in browsers
  - Link to Privacy Policy

##### 2. Privacy Policy Page (Required)
- **URL**: `/privacy-policy/` or `/polityka-prywatnosci/`
- **Content**:
  - Data controller information (BOTA Project operator)
  - What personal data is collected
  - Purpose of data processing
  - Legal basis for processing (GDPR Article 6)
  - Data retention periods
  - User rights (access, rectification, erasure, portability)
  - Data security measures
  - Contact information

##### 3. Terms of Service (Recommended)
- **URL**: `/terms-of-service/` or `/regulamin/`
- **Content**:
  - Service usage terms
  - User obligations
  - Intellectual property
  - Limitation of liability

#### User Rights Under GDPR
Users must be able to:
1. **Access**: View their personal data
2. **Rectification**: Correct inaccurate data
3. **Erasure**: Delete their account and data ("right to be forgotten")
4. **Data Portability**: Export their data
5. **Withdraw Consent**: Revoke cookie consent at any time
6. **Object**: Object to data processing

#### Implementation in Django
```python
# settings.py
COOKIE_CONSENT_ENABLED = True
COOKIE_CONSENT_LOG_ENABLED = True

# urls.py
path('cookies-policy/', views.cookie_policy, name='cookie-policy'),
path('privacy-policy/', views.privacy_policy, name='privacy-policy'),
path('cookie-settings/', views.cookie_settings, name='cookie-settings'),
```

#### Footer Links (Required)
Every page must include footer links to:
- Cookie Policy / Polityka Plików Cookie
- Privacy Policy / Polityka Prywatności
- Terms of Service / Regulamin
- Contact / Kontakt

#### Compliance Checklist
- [ ] Cookie banner implemented (multilingual)
- [ ] Cookie consent storage and management
- [ ] Cookie Policy page created (PL & EN)
- [ ] Privacy Policy page created (PL & EN)
- [ ] User can withdraw consent
- [ ] User can export their data
- [ ] User can delete their account
- [ ] Only essential cookies set without consent
- [ ] Footer links to legal pages on all pages
- [ ] Documentation of consent for audit
- [ ] Contact email for privacy questions

#### Recommended Cookie Consent Libraries
1. **django-cookie-consent**: Simple Django integration
2. **cookiebot**: Third-party service with compliance features
3. **osano**: Privacy management platform
4. **Custom Implementation**: Using Django sessions

#### Data Protection Officer (DPO)
If required, designate a DPO:
- Email: privacy@botaproject.example (or similar)
- Include contact information in Privacy Policy
- Respond to data subject requests within 30 days (GDPR requirement)

#### Penalties for Non-Compliance
- GDPR fines: Up to €20 million or 4% of annual global turnover
- Polish fines: PUODO (Polish DPA) can impose penalties
- **Recommendation**: Implement cookie consent before launch

---

### Infrastructure
- Web server: Gunicorn + LiteSpeed (Cyber Folks VPS)
- Database: MySQL/MariaDB (via DirectAdmin)
- Cache: Redis or file-based cache
- Task queue: Celery with Redis or database backend
- Monitoring: Sentry for error tracking (optional)
- Hosting: Cyber Folks VPS Managed (Gdańsk, Poland)

---

## Notes & Assumptions

1. **User Model**: Custom User model with email as username, password, and callsign fields only (simplified for regular use)
2. **File Storage**: Local storage for development, cloud storage (S3) for production
3. **Time Zones**: UTC for all timestamps, display in user's local timezone
4. **Soft Deletes**: Consider implementing soft deletes for critical models
5. **Audit Trail**: All major actions should be logged
6. **Internationalization**: Structure supports i18n/l10n if needed
7. **Scalability**: Design allows for horizontal scaling with proper database indexing

---

## Contact & Support

**Project Manager**: [To be assigned]
**Lead Developer**: [To be assigned]
**Database Admin**: [To be assigned]

---

## Version History

- **v1.0** (November 3, 2025) - Initial specification document created
- **v1.1** (November 3, 2025) - Simplified User model to email, password, and callsign only
- **v1.2** (November 3, 2025) - Updated diploma system for achievement-based awards:
  - Added UserStatistics model for tracking activator/hunter progress
  - Redefined diploma categories: HUNTER, ACTIVATOR, BUNKER_TO_BUNKER
  - Added DiplomaProgress model for real-time progress tracking with percentages
  - Defined achievement criteria for each diploma category
  - Removed training program models (not needed for this system)
- **v1.3** (November 3, 2025) - Enhanced diploma template and generation system:
  - Added template coordinate fields to DiplomaType (X/Y positions for callsign and date)
  - Added font configuration fields (font name, size)
  - Implemented on-demand diploma generation (not pre-generated)
  - Added test diploma generation for admin users
  - Added coordinate picker functionality for admin panel
  - Added generation tracking (count downloads per diploma)
  - Separated earned_date from generated_date in Diploma model
  - User profile shows "Get Diploma" button for on-demand PDF generation
- **v1.4** (November 3, 2025) - Added points system and special event diplomas:
  - Added comprehensive points system to UserStatistics (total, category-specific, diploma points)
  - Added SPECIAL_EVENT diploma category
  - Added points-based diploma requirements (requirement_type='POINTS')
  - Added event date fields (event_start_date, event_end_date) to DiplomaType
  - Added specific_bunkers ManyToMany field for special event requirements
  - Added EVENT_ACTIVATION and EVENT_HUNTING requirement types
  - Enhanced admin features for creating and managing special event diplomas
  - Added event participation monitoring
  - Added points configuration and leaderboard endpoints
  - Admin can now create time-limited contest diplomas
  - Admin can duplicate existing diplomas for quick creation
- **v1.5** (November 3, 2025) - Added CSV import/export system for bunkers:
  - Added BunkerImportLog model to track CSV import history
  - Added CSVTemplate model for admin-maintained import/export templates
  - Added imported_from_csv flag to Bunker model
  - Implemented CSV import workflow with validation and preview
  - Implemented CSV export with custom field selection
  - Added GeoJSON export for mapping applications
  - Admin can download CSV templates with proper headers
  - Admin can generate sample CSV files with test data
  - Import process includes detailed error reporting and logging
  - Support for bulk create and update via CSV
  - Added pandas for CSV processing
  - Added geojson package for map data export
- **v1.6** (November 3, 2025) - Added internationalization, photo management, and mobile responsiveness:
  - **Internationalization (i18n)**:
    - Added full Polish and English language support
    - Added translation fields to BunkerCategory and Bunker models
    - Implemented IP-based language detection using GeoIP2
    - Added manual language switching capability
    - Configured django-modeltranslation for database translations
  - **Photo Management**:
    - Added BunkerPhoto model for multiple photos per bunker
    - Implemented photo approval workflow (admin approval required)
    - Added photo gallery with primary photo designation
    - Added translation fields for photo titles and descriptions
    - Support for bulk photo uploads
    - Automatic thumbnail generation with django-imagekit
  - **Bunker Category Management**:
    - Admin can create custom categories (Bunker, Fort, Fortress, Shelter, Tower, etc.)
    - Full translation support for category names and descriptions
    - Display order management
  - **Mobile Responsiveness**:
    - Mobile-first design approach
    - Responsive layouts for phones, tablets, and desktops
    - Touch-friendly UI with appropriate spacing
    - Optimized image serving for mobile networks
    - Camera integration for photo uploads on mobile devices
    - Mobile-optimized maps and galleries
  - **New Packages**:
    - django-modeltranslation for model translations
    - geoip2 for IP-based language detection
    - django-imagekit for image optimization
    - django-cleanup for automatic media cleanup
- **v1.7** (November 3, 2025) - Added production hosting specifications and GDPR compliance:
  - **Production Hosting**:
    - Documented Cyber Folks VPS hosting environment (Poland)
    - Recommended VPS Managed (DirectAdmin panel, daily backups, SSH access)
    - Technical specifications: SSD NVMe storage, LiteSpeed web server, Python support
    - **Database Change**: MySQL/MariaDB instead of PostgreSQL (Cyber Folks standard)
    - Updated requirements.txt: `mysqlclient` replaces `psycopg2-binary`
    - Deployment stack: Gunicorn + LiteSpeed + MySQL + Redis
    - Backup strategy: Automated daily backups (28 days retention on Pro+ plans)
    - SSL: Let's Encrypt free certificates
    - Location: Gdańsk, Poland (100 Mbps network, IPv4 + IPv6)
  - **Cookie Policy & GDPR Compliance**:
    - Comprehensive cookie consent implementation requirements
    - Cookie categories: Essential, Functional, Analytics
    - Multilingual cookie banner (Polish/English)
    - Required legal pages: Cookie Policy, Privacy Policy, Terms of Service
    - User rights under GDPR: Access, Rectification, Erasure, Portability
    - Data protection officer (DPO) guidelines
    - Cookie consent storage and withdrawal mechanism
    - Footer links to legal pages on all pages
    - Compliance checklist and implementation steps
  - **New Packages**:
    - django-cookie-consent for GDPR compliance
    - gunicorn for WSGI server
    - whitenoise for static file serving
    - mysqlclient for MySQL database connection
  - **Environment Updates**:
    - MySQL database configuration examples
    - Production settings for Cyber Folks environment
    - Security considerations for VPS deployment

- **v1.8** (November 4, 2025) - Completed REST API and added ADIF log import functionality:
  - **REST API Completion (Phase 6)**:
    - Implemented 21 REST API endpoints covering all models
    - JWT authentication with access and refresh tokens
    - Swagger/OpenAPI documentation using drf-spectacular
    - Full CRUD operations for accounts, bunkers, clusters, activations, diplomas
    - Pagination and filtering on all list endpoints
    - 159 tests passing (114 original + 45 new API tests)
    - API documentation available at `/api/schema/swagger-ui/`
  - **ADIF Log Import System**:
    - Created ADIF parser (activations/adif_parser.py) supporting ADIF 3.1.5 format
    - Regex-based field extraction for QSO data
    - Parse bunker references (B/SP-xxxx format)
    - Extract activator callsigns (OPERATOR, STATION_CALLSIGN fields)
    - Extract hunter callsigns (CALL field)
    - Parse QSO date/time, mode, band
    - Validate bunker ID format and WWBOTA signature
    - Detect B2B (bunker-to-bunker) QSOs
  - **Log Import Service**:
    - Created log_import_service.py for processing ADIF uploads
    - Transaction-based processing with rollback on errors
    - Auto-create placeholder accounts for hunters
    - Award points: 1pt per QSO, 2x for B2B connections
    - Update UserStatistics (total_hunter_qso, total_activator_qso, activator_b2b_qso, total_b2b_qso)
    - Security: Users can only upload logs matching their callsign
    - Detailed logging and error reporting
  - **Database Changes**:
    - Extended ActivationLog model with:
      - activator (ForeignKey to User, nullable) - Who activated the bunker
      - mode (CharField) - Radio mode (SSB, CW, FM, etc.)
      - band (CharField) - Radio band (40m, 20m, etc.)
    - Migration: activations/0002_activationlog_activator_activationlog_band_and_more
  - **API Endpoint**:
    - POST `/api/activation-logs/upload_adif/` - Multipart file upload
    - Accepts .adi files
    - Returns QSO count, points awarded, warnings
    - File validation and parsing
    - Swagger documentation included
  - **UTC Time Display**:
    - Added *_utc fields to serializers (activation_date_utc, end_date_utc, valid_from_utc, valid_until_utc)
    - Format: "YYYY-MM-DD HH:MM UTC"
    - Uses datetime.timezone.utc for consistency
  - **Testing**:
    - Added 11 ADIF tests (activations/test_adif.py):
      - 7 parser tests (ADIFParserTest)
      - 4 import service tests (LogImportServiceTest)
    - Total: 170 tests passing
    - 100% test coverage for ADIF functionality
  - **Files Created**:
    - activations/adif_parser.py (300+ lines)
    - activations/log_import_service.py (278 lines)
    - activations/test_adif.py (197 lines)
  - **Files Modified**:
    - activations/models.py (added activator, mode, band fields)
    - activations/views.py (added upload_adif action)
    - activations/serializers.py (added UTC time fields)

---

## Approval Status

**Status**: READY FOR IMPLEMENTATION

**Current Version**: v1.8
**Last Updated**: November 4, 2025

Once approved, development can begin following the phased roadmap outlined above.

**Approved by**: ___________________
**Date**: ___________________
**Signature**: ___________________

---

*This document is subject to updates and modifications as the project evolves.*
