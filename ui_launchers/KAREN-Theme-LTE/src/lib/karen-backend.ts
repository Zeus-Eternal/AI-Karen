/**
 * Karen Backend Client
 * API client for communicating with Karen backend services
 */

export interface BackendConfig {
  baseUrl: string;
  timeout?: number;
  retries?: number;
  headers?: Record<string, string>;
}

export interface ApiResponse<T = unknown> {
  data: T;
  success: boolean;
  message?: string;
  error?: string;
}

export interface BackendRequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: Record<string, unknown>;
  timeout?: number;
}

class KarenBackend {
  private config: BackendConfig;
  private defaultHeaders: Record<string, string>;

  constructor(config: Partial<BackendConfig> = {}) {
    this.config = {
      baseUrl: process.env.NEXT_PUBLIC_KAREN_BACKEND_URL || 'http://localhost:8000',
      timeout: 30000,
      retries: 3,
      ...config
    };

    this.defaultHeaders = {
      'Content-Type': 'application/json',
      ...this.config.headers
    };
  }

  /**
   * Make authenticated request
   */
  async makeRequest<T>(endpoint: string, options: BackendRequestOptions = {}): Promise<T> {
    const url = `${this.config.baseUrl}${endpoint}`;
    const token = this.getAuthToken();

    const requestOptions: RequestInit = {
      method: options.method || 'GET',
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
        ...(token && { Authorization: `Bearer ${token}` })
      },
      ...(options.body && { body: JSON.stringify(options.body) }),
      signal: AbortSignal.timeout(options.timeout || this.config.timeout || 30000)
    };

    try {
      const response = await fetch(url, requestOptions);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: ApiResponse<T> = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Request failed');
      }

      return data.data;
    } catch (error) {
      console.error('Backend request failed:', error);
      throw error;
    }
  }

  /**
   * Make public request (no authentication)
   */
  async makeRequestPublic<T>(endpoint: string, options: BackendRequestOptions = {}): Promise<T> {
    const url = `${this.config.baseUrl}${endpoint}`;

    const requestOptions: RequestInit = {
      method: options.method || 'GET',
      headers: {
        ...this.defaultHeaders,
        ...options.headers
      },
      ...(options.body && { body: JSON.stringify(options.body) }),
      signal: AbortSignal.timeout(options.timeout || this.config.timeout || 30000)
    };

    try {
      const response = await fetch(url, requestOptions);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: ApiResponse<T> = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Request failed');
      }

      return data.data;
    } catch (error) {
      console.error('Public backend request failed:', error);
      throw error;
    }
  }

  /**
   * Upload file
   */
  async uploadFile<T>(endpoint: string, file: File, options: {
    onProgress?: (progress: number) => void;
    metadata?: Record<string, unknown>;
  } = {}): Promise<T> {
    const url = `${this.config.baseUrl}${endpoint}`;
    const token = this.getAuthToken();
    const formData = new FormData();

    formData.append('file', file);
    
    if (options.metadata) {
      formData.append('metadata', JSON.stringify(options.metadata));
    }

    const xhr = new XMLHttpRequest();
    
    return new Promise((resolve, reject) => {
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && options.onProgress) {
          const progress = (event.loaded / event.total) * 100;
          options.onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data: ApiResponse<T> = JSON.parse(xhr.responseText);
            if (data.success) {
              resolve(data.data);
            } else {
              reject(new Error(data.error || 'Upload failed'));
            }
          } catch (error) {
            reject(error);
          }
        } else {
          reject(new Error(`Upload failed: ${xhr.statusText}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed'));
      });

      xhr.open('POST', url);
      
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }
      
      xhr.send(formData);
    });
  }

  /**
   * Download file
   */
  async downloadFile(endpoint: string, filename?: string): Promise<Blob> {
    const url = `${this.config.baseUrl}${endpoint}`;
    const token = this.getAuthToken();

    const response = await fetch(url, {
      headers: {
        ...(token && { Authorization: `Bearer ${token}` })
      }
    });

    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`);
    }

    const blob = await response.blob();
    
    // Trigger download if filename provided
    if (filename) {
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
    }

    return blob;
  }

  /**
   * Get auth token from storage
   */
  private getAuthToken(): string | null {
    return localStorage.getItem('karen-auth-token') || sessionStorage.getItem('karen-auth-token');
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<BackendConfig>): void {
    this.config = { ...this.config, ...config };
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      ...this.config.headers
    };
  }

  /**
   * Get current configuration
   */
  getConfig(): BackendConfig {
    return { ...this.config };
  }
}

// Create singleton instance
let backendInstance: KarenBackend | null = null;

export function getKarenBackend(config?: Partial<BackendConfig>): KarenBackend {
  if (!backendInstance) {
    backendInstance = new KarenBackend(config);
  } else if (config) {
    backendInstance.updateConfig(config);
  }
  return backendInstance;
}

export default KarenBackend;
