/**
 * Application constants and configuration
 */

export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const APP_NAME = 'DoE-Assist';
export const APP_DESCRIPTION = 'Intelligent Parameter Reduction for Experimental Design';

// Biomolecule types
export const BIOMOLECULE_TYPES = [
  { value: 'protein', label: 'Protein' },
  { value: 'peptide', label: 'Peptide' },
  { value: 'polysaccharide', label: 'Polysaccharide' }
] as const;

// Experiment/Property types
export const PROPERTY_TYPES = [
  { value: 'stability', label: 'Stability' },
  { value: 'solubility', label: 'Solubility' },
  { value: 'aggregation', label: 'Aggregation' }
] as const;

// Prediction types
export const PREDICTION_TYPES = [
  { value: 'classification', label: 'Classification' },
  { value: 'parameter', label: 'Parameter Prediction' }
] as const;

// Parameter labels mapping
export const PARAMETER_LABELS: { [key: string]: string } = {
  pH: 'pH',
  temperature_c: 'Temperature (°C)',
  concentration_mg_ml: 'Concentration (mg/mL)',
  ionic_strength_mM: 'Ionic Strength (mM)',
  additive: 'Additive',
  time_min: 'Time (minutes)',
  shear_rate_s1: 'Shear Rate (s⁻¹)',
  pressure_bar: 'Pressure (bar)'
};

// Validation ranges (based on Parameter_Input_Specification.md)
export const VALIDATION_RANGES: { [key: string]: { min: number; max: number; step?: number } } = {
  pH: { min: 0, max: 14, step: 0.1 },
  temperature_c: { min: -20, max: 150 },
  concentration_mg_ml: { min: 0.001, max: 1000 },
  ionic_strength_mM: { min: 0, max: 5000 },
  time_min: { min: 0, max: 100000 },
  shear_rate_s1: { min: 0, max: 10000 },
  pressure_bar: { min: 0, max: 10000 }
};

// Parameter helper texts (range hints for users)
export const PARAMETER_HELPER_TEXTS: { [key: string]: string } = {
  pH: 'Range: 0 - 14',
  temperature_c: 'Range: -20°C - 150°C',
  concentration_mg_ml: 'Range: 0.001 - 1000 mg/mL (minimum: 0.001)',
  ionic_strength_mM: 'Range: 0 - 5000 mM',
  additive: 'Multiple additives can be separated by commas (e.g., glycerol, sucrose)',
  time_min: 'Range: 0 - 100000 minutes',
  shear_rate_s1: 'Range: 0 - 10000 s⁻¹',
  pressure_bar: 'Range: 0 - 10000 bar (1 bar ≈ 1 atm)'
};

// Default values
export const DEFAULT_TOP_K = 3;
export const DEFAULT_HISTORY_LIMIT = 50;

// Timeout settings (ms)
export const TIMEOUTS = {
  REQUEST: 30000,
  UPLOAD: 120000
};

// Pagination
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [10, 25, 50, 100]
};

// Routes
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  QUERY: '/query',
  INPUT: '/input',
  UPLOAD: '/upload',
  RESULTS: '/results',
  FEEDBACK: '/feedback'
} as const;

// LocalStorage keys
export const STORAGE_KEYS = {
  TOKEN: 'token',
  USER: 'user'
} as const;

// Error messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network connection failed, please check your network settings',
  UNAUTHORIZED: 'Unauthorized access, please log in again',
  FORBIDDEN: 'Insufficient permissions',
  NOT_FOUND: 'Resource not found',
  SERVER_ERROR: 'Server error, please try again later',
  TIMEOUT: 'Request timeout, please try again',
  UNKNOWN: 'Unknown error, please try again later'
} as const;

// Success messages
export const SUCCESS_MESSAGES = {
  LOGIN: 'Login successful',
  REGISTER: 'Registration successful',
  LOGOUT: 'Logged out successfully',
  UPLOAD: 'File uploaded successfully',
  PREDICTION: 'Prediction completed',
  FEEDBACK: 'Feedback submitted successfully'
} as const;

