import { useState, useCallback } from 'react';

interface UseApiOptions {
  onSuccess?: (data: any) => void;
  onError?: (error: any) => void;
}

interface UseApiReturn<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  execute: (...args: any[]) => Promise<T | null>;
  reset: () => void;
}

/**
 * Custom hook for API calls
 */
export const useApi = <T = any>(
  apiFunction: (...args: any[]) => Promise<T>,
  options?: UseApiOptions
): UseApiReturn<T> => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (...args: any[]) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiFunction(...args);
      setData(result);
      options?.onSuccess?.(result);
      return result;
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || 'Request failed';
      setError(errorMessage);
      options?.onError?.(err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [apiFunction, options]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    data,
    loading,
    error,
    execute,
    reset
  };
};

