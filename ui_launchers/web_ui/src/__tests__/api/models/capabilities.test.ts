import { NextRequest } from 'next/server';
import { GET } from '@/app/api/models/capabilities/route';

// Mock the model selection service
jest.mock('@/lib/model-selection-service', () => ({
  modelSelectionService: {
    getAvailableModels: jest.fn(),
  }
}));

describe('/api/models/capabilities', () => {
  beforeEach(() => {
    jest.clearAllMocks();

  describe('GET - Model Capabilities', () => {
    it('should return text model capabilities', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        {
          id: 'text-model',
          name: 'Text Model',
          provider: 'llama-cpp',
          type: 'text_generation',
          capabilities: ['chat', 'text-generation', 'code']
        }
      ]);

      const request = new NextRequest('http://localhost:3000/api/models/capabilities?model_id=text-model&include_parameters=true&include_compatibility=true');
      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.model_id).toBe('text-model');
      expect(data.provider).toBe('llama-cpp');
      expect(data.type).toBe('text_generation');
      expect(data.capabilities).toHaveLength(3);
      expect(data.capabilities[0].name).toBe('chat');
      expect(data.capabilities[0].supported_parameters).toContain('temperature');
      expect(data.supported_modes).toContain('text');
      expect(data.supported_modes).toContain('chat');
      expect(data.parameters.text_generation).toBeDefined();
      expect(data.parameters.text_generation.temperature).toBeDefined();
      expect(data.compatibility.streaming).toBe(true);
      expect(response.headers.get('X-Model-Type')).toBe('text_generation');

    it('should return image model capabilities', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        {
          id: 'image-model',
          name: 'Image Model',
          provider: 'stable-diffusion',
          type: 'image_generation',
          capabilities: ['text2img', 'img2img']
        }
      ]);

      const request = new NextRequest('http://localhost:3000/api/models/capabilities?model_id=image-model&include_parameters=true');
      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.model_id).toBe('image-model');
      expect(data.provider).toBe('stable-diffusion');
      expect(data.type).toBe('image_generation');
      expect(data.capabilities).toHaveLength(2);
      expect(data.capabilities[0].name).toBe('text2img');
      expect(data.capabilities[0].requirements.gpu_required).toBe(true);
      expect(data.supported_modes).toContain('image');
      expect(data.supported_modes).toContain('text2img');
      expect(data.parameters.image_generation).toBeDefined();
      expect(data.parameters.image_generation.width).toBeDefined();
      expect(data.parameters.image_generation.guidance_scale).toBeDefined();

    it('should return error for missing model_id', async () => {
      const request = new NextRequest('http://localhost:3000/api/models/capabilities');
      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe('Missing required parameter: model_id');

    it('should return error for non-existent model', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([]);

      const request = new NextRequest('http://localhost:3000/api/models/capabilities?model_id=non-existent');
      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(404);
      expect(data.error).toBe('Model not found');

    it('should return minimal response when parameters not requested', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        {
          id: 'minimal-model',
          name: 'Minimal Model',
          provider: 'llama-cpp',
          type: 'text_generation',
          capabilities: ['chat']
        }
      ]);

      const request = new NextRequest('http://localhost:3000/api/models/capabilities?model_id=minimal-model');
      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.parameters).toEqual({});
      expect(data.compatibility.multimodal).toBe(false);
      expect(data.compatibility.streaming).toBe(false);
      expect(data.compatibility.batch_processing).toBe(false);

    it('should handle embedding model capabilities', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        {
          id: 'embedding-model',
          name: 'Embedding Model',
          provider: 'transformers',
          type: 'embedding',
          capabilities: ['embedding']
        }
      ]);

      const request = new NextRequest('http://localhost:3000/api/models/capabilities?model_id=embedding-model&include_parameters=true');
      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.type).toBe('embedding');
      expect(data.supported_modes).toContain('embedding');
      expect(data.parameters.embedding).toBeDefined();
      expect(data.parameters.embedding.normalize).toBeDefined();
      expect(data.parameters.embedding.batch_size).toBeDefined();

    it('should set appropriate cache headers', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        {
          id: 'cached-model',
          name: 'Cached Model',
          provider: 'llama-cpp',
          type: 'text_generation',
          capabilities: ['chat']
        }
      ]);

      const request = new NextRequest('http://localhost:3000/api/models/capabilities?model_id=cached-model');
      const response = await GET(request);

      expect(response.headers.get('Cache-Control')).toBe('public, max-age=3600');
      expect(response.headers.get('X-Model-Provider')).toBe('llama-cpp');

    it('should handle service errors gracefully', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockRejectedValue(
        new Error('Service unavailable')
      );

      const request = new NextRequest('http://localhost:3000/api/models/capabilities?model_id=error-model');
      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(500);
      expect(data.error).toBe('Failed to fetch model capabilities');
      expect(data.message).toBe('Service unavailable');


