import { NextRequest } from 'next/server';
import { GET, POST } from '@/app/api/models/load/route';

// Mock the model selection service
jest.mock('@/lib/model-selection-service', () => ({
  modelSelectionService: {
    getAvailableModels: jest.fn(),
    getSelectionStats: jest.fn(),
    selectModel: jest.fn(),
  }
}));

describe('/api/models/load', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('POST - Load Model', () => {
    it('should load a model successfully', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        {
          id: 'test-model',
          name: 'Test Model',
          provider: 'llama-cpp',
          type: 'text_generation',
          capabilities: ['chat', 'text-generation']
        }
      ]);

      (modelSelectionService.getSelectionStats as jest.Mock).mockResolvedValue({
        selectedModel: null,
        isLoading: false
      });

      (modelSelectionService.selectModel as jest.Mock).mockResolvedValue({
        success: true
      });

      const request = new NextRequest('http://localhost:3000/api/models/load', {
        method: 'POST',
        body: JSON.stringify({
          model_id: 'test-model',
          options: { preserve_context: true }
        })
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.success).toBe(true);
      expect(data.model_id).toBe('test-model');
      expect(data.provider).toBe('llama-cpp');
      expect(data.capabilities).toEqual(['chat', 'text-generation']);
      expect(data.load_time).toBeGreaterThan(0);
      expect(response.headers.get('X-Model-Provider')).toBe('llama-cpp');
    });

    it('should return error for missing model_id', async () => {
      const request = new NextRequest('http://localhost:3000/api/models/load', {
        method: 'POST',
        body: JSON.stringify({})
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe('Missing required field: model_id');
    });

    it('should return error for non-existent model', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([]);

      const request = new NextRequest('http://localhost:3000/api/models/load', {
        method: 'POST',
        body: JSON.stringify({ model_id: 'non-existent' })
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(404);
      expect(data.error).toBe('Model not found');
    });

    it('should handle already loaded model', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        {
          id: 'loaded-model',
          name: 'Loaded Model',
          provider: 'llama-cpp',
          capabilities: ['chat']
        }
      ]);

      (modelSelectionService.getSelectionStats as jest.Mock).mockResolvedValue({
        selectedModel: { id: 'loaded-model' }
      });

      const request = new NextRequest('http://localhost:3000/api/models/load', {
        method: 'POST',
        body: JSON.stringify({ model_id: 'loaded-model' })
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.success).toBe(true);
      expect(data.message).toBe('Model already loaded');
    });

    it('should handle model loading failure', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        { id: 'failing-model', name: 'Failing Model', provider: 'llama-cpp' }
      ]);

      (modelSelectionService.getSelectionStats as jest.Mock).mockResolvedValue({
        selectedModel: null
      });

      (modelSelectionService.selectModel as jest.Mock).mockResolvedValue({
        success: false,
        error: 'Loading failed'
      });

      const request = new NextRequest('http://localhost:3000/api/models/load', {
        method: 'POST',
        body: JSON.stringify({ model_id: 'failing-model' })
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(500);
      expect(data.error).toBe('Model loading failed');
      expect(data.message).toBe('Loading failed');
    });
  });

  describe('GET - Load Status', () => {
    it('should return current loading status', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getSelectionStats as jest.Mock).mockResolvedValue({
        selectedModel: { id: 'current-model', name: 'Current Model' },
        isLoading: false,
        lastLoadTime: 1500
      });

      const request = new NextRequest('http://localhost:3000/api/models/load');
      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.currently_loaded).toEqual({ id: 'current-model', name: 'Current Model' });
      expect(data.loading_status).toBe(false);
      expect(data.last_load_time).toBe(1500);
      expect(data.available_providers).toContain('llama-cpp');
      expect(data.available_providers).toContain('stable-diffusion');
    });

    it('should handle status check errors', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getSelectionStats as jest.Mock).mockRejectedValue(
        new Error('Stats unavailable')
      );

      const request = new NextRequest('http://localhost:3000/api/models/load');
      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(500);
      expect(data.error).toBe('Status check failed');
      expect(data.message).toBe('Stats unavailable');
    });
  });
});