/**
 * Global type definitions
 */

/**
 * User type
 */
export interface User {
  id: string;
  name: string;
  email: string;
  role: 'user' | 'admin';
}

/**
 * API Response wrapper
 */
export interface ApiResponse<T> {
  status: string;
  data?: T;
  message?: string;
  count?: number;
}

/**
 * Error response
 */
export interface ErrorResponse {
  detail?: string;
  error_code?: string;
  message?: string;
  details?: any;
}

/**
 * Loading state
 */
export interface LoadingState {
  loading: boolean;
  error: string | null;
}

/**
 * Select option
 */
export interface SelectOption {
  value: string;
  label: string;
}

/**
 * Pagination params
 */
export interface PaginationParams {
  page: number;
  pageSize: number;
}

/**
 * Sort params
 */
export interface SortParams {
  field: string;
  order: 'asc' | 'desc';
}

/**
 * Filter params
 */
export interface FilterParams {
  [key: string]: any;
}

/**
 * File upload result
 */
export interface FileUploadResult {
  url: string;
  filename: string;
  size: number;
}

/**
 * Chart data point
 */
export interface ChartDataPoint {
  name: string;
  value: number;
  [key: string]: any;
}

/**
 * Statistics summary
 */
export interface StatisticsSummary {
  total: number;
  good: number;
  bad: number;
  avgConfidence: number;
}

