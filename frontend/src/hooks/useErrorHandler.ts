import { useState, useCallback } from 'react';

interface UseErrorHandlerReturn {
  error: string | null;
  setError: (error: string | null) => void;
  clearError: () => void;
  handleError: (error: any) => void;
}

/**
 * Custom hook for error handling
 */
export const useErrorHandler = (): UseErrorHandlerReturn => {
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const handleError = useCallback((error: any) => {
    if (error?.response?.data?.detail) {
      setError(error.response.data.detail);
    } else if (error?.response?.data?.message) {
      setError(error.response.data.message);
    } else if (error?.message) {
      setError(error.message);
    } else {
      setError('An unknown error occurred, please try again later');
    }
  }, []);

  return {
    error,
    setError,
    clearError,
    handleError
  };
};

