# Scripts Directory

## Core Scripts

### Project Management
- `setup_project.py` - Project initialization script
- `start_services.py` - Start all services

### Model Training
- `train_multi_models.py` - Train multiple ML models (RF, XGBoost, LightGBM)
- `train_by_experiment_type.py` - Train models by experiment type
- `train_dual_track_system.py` - Train dual-track system models

### Data Processing
- `run_pipeline.py` - Run complete data processing pipeline (literature scraping → NLP extraction → ML training)
- `generate_iqr_statistics.py` - Generate IQR statistics for parameter recommendation

### Quality Analysis
- `analyze_quality.py` - Unified data quality analysis tool

### Docker Management
- `start_docker.py` - Start Docker services (cross-platform)
- `start_docker.bat` - Start Docker services (Windows batch)
- `start_docker.ps1` - Start Docker services (PowerShell)

### Recommendation
- `run_recommendation.py` - Run parameter recommendation system

## Usage

### Initialize Project
```bash
python scripts/setup_project.py
```

### Train Models
```bash
# Train multiple models
python scripts/train_multi_models.py --experiment-type stability --mode classification

# Train by experiment type
python scripts/train_by_experiment_type.py --experiment-type stability

# Train dual-track system
python scripts/train_dual_track_system.py
```

### Run Complete Pipeline
```bash
python scripts/run_pipeline.py --query "protein stability pH temperature"
```

### Analyze Data Quality
```bash
python scripts/analyze_quality.py --input literature_mining/storage/structured_store.jsonl
```

### Generate IQR Statistics
```bash
python scripts/generate_iqr_statistics.py
```

### Start Docker Services
```bash
# Cross-platform (Python)
python scripts/start_docker.py

# Windows
scripts/start_docker.bat

# PowerShell
scripts/start_docker.ps1
```

## Deprecated Scripts

The following scripts are for debugging purposes and can be safely deleted:
- `debug_regex.py`
- `debug_full.py`
- `debug_sentences.py`
- `relaxed_extractor.py`
- `ultra_simple_extractor.py`
- `test_extractor.py`
- `analyze_extraction_limits.py`
- `check_project.py`
- `run_closed_loop*.py` (all closed loop scripts)

## Script Organization

Scripts are organized by functionality:
- **Training scripts**: Model training and evaluation
- **Processing scripts**: Data processing and transformation
- **Analysis scripts**: Data quality analysis and statistics
- **Management scripts**: Project setup and service management
- **Docker scripts**: Docker service management

## Notes

- All scripts should be run from the project root directory
- Check script dependencies before running
- Use virtual environment for Python scripts
- Docker scripts require Docker and Docker Compose to be installed
