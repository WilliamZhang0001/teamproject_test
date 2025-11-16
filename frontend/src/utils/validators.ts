/**
 * Utility functions for validation
 */

/**
 * Validate email format
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validate password strength
 */
export const isStrongPassword = (password: string): boolean => {
  // At least 6 characters
  return password.length >= 6;
};

/**
 * Validate pH value
 */
export const isValidPH = (value: number): boolean => {
  return value >= 0 && value <= 14;
};

/**
 * Validate temperature
 */
export const isValidTemperature = (value: number): boolean => {
  return value >= -50 && value <= 200;
};

/**
 * Validate positive number
 */
export const isValidPositiveNumber = (value: number): boolean => {
  return value >= 0;
};

/**
 * Validate biomolecule name
 */
export const isValidBiomoleculeName = (name: string): boolean => {
  return name.trim().length > 0;
};

/**
 * Get validation error message
 */
export const getValidationError = (field: string, value: any): string | null => {
  switch (field) {
    case 'email':
      if (!isValidEmail(value)) {
        return 'Please enter a valid email address';
      }
      return null;
    case 'password':
      if (!isStrongPassword(value)) {
        return 'Password must be at least 6 characters';
      }
      return null;
    case 'biomoleculeName':
      if (!isValidBiomoleculeName(value)) {
        return 'Please enter a biomolecule name';
      }
      return null;
    case 'pH':
      if (value !== null && value !== undefined && value !== '' && !isValidPH(value)) {
        return 'pH value must be between 0 and 14';
      }
      return null;
    case 'temperature':
      if (value !== null && value !== undefined && value !== '' && !isValidTemperature(value)) {
        return 'Temperature must be between -50 and 200°C';
      }
      return null;
    default:
      return null;
  }
};

/**
 * Validate experiment input
 */
export const validateExperimentInput = (input: any): { valid: boolean; errors: string[] } => {
  const errors: string[] = [];
  
  if (!isValidBiomoleculeName(input.biomolecule_name)) {
    errors.push('Biomolecule name cannot be empty');
  }
  
  if (input.pH !== null && input.pH !== undefined && input.pH !== '' && !isValidPH(input.pH)) {
    errors.push('pH value must be between 0 and 14');
  }
  
  if (input.temperature !== null && input.temperature !== undefined && input.temperature !== '' && 
      !isValidTemperature(input.temperature)) {
    errors.push('Temperature must be between -50 and 200°C');
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
};

/**
 * Validate selected parameters for parameter prediction
 */
export const validateParameterPrediction = (selectedParameters: string[]): { valid: boolean; error: string | null } => {
  if (selectedParameters.length === 0) {
    return {
      valid: false,
      error: 'Please select at least one parameter to predict'
    };
  }
  return {
    valid: true,
    error: null
  };
};

/**
 * Sanitize input string
 */
export const sanitizeString = (str: string): string => {
  return str.trim().replace(/[<>]/g, '');
};

/**
 * Validate parameter value against validation ranges
 * Returns error message if invalid, null if valid
 */
export const validateParameterValue = (
  field: string, 
  value: number | string | '',
  validationRanges: { [key: string]: { min: number; max: number; step?: number } },
  fieldLabel?: string
): string | null => {
  // Empty values are allowed (optional parameters)
  if (value === '' || value === null || value === undefined) {
    return null;
  }

  // For non-numeric fields (like additive), no range validation needed
  if (typeof value === 'string') {
    return null;
  }

  // Get validation range for the field
  const range = validationRanges[field];
  if (!range) {
    return null; // No validation range defined, allow it
  }

  // Use provided label or fall back to field name
  const displayName = fieldLabel || field;

  // Check if value is a valid number
  if (typeof value !== 'number' || isNaN(value)) {
    return `${displayName} must be a valid number`;
  }

  // Check minimum
  if (value < range.min) {
    return `${displayName} is ${value}, but must be at least ${range.min}`;
  }

  // Check maximum
  if (value > range.max) {
    return `${displayName} is ${value}, but must be at most ${range.max}`;
  }

  return null; // Valid
};

/**
 * Get field label for error messages
 */
export const getFieldLabel = (field: string, labels: { [key: string]: string }): string => {
  return labels[field] || field;
};

