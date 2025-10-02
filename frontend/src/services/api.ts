const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || 'supersecretapexkey';

export interface AskRequest {
  question: string;
  lang: string;
  top_k?: number;
}

export interface Source {
  title: string;
  snippet: string;
  url: string;
}

export interface AskResponse {
  answer: string;
  sources: Source[];
  latency_ms: number;
}

export interface InsightsRequest {
  lat: number;
  lon: number;
  crop: string;
  lang?: string;
  use_ml_forecast?: boolean;
}

export interface InsightsResponse {
  forecast: {
    next_5_days?: {
      rainfall_mm: number;
      temp_avg_c: number;
      humidity_pct: number;
    };
    next_7_days?: {
      total_rainfall_mm: number;
      avg_temp_c: number;
      precipitation_probability: number;
    };
    model?: string;
    [key: string]: any;
  };
  soil: {
    texture?: string;
    ph?: number;
    organic_carbon_pct?: number;
    summary?: {
      texture?: string;
      pH?: number;
      ph?: number;
      organic_carbon_pct?: number;
      sand_pct?: number;
      bulk_density?: number;
      cec?: number;
    };
    macronutrients?: {
      nitrogen_pct?: number;
      phosphorus_ppm?: number;
      potassium_ppm?: number;
    };
    source?: string;
    [key: string]: any;
  };
  tips: string[];
  crop?: string;
  location?: {
    lat: number;
    lon: number;
  };
}

export interface IndexDocRequest {
  title: string;
  text_md: string;
  lang?: string;
  country?: string;
}

export interface IndexDocResponse {
  message: string;
  doc_id?: number;
}

export interface HealthResponse {
  status: string;
  index_loaded?: boolean;
  num_documents?: number;
  num_chunks?: number;
  translation_available?: boolean;
  error?: string;
}

export interface CropListResponse {
  crops: string[];
}

export class ApiError extends Error {
  status?: number;
  response?: any;
  
  constructor(message: string, status?: number, response?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.response = response;
  }
}

async function fetchWithAuth<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    'x-api-key': API_KEY,
    ...options.headers,
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorData;
      try {
        errorData = JSON.parse(errorText);
      } catch {
        errorData = { detail: errorText };
      }
      
      throw new ApiError(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      0
    );
  }
}

export const apiService = {
  async ask(request: AskRequest): Promise<AskResponse> {
    return fetchWithAuth<AskResponse>('/ask', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  async getInsights(request: InsightsRequest): Promise<InsightsResponse> {
    const params = new URLSearchParams({
      lat: request.lat.toString(),
      lon: request.lon.toString(),
      crop: request.crop,
      lang: request.lang || 'en',
      use_ml_forecast: (request.use_ml_forecast || false).toString(),
    });

    return fetchWithAuth<InsightsResponse>(`/insights?${params}`);
  },

  async indexDocument(request: IndexDocRequest): Promise<IndexDocResponse> {
    return fetchWithAuth<IndexDocResponse>('/index_doc', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  async getCrops(): Promise<CropListResponse> {
    return fetchWithAuth<CropListResponse>('/crops');
  },

  async getHealth(): Promise<HealthResponse> {
    return fetchWithAuth<HealthResponse>('/health');
  },

  async getRoot(): Promise<{ service: string; status: string; version: string }> {
    return fetchWithAuth<{ service: string; status: string; version: string }>('/');
  },
};

export default apiService;
