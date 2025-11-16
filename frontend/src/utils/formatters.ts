/**
 * Utility functions for formatting data
 */

/**
 * Format date to local string
 */
export const formatDate = (date: string | Date): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleString('en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

/**
 * Format number to percentage
 */
export const formatPercentage = (value: number, decimals: number = 1): string => {
  return `${(value * 100).toFixed(decimals)}%`;
};

/**
 * Format number with specified decimals
 */
export const formatNumber = (value: number | null | undefined, decimals: number = 2): string => {
  if (value === null || value === undefined) return 'N/A';
  return value.toFixed(decimals);
};

/**
 * Format confidence score
 */
export const formatConfidence = (confidence: number): string => {
  return formatPercentage(confidence, 1);
};

/**
 * Format similarity score
 */
export const formatSimilarity = (similarity: number): string => {
  return formatPercentage(similarity, 1);
};

/**
 * Format file size
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

/**
 * Truncate text with ellipsis
 */
export const truncateText = (text: string, maxLength: number = 100): string => {
  if (text.length <= maxLength) return text;
  return `${text.substring(0, maxLength)}...`;
};

/**
 * Capitalize first letter
 */
export const capitalize = (text: string): string => {
  if (!text) return text;
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
};

/**
 * Format biomolecule type display
 */
export const formatBiomoleculeType = (type: string): string => {
  const typeMap: { [key: string]: string } = {
    protein: 'Protein',
    peptide: 'Peptide',
    polysaccharide: 'Polysaccharide'
  };
  return typeMap[type] || type;
};

/**
 * Format property type display
 */
export const formatPropertyType = (type: string): string => {
  const typeMap: { [key: string]: string } = {
    stability: 'Stability',
    solubility: 'Solubility',
    aggregation: 'Aggregation'
  };
  return typeMap[type] || type;
};

/**
 * Format prediction result display
 */
export const formatPredictionResult = (result: string): string => {
  const resultMap: { [key: string]: string } = {
    Good: 'Good',
    Bad: 'Bad',
    stable: 'Stable',
    unstable: 'Unstable'
  };
  return resultMap[result] || result;
};

