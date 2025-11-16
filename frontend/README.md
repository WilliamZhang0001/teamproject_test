# Frontend Module - DoE-Assist

## Overview
DoE-Assist frontend module is built with React + TypeScript + Material-UI, providing a complete interface for experimental parameter recommendation and prediction.

## Feature Modules

### 1. User Authentication System
- User registration and login
- JWT Token authentication
- Protected routes

### 2. Experimental Parameter Query and Prediction (/query)
- **Classification Prediction**: Determine if experimental conditions are good/bad (Good/Bad)
- **Parameter Prediction**: Recommend values for specified parameters (based on IQR statistics)
- Supports biomolecule types: protein, peptide, polysaccharide
- Supports experiment types: stability, solubility, aggregation
- 8 optional parameter inputs (pH, temperature, concentration, etc.)
- Displays prediction results, confidence levels, and literature similarity references

### 3. Literature Search (/input)
- Search similar literature based on biomolecule name and experimental conditions
- Display literature similarity scores
- Show experimental parameters and result summaries
- Support DOI, authors, year, and other information

### 4. CSV Batch Prediction Upload (/upload)
- Upload CSV files for batch classification or parameter prediction
- Classification prediction: Returns Good/Bad judgment and confidence for each row
- Parameter prediction: Returns recommended parameter values and ranges
- Automatic download link generation

### 5. Experiment History Records (/results)
- View all historical prediction records
- Statistics: Total records, good/poor predictions, average confidence
- Detail dialog: Display complete prediction results and recommended literature
- Support sorting and filtering by time

### 6. User Feedback Submission (/feedback)
- Satisfaction rating (1-5 stars)
- Experiment type and feature satisfaction selection
- Detailed text feedback
- Feedback content hints

### 7. Home Dashboard (/dashboard)
- User welcome interface
- Statistics display
- Recent experiment records
- Feature entry navigation

## Tech Stack
- **React** 18.2+
- **TypeScript** 4.9+
- **Material-UI** 5.15 (Component library)
- **React Router** 6.8 (Routing management)
- **Axios** 1.6 (HTTP client)
- **Recharts** 2.8 (Data visualization)
- **Formik + Yup** (Form validation)

## Project Structure
```
frontend/
├── src/
│   ├── components/              # Reusable components
│   │   ├── ProtectedRoute.tsx       # Protected routes
│   │   ├── ErrorBoundary.tsx        # Error boundaries
│   │   └── Loading.tsx              # Loading components
│   ├── contexts/                # React Context
│   │   └── AuthContext.tsx          # Authentication context
│   ├── pages/                   # Page components
│   │   ├── HomePage.tsx             # Home page
│   │   ├── LoginPage.tsx            # Login
│   │   ├── RegisterPage.tsx         # Registration
│   │   ├── WelcomePage.tsx          # Welcome page
│   │   ├── ParameterQueryPage.tsx   # Parameter query
│   │   ├── DataInputPage.tsx        # Literature search
│   │   ├── UploadDatasetPage.tsx    # CSV upload
│   │   ├── ResultsDisplayPage.tsx   # History records
│   │   └── FeedbackPage.tsx         # Feedback
│   ├── services/                # API services
│   │   ├── api.ts                   # Axios configuration
│   │   ├── authService.ts           # Authentication service
│   │   └── experimentService.ts     # Experiment service
│   ├── utils/                   # Utility functions
│   │   ├── formatters.ts            # Formatting utilities
│   │   └── validators.ts            # Validation utilities
│   ├── config/                  # Configuration files
│   │   └── constants.ts             # Constant configuration
│   ├── types/                   # TypeScript types
│   │   └── index.ts                # Global type definitions
│   ├── App.tsx                  # Main application component
│   └── index.tsx                # Entry file
├── public/                      # Static resources
│   ├── index.html                  # HTML template
│   ├── manifest.json               # PWA manifest
│   └── favicon.ico                 # Website icon
├── Dockerfile                   # Production build configuration
├── Dockerfile.dev               # Development environment configuration
├── tsconfig.json                # TypeScript configuration
├── package.json                 # Dependency configuration
└── README.md                    # Documentation
```

## API Integration

### Backend Interface Integration
The frontend fully integrates with the following backend APIs:
- `POST /auth/login` - User login
- `POST /users` - User registration
- `POST /api/v1/experiments/predict-classification` - Classification prediction
- `POST /api/v1/experiments/predict-parameter` - Parameter prediction
- `POST /api/v1/predict` - Unified prediction interface
- `POST /api/v1/experiments/predict-csv` - CSV batch prediction
- `GET /api/v1/experiments/history` - Get history records
- `GET /api/v1/experiments/{id}` - Get single record
- `GET /literature/search` - Search literature

## Quick Start

### Using Docker Compose (Recommended)

The easiest way to start the frontend along with the entire system:

```bash
# From project root directory
docker compose up -d --build
```

This will automatically start:
- MySQL database
- Backend API service
- Frontend service (available at http://localhost:3000)

### Local Development (Without Docker)

If you prefer to run the frontend locally:

```bash
# Install dependencies
npm install

# Start development server
npm start
```

The development server will be available at http://localhost:3000

### Production Build

```bash
# Build production version
npm run build

# The build files will be in the `build/` directory
```

## Development Commands
```bash
npm install          # Install dependencies
npm start           # Start development server (http://localhost:3000)
npm run build       # Build production version
npm test            # Run tests
npm run type-check  # TypeScript type checking
npm run lint        # ESLint code checking
npm run lint:fix    # Auto-fix ESLint errors
```

## Environment Configuration

### Docker Compose Environment
When using Docker Compose, the frontend automatically uses:
- `REACT_APP_API_URL=http://localhost:8000` (configured in docker-compose.yml)

### Local Development Environment
Create `.env` file in the `frontend/` directory (optional):
```env
REACT_APP_API_URL=http://localhost:8000
```

## Docker Deployment

### Using Docker Compose (Recommended)

Run from project root directory:
```bash
docker compose up -d --build
```

Frontend service will automatically start at http://localhost:3000

### Run Frontend Container Separately

If you need to run the frontend container separately:

#### Development Environment
```bash
cd frontend
docker build -f Dockerfile.dev -t doe-assist-frontend:dev .
docker run -p 3000:3000 doe-assist-frontend:dev
```

#### Production Environment
```bash
cd frontend
docker build -t doe-assist-frontend:prod .
docker run -p 80:80 doe-assist-frontend:prod
```
Access: http://localhost

## Design Principles
- **Responsive Design**: Support desktop and mobile devices
- **Intuitive User Interface**: Clear navigation and feedback
- **Real-time Data Updates**: Loading states and error handling
- **Good User Experience**: Form validation, hints, empty states
- **Unified Visual Style**: Material-UI theme system

## Key Features

### 1. Complete Authentication Flow
- JWT Token automatic management
- Request interceptor automatically adds Token
- 401 error automatically logs out
- Protected route redirects

### 2. Rich Form Interactions
- Classification/parameter prediction switching
- Multi-select parameter prediction
- Real-time form validation
- Elegant error hints

### 3. Data Visualization
- History record statistics cards
- Literature similarity scores
- Parameter range display
- Confidence visualization

### 4. User Experience Optimization
- Loading state indicators
- Success/error feedback
- Empty state hints
- Responsive layout

## Code Quality
- ✅ No Linter errors
- ✅ TypeScript type safety
- ✅ Componentized design
- ✅ Service layer abstraction
- ✅ Error boundary handling
- ✅ Utility functions and common Hooks
- ✅ Unified constant configuration
- ✅ Responsive layout
- ✅ SEO optimization
- ✅ PWA support

## New Features and Improvements

### Utility Functions
- **formatters.ts**: Formatting utilities for dates, percentages, file sizes, etc.
- **validators.ts**: Form validation and input validation utilities
- **constants.ts**: Unified constant configuration management

### Custom Hooks
- **useApi**: Encapsulates API calling logic, automatically manages loading and error states
- **useErrorHandler**: Unified error handling logic

### Common Components
- **ErrorBoundary**: React error boundary, captures and handles application-level errors
- **Loading**: Reusable loading component

### Type Definitions
- **types/index.ts**: Global TypeScript type definitions

### Configuration Optimization
- **tsconfig.json**: Added path alias configuration, simplified import paths
- **index.html**: SEO metadata and PWA configuration
- **Dockerfile**: Multi-stage build, optimized production deployment
- **Dockerfile.dev**: Dedicated development environment configuration
