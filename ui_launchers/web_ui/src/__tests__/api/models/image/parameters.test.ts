import { NextRequest } from 'next/server';
import { GET } from '@/app/api/models/image/parameters/[model_id]/route';

// Mock the model selection service
jest.mock('@/lib/model-selection-service', () => ({
  modelSelectionService: {
    getAvailableModels: jest.fn(),
  }
}));

describe('/api/models/image/parameters/[model_id]', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('GET - Image Model Parameters', () => {
    it('should return Stable Diffusion model parameters', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        {
          id: 'sd-v1-5',
          name: 'Stable Diffusion v1.5',
          provider: 'stable-diffusion',
          type: 'image_generation',
          capabilities: ['text2img', 'img2img'],
          metadata: { base_model: 'SD 1.5' }
        }
      ]);

      const request = new NextRequest('http://localhost:3000/api/models/image/parameters/sd-v1-5');
      const response = await GET(request, { params: { model_id: 'sd-v1-5' } });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.model_id).toBe('sd-v1-5');
      expect(data.model_name).toBe('Stable Diffusion v1.5');
      expect(data.provider).toBe('stable-diffusion');
      expect(data.supported_modes).toContain('text2img');
      expect(data.supported_modes).toContain('img2img');
      
      // Check parameters
      expect(data.parameters.prompt).toBeDefined();
      expect(data.parameters.prompt.required).toBe(true);
      expect(data.parameters.width).toBeDefined();
      expect(data.parameters.width.default).toBe(512);
      expect(data.parameters.height).toBeDefined();
      expect(data.parameters.steps).toBeDefined();
      expect(data.parameters.guidance_scale).toBeDefined();
      expect(data.parameters.strength).toBeDefined(); // Should have img2img parameter
      
      // Check presets
      expect(data.presets).toBeInstanceOf(Array);
      expect(data.presets.length).toBeGreaterThan(0);
      expect(data.presets[0].name).toBeDefined();
      expect(data.presets[0].parameters).toBeDefined();
      
      // Check limitations
      expect(data.limitations.max_batch_size).toBe(4);
      expect(data.limitations.memory_requirement_mb).toBeGreaterThan(0);
      
      expect(response.headers.get('X-Model-Provider')).toBe('stable-diffusion');
    });

    it('should return Flux model parameters with higher resolution support', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        {
          id: 'flux-dev',
          name: 'Flux Dev',
          provider: 'flux',
          type: 'image_generation',
          capabilities: ['text2img']
        }
      ]);

      const request = new NextRequest('http://localhost:3000/api/models/image/parameters/flux-dev');
      const response = await GET(request, { params: { model_id: 'flux-dev' } });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.provider).toBe('flux');
      expect(data.parameters.width.max).toBe(2048); // Flux supports higher resolution
      expect(data.parameters.height.max).toBe(2048);
      expect(data.parameters.guidance_scale.default).toBe(3.5); // Flux has different default
      expect(data.parameters.strength).toBeUndefined(); // No img2img support
      
      // Should have Flux-specific preset
      const fluxPreset = data.presets.find(p => p.name === 'Flux High-Res');
      expect(fluxPreset).toBeDefined();
      expect(fluxPreset.parameters.width).toBe(1024);
      expect(fluxPreset.parameters.height).toBe(1024);
    });

    it('should return SDXL model parameters with higher resolution defaults', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        {
          id: 'sdxl-base',
          name: 'SDXL Base',
          provider: 'stable-diffusion',
          type: 'image_generation',
          capabilities: ['text2img'],
          metadata: { base_model: 'SDXL' }
        }
      ]);

      const request = new NextRequest('http://localhost:3000/api/models/image/parameters/sdxl-base');
      const response = await GET(request, { params: { model_id: 'sdxl-base' } });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.parameters.width.default).toBe(1024); // SDXL default
      expect(data.parameters.height.default).toBe(1024);
      expect(data.parameters.width.max).toBe(1536); // SDXL max
      expect(data.limitations.memory_requirement_mb).toBe(6000); // Higher memory for SDXL
    });

    it('should return error for missing model_id', async () => {
      const request = new NextRequest('http://localhost:3000/api/models/image/parameters/');
      const response = await GET(request, { params: { model_id: '' } });
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe('Missing model_id parameter');
    });

    it('should return error for non-existent model', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([]);

      const request = new NextRequest('http://localhost:3000/api/models/image/parameters/non-existent');
      const response = await GET(request, { params: { model_id: 'non-existent' } });
      const data = await response.json();

      expect(response.status).toBe(404);
      expect(data.error).toBe('Model not found');
    });

    it('should return error for non-image model', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        {
          id: 'text-model',
          name: 'Text Model',
          provider: 'llama-cpp',
          type: 'text_generation',
          capabilities: ['chat']
        }
      ]);

      const request = new NextRequest('http://localhost:3000/api/models/image/parameters/text-model');
      const response = await GET(request, { params: { model_id: 'text-model' } });
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe('Model does not support image generation');
    });

    it('should set appropriate cache headers', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        {
          id: 'cached-model',
          name: 'Cached Model',
          provider: 'stable-diffusion',
          type: 'image_generation',
          capabilities: ['text2img']
        }
      ]);

      const request = new NextRequest('http://localhost:3000/api/models/image/parameters/cached-model');
      const response = await GET(request, { params: { model_id: 'cached-model' } });

      expect(response.headers.get('Cache-Control')).toBe('public, max-age=3600');
      expect(response.headers.get('X-Model-Provider')).toBe('stable-diffusion');
      expect(response.headers.get('X-Model-Type')).toBe('image_generation');
    });

    it('should handle service errors gracefully', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockRejectedValue(
        new Error('Service unavailable')
      );

      const request = new NextRequest('http://localhost:3000/api/models/image/parameters/error-model');
      const response = await GET(request, { params: { model_id: 'error-model' } });
      const data = await response.json();

      expect(response.status).toBe(500);
      expect(data.error).toBe('Failed to fetch model parameters');
      expect(data.message).toBe('Service unavailable');
    });
  });
});