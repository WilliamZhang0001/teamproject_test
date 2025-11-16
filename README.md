# DoE-Assist - Intelligent Parameter Reduction for Experimental Design

## Project Overview
DoE-Assist is an intelligent system designed to provide researchers with optimal starting parameters for experimental design by mining scientific literature and leveraging machine learning technologies.

## Project Structure

```
project/
├── frontend/          # Frontend Interface (React + TypeScript + Material-UI)
├── backend/           # Backend Services (Python + FastAPI)
├── database/         # Database Models and Configuration (MySQL)
├── ml_engine/         # Machine Learning Engine
├── literature_mining/ # Literature Mining Engine
├── docs/             # Project Documentation
├── scripts/          # Utility Scripts
├── docker-compose.yml # Docker Compose configuration
└── README.md         # This file
```

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git (to clone the repository)

### Start the Entire System

#### Method 1: Using Auto-Start Scripts (Recommended, automatically opens browser)

**Windows Users:**
- Double-click `start.bat` or run in command line:
  ```bash
  start.bat
  ```
- Or use PowerShell:
  ```powershell
  .\start.ps1
  ```

**Cross-platform (Python):**
```bash
python scripts/start_docker.py
```

These scripts will:
1. Start all Docker containers
2. Wait for frontend service to be ready
3. **Automatically open browser to access the application**

#### Method 2: Manual Start

The entire system (database, backend, and frontend) can be started with a single command:

```bash
docker compose up -d --build
```

This will:
1. Build and start MySQL database (port 53306)
2. Build and start Backend API (port 8000)
3. Build and start Frontend (port 3000)

Then manually access: http://localhost:3000

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **API ReDoc**: http://localhost:8000/redoc

### Stop the System

```bash
docker compose down
```

To also remove volumes:

```bash
docker compose down -v
```

## Tech Stack

- **Frontend**: React 18.2+, TypeScript, Material-UI 5.15
- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0+
- **Database**: MySQL 8.0
- **Machine Learning**: scikit-learn, XGBoost, LightGBM, pandas, numpy
- **Literature Mining**: BeautifulSoup, NLTK, spaCy
- **Deployment**: Docker, Docker Compose

## Features

### Core Functionality
- **Experiment Classification**: Predict if experimental conditions are good/bad
- **Parameter Recommendation**: Get optimal parameter values based on IQR statistics and ML models
- **Literature Search**: Find similar literature based on experimental conditions
- **Batch CSV Processing**: Upload CSV files for batch predictions
  - Each row in the CSV represents one prediction query
  - Original columns are preserved in the output
  - Results are appended as new columns: `Result Value`, `Confidence Level`, `Related Literature`
  - Returns a downloadable CSV file with all predictions
- **User Authentication**: JWT-based authentication system
- **Experiment History**: Track and view prediction history

### Key Components
- **Frontend**: React-based single-page application with Material-UI
- **Backend**: RESTful API with FastAPI, supports multiple prediction endpoints
- **ML Engine**: Trained models for classification and parameter recommendation
- **Literature Mining**: Automated literature extraction and search system

## Development

### For Frontend Development
See [frontend/README.md](frontend/README.md) for detailed frontend development instructions.

### For Backend Development
See [backend/README.md](backend/README.md) for detailed backend development instructions.

### Environment Variables

The system uses environment variables configured in `docker-compose.yml`. Key variables include:
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, `DB_NAME` - Database connection
- `JWT_SECRET`, `JWT_EXPIRE_MINUTES` - Authentication settings
- `REACT_APP_API_URL` - Frontend API URL

## Project Status

- ✅ Docker Compose setup for complete system
- ✅ Frontend with React + TypeScript + Material-UI
- ✅ Backend API with FastAPI
- ✅ MySQL database with automatic initialization
- ✅ ML model integration
- ✅ Literature search functionality
- ✅ CSV batch processing
- ✅ User authentication and authorization
- ✅ Experiment history tracking

## Testing

A sample CSV file for batch prediction testing is available:
- `test_batch_prediction.csv` - Sample CSV with 7 test rows
- `test_batch_prediction_full.csv` - Extended test file with 9 rows

Use these files to test the CSV batch prediction feature in the Upload Dataset page.

## Documentation

- [Frontend README](frontend/README.md) - Frontend module documentation
- [Backend README](backend/README.md) - Backend module documentation
- [ML System Integration](ML_System_Integration_Documentation.md) - ML engine integration guide
- [ML Model QuickStart](DemoB_Model_QuickStart.md) - ML model quick start guide
- [Parameter Input Specification](Parameter_Input_Specification.md) - Parameter input specification


## License

MIT License
