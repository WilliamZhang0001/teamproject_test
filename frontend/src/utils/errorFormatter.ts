/**
 * Error formatting utilities for user-friendly error messages
 */
import { PARAMETER_LABELS } from '../config/constants';

interface ValidationError {
  field: string;
  code: string;
  message: string;
  expected?: { min?: number; max?: number };
  actual?: number | string;
}

interface ErrorResponse {
  message?: string;
  context?: string;
  errors?: ValidationError[];
  status?: string;
  detail?: string | ErrorResponse;
}

/**
 * Format validation error to user-friendly message
 */
export function formatValidationError(error: any): string {
  // Handle string errors - may contain Python dict-like string
  if (typeof error === 'string') {
    // Check if it contains Python dict-like format with 'errors' key
    if (error.includes("'errors'") || error.includes('"errors"')) {
      // Try to extract and parse the error structure
      try {
        // Replace Python dict syntax with JSON syntax
        let jsonStr = error
          .replace(/'/g, '"')  // Replace single quotes with double quotes
          .replace(/True/g, 'true')
          .replace(/False/g, 'false')
          .replace(/None/g, 'null');
        
        // Try to find the JSON-like part
        const jsonMatch = jsonStr.match(/\{[^}]*"errors"[^}]*\}/s);
        if (jsonMatch) {
          const parsed = JSON.parse(jsonMatch[0]);
          return formatValidationError(parsed);
        }
      } catch {
        // If parsing fails, continue to default handling
      }
    }
    
    // Try to parse if it looks like JSON
    if (error.startsWith('{') || error.startsWith('[')) {
      try {
        const parsed = JSON.parse(error);
        return formatValidationError(parsed);
      } catch {
        return error;
      }
    }
    
    // If it contains "422" and validation info, try to extract useful info
    if (error.includes('Parameter validation failed') || error.includes('validation failed')) {
      return 'Input validation failed. Please check that all parameter values are within the allowed ranges.';
    }
    
    return error;
  }

  // Handle error response from API
  // Try multiple paths to find error data
  let errorData = error?.response?.data?.detail || error?.response?.data || error?.detail || error;

  // If detail is a string, try to parse it
  if (typeof errorData === 'string') {
    const originalErrorData = errorData; // Keep original for fallback
    
    // Check for Python dict-like format with single quotes (common from FastAPI)
    if (errorData.includes("'errors'") || (errorData.includes("'message'") && errorData.includes("'errors'"))) {
      try {
        // Replace Python dict syntax with JSON syntax
        let jsonStr = errorData
          .replace(/'/g, '"')  // Replace single quotes with double quotes
          .replace(/True/g, 'true')
          .replace(/False/g, 'false')
          .replace(/None/g, 'null');
        
        // Remove trailing commas before } or ]
        jsonStr = jsonStr.replace(/,(\s*[}\]])/g, '$1');
        
        // Try to find and parse the full object (handle nested structures)
        const fullMatch = jsonStr.match(/\{[\s\S]*\}/);
        if (fullMatch) {
          const parsed = JSON.parse(fullMatch[0]);
          // Recursively process the parsed object
          return formatValidationError(parsed);
        }
      } catch (parseError) {
        // If full object parsing fails, try regex extraction as fallback
        // Extract errors array directly from string
        const errorsRegex = /'errors':\s*\[([^\]]+)\]/;
        const errorsMatch = originalErrorData.match(errorsRegex);
        
        if (errorsMatch) {
          // Extract individual error objects
          const errorStr = errorsMatch[1];
          const fieldMatch = errorStr.match(/'field':\s*'([^']+)'/);
          const codeMatch = errorStr.match(/'code':\s*'([^']+)'/);
          const actualMatch = errorStr.match(/'actual':\s*([^,}]+)/);
          const minMatch = errorStr.match(/'min':\s*([^,}]+)/);
          
          if (fieldMatch && codeMatch) {
            const field = fieldMatch[1];
            const code = codeMatch[1];
            const fieldName = PARAMETER_LABELS[field] || field;
            
            if (code === 'below_minimum' && actualMatch && minMatch) {
              return `${fieldName} is ${actualMatch[1].trim()}, but must be at least ${minMatch[1].trim()}`;
            } else if (code === 'above_maximum') {
              const maxMatch = errorStr.match(/'max':\s*([^,}]+)/);
              if (maxMatch && actualMatch) {
                return `${fieldName} is ${actualMatch[1].trim()}, but must be at most ${maxMatch[1].trim()}`;
              }
            }
          }
        }
        
        // Final fallback for validation errors
        if (originalErrorData.includes('Parameter validation failed') || originalErrorData.includes('validation failed')) {
          return 'Input validation failed. Please check that all parameter values are within the allowed ranges.';
        }
      }
    }
    
    // Try standard JSON parsing (for proper JSON strings)
    if ((originalErrorData.startsWith('{') || originalErrorData.startsWith('[')) && !originalErrorData.includes("'")) {
      try {
        const parsed = JSON.parse(originalErrorData);
        // Recursively process the parsed object
        return formatValidationError(parsed);
      } catch {
        // If JSON parsing fails and contains validation info
        if (originalErrorData.includes('Parameter validation failed') || originalErrorData.includes('validation failed')) {
          return 'Input validation failed. Please check that all parameter values are within the allowed ranges.';
        }
        return originalErrorData;
      }
    }
    
    // If it's a plain string without JSON structure
    if (!originalErrorData.includes('{') && !originalErrorData.includes("'")) {
      return originalErrorData;
    }
    
    // Default fallback for string errors
    return originalErrorData;
  }

  // Handle structured error response
  if (errorData && typeof errorData === 'object') {
    const errorObj: ErrorResponse = errorData;

    // Check if it's a validation error with errors array
    if (errorObj.errors && Array.isArray(errorObj.errors) && errorObj.errors.length > 0) {
      const errorMessages = errorObj.errors.map(formatSingleError);
      if (errorMessages.length === 1) {
        return errorMessages[0];
      }
      return 'Please fix the following errors:\n• ' + errorMessages.join('\n• ');
    }

    // Fallback to message if available
    if (errorObj.message) {
      return errorObj.message;
    }

    // Fallback to detail if available
    if (errorObj.detail) {
      return typeof errorObj.detail === 'string' ? errorObj.detail : formatValidationError(errorObj.detail);
    }
  }

  // Default error message
  return 'An error occurred. Please check your input and try again.';
}

/**
 * Format a single validation error
 */
function formatSingleError(error: ValidationError): string {
  const fieldName = PARAMETER_LABELS[error.field] || error.field;
  
  switch (error.code) {
    case 'below_minimum':
      if (error.expected?.min !== undefined && error.actual !== undefined) {
        return `${fieldName} is ${error.actual}, but must be at least ${error.expected.min}`;
      }
      return `${fieldName} is below the minimum allowed value`;
    
    case 'above_maximum':
      if (error.expected?.max !== undefined && error.actual !== undefined) {
        return `${fieldName} is ${error.actual}, but must be at most ${error.expected.max}`;
      }
      return `${fieldName} is above the maximum allowed value`;
    
    case 'out_of_range':
      if (error.expected?.min !== undefined && error.expected?.max !== undefined && error.actual !== undefined) {
        return `${fieldName} is ${error.actual}, but must be between ${error.expected.min} and ${error.expected.max}`;
      }
      return `${fieldName} is out of the allowed range`;
    
    case 'missing_required':
      return `${fieldName} is required but was not provided`;
    
    case 'invalid_type':
      return `${fieldName} has an invalid type. Expected a number`;
    
    case 'invalid_format':
      return `${fieldName} has an invalid format`;
    
    default:
      // Use the message if available, otherwise provide a generic one
      if (error.message) {
        return `${fieldName}: ${error.message}`;
      }
      return `${fieldName} validation failed`;
  }
}

/**
 * Format general API error to user-friendly message
 */
export function formatApiError(error: any): string {
  // For 422 errors, prioritize validation error formatting
  const status = error?.response?.status;
  if (status === 422) {
    const validationMsg = formatValidationError(error);
    if (validationMsg && validationMsg !== 'An error occurred. Please check your input and try again.') {
      return validationMsg;
    }
    return 'Validation failed. Please check your input.';
  }

  // Try validation error first for other cases
  const validationMsg = formatValidationError(error);
  if (validationMsg && validationMsg !== 'An error occurred. Please check your input and try again.') {
    return validationMsg;
  }

  // Handle HTTP status codes
  if (status) {
    switch (status) {
      case 400:
        return 'Invalid request. Please check your input.';
      case 401:
        return 'Authentication required. Please log in.';
      case 403:
        return 'Access denied. You do not have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 422:
        return 'Validation failed. Please check your input.';
      case 429:
        return 'Too many requests. Please wait a moment and try again.';
      case 500:
        return 'Server error. Please try again later.';
      case 503:
        return 'Service temporarily unavailable. Please try again later.';
      default:
        return `Request failed (${status}). Please try again.`;
    }
  }

  // Fallback - check if error message contains validation info
  const errorMessage = error?.message || '';
  if (errorMessage.includes('422') || errorMessage.includes('validation failed') || errorMessage.includes('Parameter validation')) {
    return formatValidationError(error) || 'Input validation failed. Please check that all parameter values are within the allowed ranges.';
  }

  // Fallback
  return errorMessage || 'An unexpected error occurred. Please try again.';
}

