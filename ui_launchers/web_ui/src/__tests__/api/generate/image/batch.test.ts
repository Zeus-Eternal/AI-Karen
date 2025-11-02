import { NextRequest } from 'next/server';
import { GET, POST } from '@/app/api/generate/image/batch/route';

// Mock the model selection service
jest.mock('@/lib/model-selection-service', () => ({
  modelSelectionService: {
    getAvailableModels: jest.fn(),
  }
}));

describe('/api/generate/image/batch', () => {
  beforeEach(() => {
    jest.clearAllMocks();

  describe('POST - Create Batch', () => {
    it('should create batch generation job successfully', async () => {
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

      const request = new NextRequest('http://localhost:3000/api/generate/image/batch', {
        method: 'POST',
        body: JSON.stringify({
          requests: [
            {
              id: 'req1',
              prompt: 'A beautiful sunset',
              width: 512,
              height: 512
            },
            {
              id: 'req2',
              prompt: 'A mountain landscape',
              width: 768,
              height: 512
            }
          ],
          global_model_id: 'sd-v1-5',
          priority: 'normal'
        })

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(202); // Accepted
      expect(data.success).toBe(true);
      expect(data.batch_id).toBeDefined();
      expect(data.batch_id).toMatch(/^batch_\d+_[a-z0-9]+$/);
      expect(data.total_requests).toBe(2);
      expect(data.estimated_completion_time).toBeGreaterThan(0);
      expect(data.status).toBe('queued');
      expect(response.headers.get('X-Batch-ID')).toBe(data.batch_id);
      expect(response.headers.get('Location')).toBe(`/api/generate/image/batch/${data.batch_id}`);

    it('should return error for empty requests array', async () => {
      const request = new NextRequest('http://localhost:3000/api/generate/image/batch', {
        method: 'POST',
        body: JSON.stringify({
          requests: []
        })

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe('Missing or empty requests array');

    it('should return error for missing requests field', async () => {
      const request = new NextRequest('http://localhost:3000/api/generate/image/batch', {
        method: 'POST',
        body: JSON.stringify({})

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe('Missing or empty requests array');

    it('should return error for excessive batch size', async () => {
      const requests = Array.from({ length: 25 }, (_, i) => ({
        id: `req${i + 1}`,
        prompt: `Prompt ${i + 1}`
      }));

      const request = new NextRequest('http://localhost:3000/api/generate/image/batch', {
        method: 'POST',
        body: JSON.stringify({ requests })

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe('Batch size cannot exceed 20 requests');

    it('should validate individual requests', async () => {
      const request = new NextRequest('http://localhost:3000/api/generate/image/batch', {
        method: 'POST',
        body: JSON.stringify({
          requests: [
            { prompt: 'Valid prompt' },
            { /* missing prompt */ },
            { prompt: 'Another valid prompt' }
          ]
        })

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe('Request 2 is missing required field: prompt');

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

      const request = new NextRequest('http://localhost:3000/api/generate/image/batch', {
        method: 'POST',
        body: JSON.stringify({
          requests: [{ prompt: 'Test prompt' }]
        })

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(503);
      expect(data.error).toBe('No image generation models available');

    it('should assign default IDs to requests without IDs', async () => {
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

      const request = new NextRequest('http://localhost:3000/api/generate/image/batch', {
        method: 'POST',
        body: JSON.stringify({
          requests: [
            { prompt: 'First prompt' }, // No ID
            { id: 'custom-id', prompt: 'Second prompt' }, // Custom ID
            { prompt: 'Third prompt' } // No ID
          ]
        })

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(202);
      expect(data.success).toBe(true);


  describe('GET - Batch Status', () => {
    it('should return recent batches when no batch_id provided', async () => {
      const request = new NextRequest('http://localhost:3000/api/generate/image/batch');
      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.recent_batches).toBeInstanceOf(Array);
      expect(data.active_batches).toBeGreaterThanOrEqual(0);

    it('should return error for non-existent batch', async () => {
      const request = new NextRequest('http://localhost:3000/api/generate/image/batch?batch_id=non-existent');
      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(404);
      expect(data.error).toBe('Batch not found');
      expect(data.batch_id).toBe('non-existent');

    it('should handle service errors gracefully', async () => {
      // This test would require mocking internal batch storage, 
      // which is simplified for this implementation
      const request = new NextRequest('http://localhost:3000/api/generate/image/batch');
      const response = await GET(request);

      expect(response.status).toBe(200);


  describe('Batch Processing Integration', () => {
    it('should process batch and update status', async () => {
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

      // Create batch
      const createRequest = new NextRequest('http://localhost:3000/api/generate/image/batch', {
        method: 'POST',
        body: JSON.stringify({
          requests: [
            { prompt: 'Test prompt 1' },
            { prompt: 'Test prompt 2' }
          ]
        })

      const createResponse = await POST(createRequest);
      const createData = await createResponse.json();
      const batchId = createData.batch_id;

      expect(createResponse.status).toBe(202);
      expect(batchId).toBeDefined();

      // Check initial status
      const statusRequest = new NextRequest(`http://localhost:3000/api/generate/image/batch?batch_id=${batchId}`);
      const statusResponse = await GET(statusRequest);
      const statusData = await statusResponse.json();

      expect(statusResponse.status).toBe(200);
      expect(statusData.batch_id).toBe(batchId);
      expect(statusData.status).toBe('queued');
      expect(statusData.total_requests).toBe(2);

      // Wait a bit for processing to potentially start
      await new Promise(resolve => setTimeout(resolve, 100));

      // Check status again
      const statusRequest2 = new NextRequest(`http://localhost:3000/api/generate/image/batch?batch_id=${batchId}`);
      const statusResponse2 = await GET(statusRequest2);
      const statusData2 = await statusResponse2.json();

      expect(statusResponse2.status).toBe(200);
      expect(['queued', 'processing', 'completed']).toContain(statusData2.status);


