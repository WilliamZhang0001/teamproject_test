import api from './api';
import { formatApiError } from '../utils/errorFormatter';

export interface ExperimentInput {
  biomolecule_type?: string;
  biomolecule_name: string;
  property?: string;
  experiment_type?: string;
  pH?: number;
  temperature_c?: number;
  concentration_mg_ml?: number;
  ionic_strength_mM?: number;
  additive?: string;
  time_min?: number;
  shear_rate_s1?: number;
  pressure_bar?: number;
}

export interface PredictionResult {
  prediction: 'stable' | 'unstable' | 'Good' | 'Bad' | string;
  confidence: number;
  probabilities?: { [key: string]: number };
  model_used?: string;
  recommendation?: string;
}

export interface ParameterPrediction {
  recommended_value: number;
  min: number;
  max: number;
  median: number;
}

export interface ParameterPredictionResult {
  predicted_parameters?: { [key: string]: ParameterPrediction };
  confidence: number;
}

export interface LiteratureRecord {
  id: number;
  similarity_score: number;
  // Fields can be at top level or nested in literature object
  title?: string;
  authors?: string;
  pub_year?: number;
  doi?: string;
  literature?: {
    doi?: string;
    title?: string;
    authors?: string;
    pub_year?: number;
  };
  parameters: { [key: string]: any };
  outcome_text?: string;
  confidence?: number;
}

export interface ExperimentResponse {
  status: string;
  data: {
    prediction?: string;
    confidence?: number;
    similar_literature?: LiteratureRecord[];
    predicted_parameters?: { [key: string]: ParameterPrediction };
  };
}

export interface UnifiedPredictResponse {
  prediction?: string;
  confidence?: number;
  probabilities?: { [key: string]: number };
  model_used?: string;
  recommendation?: string;
  predicted_parameters?: { [key: string]: any };
  literature_evidence?: LiteratureRecord[];
  prediction_id?: string;
}

export interface ExperimentHistory {
  id: number;
  user_id: number;
  biomolecule_type: string;
  biomolecule_name: string;
  experiment_type: string;
  prediction_type: string;
  prediction_result: any;
  confidence: number;
  recommended_literature: any[];
  created_at: string;
}

export interface JobCreateRequest {
  task_type?: string;
  payload: any;
}

export interface JobStatus {
  job_id: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCEEDED' | 'FAILED';
  result_json?: any;
  result_url?: string | null;
  error?: string;
}

export interface EnhancedPredictionResponse {
  prediction?: any;
  evidence?: {
    top_similar_literature?: LiteratureRecord[];
    count?: number;
  };
  input_parameters?: any;
}

export const experimentService = {
  /**
   * Classification prediction - Evaluate if experimental conditions are good or bad
   */
  async predictClassification(
    input: ExperimentInput,
    topK: number = 3
  ): Promise<ExperimentResponse> {
    try {
      const response = await api.post<ExperimentResponse>(
        `/api/v1/experiments/predict-classification?top_k=${topK}`,
        {
          ...input,
          experiment_type: input.experiment_type || input.property,
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(formatApiError(error));
    }
  },

  /**
   * Parameter prediction - Predict values for specified parameters
   */
  async predictParameter(
    input: ExperimentInput,
    predictParameters: string[],
    topK: number = 3
  ): Promise<ExperimentResponse> {
    try {
      const response = await api.post<ExperimentResponse>(
        '/api/v1/experiments/predict-parameter',
        {
          input: {
            ...input,
            experiment_type: input.experiment_type || input.property,
          },
          predict_parameters: predictParameters,
          top_k: topK,
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(formatApiError(error));
    }
  },

  /**
   * Unified prediction endpoint - /api/v1/predict
   */
  async unifiedPredict(
    input: ExperimentInput,
    recommendParameters?: string[]
  ): Promise<UnifiedPredictResponse> {
    try {
      const response = await api.post<UnifiedPredictResponse>(
        '/api/v1/predict',
        {
          ...input,
          property: input.property || input.experiment_type || 'stability',
          recommend_parameters: recommendParameters,
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(formatApiError(error));
    }
  },

  /**
   * Get experiment history
   */
  async getHistory(limit: number = 100): Promise<ExperimentHistory[]> {
    try {
      const response = await api.get<{ status: string; count: number; data: ExperimentHistory[] }>(
        `/api/v1/experiments/history?limit=${limit}`
      );
      return response.data.data;
    } catch (error: any) {
      throw new Error(formatApiError(error));
    }
  },

  /**
   * Get a single experiment record
   */
  async getExperiment(experimentId: number): Promise<ExperimentHistory> {
    try {
      const response = await api.get<{ status: string; data: ExperimentHistory }>(
        `/api/v1/experiments/${experimentId}`
      );
      return response.data.data;
    } catch (error: any) {
      throw new Error(formatApiError(error));
    }
  },

  /**
   * Delete all experiment history for current user
   */
  async deleteHistory(): Promise<{ status: string; message: string; deleted_count: number }> {
    try {
      const response = await api.delete<{ status: string; message: string; deleted_count: number }>(
        `/api/v1/experiments/history`
      );
      return response.data;
    } catch (error: any) {
      throw new Error(formatApiError(error));
    }
  },

  /**
   * Batch CSV prediction upload
   */
  async predictCSV(
    file: File,
    predictionType: 'classification' | 'parameter' = 'classification',
    topK: number = 3,
    predictParameters?: string[]
  ): Promise<Blob> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('prediction_type', predictionType);
      formData.append('top_k', topK.toString());
      
      if (predictionType === 'parameter' && predictParameters) {
        formData.append('predict_parameters', JSON.stringify(predictParameters));
      }

      const response = await api.post<Blob>(
        '/api/v1/experiments/predict-csv',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          responseType: 'blob',
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(formatApiError(error));
    }
  },

  /**
   * Search literature
   */
  async searchLiterature(input: Partial<ExperimentInput>, limit: number = 3): Promise<LiteratureRecord[]> {
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
      });
      
      if (input.biomolecule_name) params.append('biomolecule_name', input.biomolecule_name);
      if (input.experiment_type) params.append('property_type', input.experiment_type);
      if (input.property) params.append('property_type', input.property);
      if (input.pH !== undefined) params.append('pH', input.pH.toString());
      if (input.temperature_c !== undefined) params.append('temperature_c', input.temperature_c.toString());
      if (input.concentration_mg_ml !== undefined) params.append('concentration_mg_ml', input.concentration_mg_ml.toString());
      if (input.ionic_strength_mM !== undefined) params.append('ionic_strength_mM', input.ionic_strength_mM.toString());
      if (input.additive !== undefined && input.additive !== '') params.append('additive', input.additive);
      if (input.time_min !== undefined) params.append('time_min', input.time_min.toString());
      if (input.shear_rate_s1 !== undefined) params.append('shear_rate_s1', input.shear_rate_s1.toString());
      if (input.pressure_bar !== undefined) params.append('pressure_bar', input.pressure_bar.toString());

      const response = await api.get<{ status: string; count: number; results: LiteratureRecord[] }>(
        `/literature/search?${params.toString()}`
      );
      return response.data.results;
    } catch (error: any) {
      throw new Error(formatApiError(error));
    }
  },

  /**
   * Create async prediction job
   */
  async createAsyncJob(taskType: string, payload: any): Promise<{ job_id: string }> {
    try {
      const response = await api.post<{ job_id: string }>(
        '/api/v1/jobs',
        {
          task_type: taskType,
          payload
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to create async job');
    }
  },

  /**
   * Get async job status
   */
  async getJobStatus(jobId: string): Promise<JobStatus> {
    try {
      const response = await api.get<JobStatus>(`/api/v1/jobs/${jobId}`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to get job status');
    }
  },

  /**
   * Literature-enhanced prediction
   */
  async enhancePrediction(
    mlResult: any,
    userInput: any,
    topK: number = 3
  ): Promise<EnhancedPredictionResponse> {
    try {
      const response = await api.post<EnhancedPredictionResponse>(
        '/literature/enhance-prediction',
        {
          ml_result: mlResult,
          user_input: userInput,
          top_k: topK
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Prediction enhancement failed');
    }
  },

  /**
   * Get high-confidence literature
   */
  async getTopConfidenceLiterature(
    biomoleculeName?: string,
    propertyType: string = 'stability',
    limit: number = 3
  ): Promise<LiteratureRecord[]> {
    try {
      const params = new URLSearchParams({
        property_type: propertyType,
        limit: limit.toString()
      });
      
      if (biomoleculeName) params.append('biomolecule_name', biomoleculeName);

      const response = await api.get<{ status: string; count: number; results: LiteratureRecord[] }>(
        `/literature/top-confidence?${params.toString()}`
      );
      return response.data.results;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch top confidence literature');
    }
  },

  /**
   * Upload file (Base64 encoded)
   */
  async uploadFile(filename: string, content: string): Promise<{ file_id: string; filename: string }> {
    try {
      const response = await api.post<{ file_id: string; filename: string }>(
        '/api/v1/upload',
        {
          filename,
          content
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'File upload failed');
    }
  },
};

