import { NextRequest } from 'next/server';
import { POST } from '@/app/api/generate/image/route';

// Mock the model selection service
jest.mock('@/lib/model-selection-service', () => ({
  modelSelectionService: {
    getAvailableModels: jest.fn(),
  }
}));

describe('/api/generate/image', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('POST - Generate Image', () => {
    it('should generate image successfully', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        {
          id: 'sd-v1-5',
          name: 'Stable Diffusion v1.5',
          provider: 'stable-diffusion',
          type: 'image_generation',
          capabilities: ['text2img', 'img2img']
        }
      ]);

      const request = new NextRequest('http://localhost:3000/api/generate/image', {
        method: 'POST',
        body: JSON.stringify({
          prompt: 'A beautiful sunset over mountains',
          width: 512,
          height: 512,
          steps: 20,
          guidance_scale: 7.5,
          batch_size: 1
        })
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.success).toBe(true);
      expect(data.images).toHaveLength(1);
      expect(data.images[0].width).toBe(512);
      expect(data.images[0].height).toBe(512);
      expect(data.images[0].seed).toBeGreaterThan(0);
      expect(data.generation_info.model_id).toBe('sd-v1-5');
      expect(data.generation_info.provider).toBe('stable-diffusion');
      expect(data.generation_info.prompt).toBe('A beautiful sunset over mountains');
      expect(data.generation_info.generation_time).toBeGreaterThan(0);
      expect(response.headers.get('X-Model-Provider')).toBe('stable-diffusion');
    });

    it('should return error for missing prompt', async () => {
      const request = new NextRequest('http://localhost:3000/api/generate/image', {
        method: 'POST',
        body: JSON.stringify({})
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe('Missing required field: prompt');
    });

    it('should return error for excessive batch size', async () => {
      const request = new NextRequest('http://localhost:3000/api/generate/image', {
        method: 'POST',
        body: JSON.stringify({
          prompt: 'Test prompt',
          batch_size: 10
        })
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe('Batch size cannot exceed 4 images');
    });

    it('should return error when no image models available', async () => {
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

      const request = new NextRequest('http://localhost:3000/api/generate/image', {
        method: 'POST',
        body: JSON.stringify({
          prompt: 'Test prompt'
        })
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(503);
      expect(data.error).toBe('No image generation models available');
    });

    it('should use specified model when model_id provided', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        {
          id: 'sd-v1-5',
          name: 'Stable Diffusion v1.5',
          provider: 'stable-diffusion',
          type: 'image_generation',
          capabilities: ['text2img']
        },
        {
          id: 'flux-dev',
          name: 'Flux Dev',
          provider: 'flux',
          type: 'image_generation',
          capabilities: ['text2img']
        }
      ]);

      const request = new NextRequest('http://localhost:3000/api/generate/image', {
        method: 'POST',
        body: JSON.stringify({
          prompt: 'Test prompt',
          model_id: 'flux-dev'
        })
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.generation_info.model_id).toBe('flux-dev');
      expect(data.generation_info.provider).toBe('flux');
    });

    it('should return error for img2img without model support', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        {
          id: 'text2img-only',
          name: 'Text2Img Only Model',
          provider: 'stable-diffusion',
          type: 'image_generation',
          capabilities: ['text2img'] // No img2img support
        }
      ]);

      const request = new NextRequest('http://localhost:3000/api/generate/image', {
        method: 'POST',
        body: JSON.stringify({
          prompt: 'Test prompt',
          init_image: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
          strength: 0.8
        })
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe('Model does not support image-to-image generation');
    });

    it('should generate multiple images in batch', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        {
          id: 'sd-v1-5',
          name: 'Stable Diffusion v1.5',
          provider: 'stable-diffusion',
          type: 'image_generation',
          capabilities: ['text2img']
        }
      ]);

      const request = new NextRequest('http://localhost:3000/api/generate/image', {
        method: 'POST',
        body: JSON.stringify({
          prompt: 'Test prompt',
          batch_size: 3
        })
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.images).toHaveLength(3);
      expect(response.headers.get('X-Images-Generated')).toBe('3');
    });

    it('should handle generation service errors', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockRejectedValue(
        new Error('Service unavailable')
      );

      const request = new NextRequest('http://localhost:3000/api/generate/image', {
        method: 'POST',
        body: JSON.stringify({
          prompt: 'Test prompt'
        })
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(500);
      expect(data.error).toBe('Image generation failed');
      expect(data.message).toBe('Service unavailable');
    });
  });
});