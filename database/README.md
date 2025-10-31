# Database Module - DoE-Assist

## Overview

This module contains the database schema, initialization scripts, and documentation for the DoE-Assist MySQL database.

## Responsibilities

- Database Schema Design (Users, Experiments, Literature, etc.)
- Data Migration Management
- Data Validation and Constraints
- Query Optimization and Index Management
- Database Initialization Scripts

## Tech Stack

- **MySQL 8.0** - Primary database (Dockerized)
- **SQLAlchemy 2.0+** - ORM for Python backend
- **PyMySQL** - MySQL connector for Python

## Database Schema

### Core Tables

#### 1. `app_user` - User Accounts
Stores user account information and authentication data.

**Columns:**
- `id` (BIGINT, PRIMARY KEY, AUTO_INCREMENT) - User ID
- `username` (VARCHAR(64), UNIQUE, NOT NULL) - Username
- `email` (VARCHAR(255), NOT NULL) - Email address
- `password_hash` (VARCHAR(255), NOT NULL) - Hashed password (bcrypt)
- `role` (VARCHAR(32), NOT NULL, DEFAULT 'user') - User role
- `is_active` (TINYINT(1), NOT NULL, DEFAULT 1) - Active status
- `created_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP) - Creation time
- `last_login_at` (TIMESTAMP, NULL) - Last login time

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `username`

#### 2. `auth_login_audit` - Login Audit Log
Records all login attempts for security auditing.

**Columns:**
- `id` (BIGINT, PRIMARY KEY, AUTO_INCREMENT) - Audit record ID
- `user_id` (BIGINT, NULL, FK → `app_user.id`) - User ID (if successful)
- `username` (VARCHAR(64)) - Username attempted
- `ip` (VARCHAR(45)) - IP address
- `ok` (TINYINT(1), NOT NULL) - Login success (1) or failure (0)
- `created_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP) - Attempt time

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `created_at`
- FOREIGN KEY on `user_id` → `app_user.id` (ON DELETE SET NULL)

### Literature Tables

#### 3. `literature` - Literature Metadata
Stores metadata about scientific literature sources.

**Columns:**
- `id` (INT, PRIMARY KEY, AUTO_INCREMENT) - Literature ID
- `doi` (VARCHAR(255)) - Digital Object Identifier
- `title` (TEXT) - Publication title
- `authors` (TEXT) - Author list
- `pub_year` (INT) - Publication year
- `source` (VARCHAR(255)) - Source (e.g., "arxiv", "pubmed")
- `created_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP) - Creation time

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `doi`

#### 4. `extraction_records` - Experimental Data from Literature
Stores extracted experimental parameters and results from literature.

**Columns:**
- `id` (INT, PRIMARY KEY, AUTO_INCREMENT) - Record ID
- `literature_id` (INT, FK → `literature.id`) - Related literature
- `biomolecule_type` (VARCHAR(64), NOT NULL, DEFAULT 'protein') - Type of biomolecule
- `protein_name` (VARCHAR(255)) - Protein/biomolecule name
- `polarity` (VARCHAR(32)) - Polarity
- `property` (VARCHAR(64), NOT NULL, DEFAULT 'stability') - Property type

**Experimental Parameters:**
- `pH` (FLOAT) - pH value
- `temperature_c` (FLOAT) - Temperature in Celsius
- `concentration_mg_ml` (FLOAT) - Concentration in mg/mL
- `ionic_strength_mM` (FLOAT) - Ionic strength in mM
- `additive` (TEXT) - Additive information
- `time_min` (FLOAT) - Time in minutes
- `shear_rate_s1` (FLOAT) - Shear rate in s⁻¹
- `pressure_bar` (FLOAT) - Pressure in bar

**Results:**
- `outcome_score` (FLOAT) - Outcome score
- `outcome_label` (VARCHAR(255)) - Outcome label
- `outcome_text` (TEXT) - Outcome description
- `source_section` (VARCHAR(255)) - Source section in paper

**Metadata:**
- `confidence` (FLOAT, NOT NULL, DEFAULT 0.5) - Confidence score
- `raw_context` (TEXT) - Raw text context
- `full_data` (JSON) - Complete extracted data
- `created_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP) - Creation time

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `literature_id`
- INDEX on `protein_name`
- INDEX on `biomolecule_type`
- INDEX on `confidence`
- FOREIGN KEY on `literature_id` → `literature.id` (ON DELETE CASCADE)

### Experiment Tables

#### 5. `user_experiment_records` - User Experiment Predictions
Stores user prediction requests and results.

**Columns:**
- `id` (INT, PRIMARY KEY, AUTO_INCREMENT) - Record ID
- `user_id` (INT, FK → `app_user.id`) - User ID
- `biomolecule_type` (VARCHAR(64), NOT NULL) - Biomolecule type
- `biomolecule_name` (VARCHAR(255), NOT NULL) - Biomolecule name
- `experiment_type` (VARCHAR(64), NOT NULL, DEFAULT 'stability') - Experiment type

**Input Parameters (with `input_` prefix):**
- `input_pH` (FLOAT) - pH value
- `input_temperature_c` (FLOAT) - Temperature
- `input_concentration_mg_ml` (FLOAT) - Concentration
- `input_ionic_strength_mM` (FLOAT) - Ionic strength
- `input_additive` (TEXT) - Additive
- `input_time_min` (FLOAT) - Time
- `input_shear_rate_s1` (FLOAT) - Shear rate
- `input_pressure_bar` (FLOAT) - Pressure

**Prediction Results:**
- `prediction_type` (VARCHAR(32), NOT NULL) - 'classification' or 'parameter_prediction'
- `prediction_result` (TEXT/JSON) - Prediction result data
- `confidence` (FLOAT) - Confidence score
- `recommended_literature` (TEXT/JSON) - Top K similar literature records

**Metadata:**
- `created_at` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP) - Creation time

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `user_id`
- INDEX on `biomolecule_name`
- INDEX on `experiment_type`
- INDEX on `created_at`
- FOREIGN KEY on `user_id` → `app_user.id` (ON DELETE SET NULL)

## Project Structure

```
database/
├── db/
│   └── init/           # Initialization SQL scripts
│       ├── 001_users.sql              # User and auth tables
│       ├── 002_literature.sql         # Literature tables
│       ├── 003_user_experiments.sql   # Experiment tables
│       └── README.md                  # Init scripts documentation
└── README.md           # This file
```

## Initialization Scripts

SQL scripts in `db/init/` are automatically executed when MySQL container starts (if mounted as volume in `docker-compose.yml`).

### Execution Order
1. `001_users.sql` - User and authentication tables
2. `002_literature.sql` - Literature and extraction tables
3. `003_user_experiments.sql` - Experiment record tables

## Database Setup

### Using Docker Compose (Recommended)

The database is automatically initialized when using Docker Compose:

```bash
# From project root
docker compose up -d db
```

The initialization scripts in `database/db/init/` will be automatically executed.

### Manual Setup

1. **Create database:**
```sql
CREATE DATABASE appdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. **Run initialization scripts:**
```bash
mysql -u root -p appdb < database/db/init/001_users.sql
mysql -u root -p appdb < database/db/init/002_literature.sql
mysql -u root -p appdb < database/db/init/003_user_experiments.sql
```

## Connection Configuration

### Default Configuration (Docker)
- **Host**: `db` (service name in docker-compose)
- **Port**: `3306`
- **Database**: `appdb`
- **User**: `appuser`
- **Password**: `devpass`
- **Root Password**: `rootpass`

### Local Development
- **Host**: `localhost`
- **Port**: `53306` (mapped from container port 3306)

## Relationships

### Entity Relationships
- **User** → **UserExperimentRecord** (One-to-Many)
  - A user can have many experiment records
  - Deletion: SET NULL (records remain if user deleted)

- **Literature** → **ExtractionRecord** (One-to-Many)
  - A literature can have many extraction records
  - Deletion: CASCADE (records deleted if literature deleted)

- **User** → **AuthLoginAudit** (One-to-Many)
  - A user can have many login audit records
  - Deletion: SET NULL (audit records remain if user deleted)

## Data Features

### Current Features
- ✅ User authentication and audit logging
- ✅ Secure password hashing (bcrypt)
- ✅ Literature metadata storage
- ✅ Experimental parameter extraction
- ✅ Similarity search support (weighted parameters)
- ✅ User experiment history tracking
- ✅ JSON storage for flexible data (prediction results, literature recommendations)

### Indexes for Performance
- User lookups: `username` (UNIQUE)
- Literature search: `doi`, `protein_name`
- Similarity search: `protein_name`, `biomolecule_type`, `confidence`
- Experiment history: `user_id`, `created_at`

## Backup and Restore

### Backup
```bash
# Backup entire database
docker compose exec db mysqldump -u root -prootpass appdb > backup.sql

# Backup specific table
docker compose exec db mysqldump -u root -prootpass appdb literature > literature_backup.sql
```

### Restore
```bash
# Restore from backup
docker compose exec -T db mysql -u root -prootpass appdb < backup.sql
```

## Maintenance

### Check Table Sizes
```sql
SELECT 
    table_name AS 'Table',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.TABLES
WHERE table_schema = 'appdb'
ORDER BY (data_length + index_length) DESC;
```

### Check Index Usage
```sql
SHOW INDEX FROM extraction_records;
```

### Optimize Tables
```sql
OPTIMIZE TABLE app_user;
OPTIMIZE TABLE extraction_records;
OPTIMIZE TABLE user_experiment_records;
```

## Migration Notes

If you need to modify the schema:

1. **Create migration script** in `db/init/004_migration.sql`
2. **Test on development database first**
3. **Backup production database before applying**
4. **Document schema changes**

## Security Considerations

- ✅ Passwords are hashed using bcrypt
- ✅ SQL injection protection via SQLAlchemy ORM
- ✅ Database user has limited privileges (non-root)
- ✅ Connection uses credentials (not root user)
- ⚠️ **Change default passwords in production!**

## License

Part of DoE-Assist project
