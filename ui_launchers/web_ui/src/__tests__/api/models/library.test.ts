import { NextRequest } from 'next/server';
import { GET } from '@/app/api/models/library/route';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock the model selection service
vi.mock('@/lib/model-selection-service', () => ({
  modelSelectionService: {
    getAvailableModels: vi.fn(),
    getSelectionStats: vi.fn(),
  }
}));

// Mock fetch
global.fetch = vi.fn();

describe('/api/models/library', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockClear();

  describe('Enhanced scanning functionality', () => {
    it('should perform dynamic scanning when scan=true', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      // Mock the service responses
      (modelSelectionService.getAvailableModels as any).mockResolvedValue([
        {
          id: 'test-model-1',
          name: 'Test Model 1',
          provider: 'llama-cpp',
          type: 'text_generation',
          status: 'local',
          capabilities: ['chat', 'text-generation'],
          size: 1000000,
          metadata: { parameter_count: '1B' }
        },
        {
          id: 'test-model-2',
          name: 'Test Model 2',
          provider: 'stable-diffusion',
          type: 'image_generation',
          status: 'available',
          capabilities: ['text2img'],
          size: 2000000,
          metadata: { resolution: [512, 512] }
        }
      ]);

      (modelSelectionService.getSelectionStats as any).mockResolvedValue({
        scanStats: {
          scanDuration: 1500,
          modelsFound: 2,
          lastScan: new Date().toISOString()
        },
        selectedModel: { id: 'test-model-1' },
        lastLoadTime: 2000,
        averageResponseTime: 500

      const request = new NextRequest('http://localhost:3000/api/models/library?scan=true&includeHealth=true');
      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.source).toBe('enhanced_dynamic_scan');
      expect(data.models).toHaveLength(2);
      expect(data.total_count).toBe(2);
      expect(data.local_count).toBe(1);
      expect(data.available_count).toBe(1);
      expect(data.categorized_models).toBeDefined();
      expect(data.categorized_models.text_generation).toHaveLength(1);
      expect(data.categorized_models.image_generation).toHaveLength(1);
      expect(data.scan_metadata.include_health).toBe(true);
      expect(data.models[0].health).toBeDefined();
      expect(data.models[0].last_scanned).toBeDefined();

    it('should handle scan errors gracefully', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as any).mockRejectedValue(
        new Error('Scan failed')
      );

      const request = new NextRequest('http://localhost:3000/api/models/library?scan=true');
      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(500);
      expect(data.error).toBe('Scan failed');
      expect(data.message).toBe('Dynamic model scanning encountered an error');
      expect(data.details).toBe('Scan failed');
      expect(data.fallback_available).toBe(true);


  describe('Backend fallback functionality', () => {
    it('should fall back to backend when scan is not requested', async () => {
      (global.fetch as any).mockResolvedValue({
        status: 200,
        ok: true,
        headers: new Map([['content-type', 'application/json']]),
        json: async () => ({
          models: [{ id: 'backend-model', name: 'Backend Model' }],
          total_count: 1
        })

      const request = new NextRequest('http://localhost:3000/api/models/library');
      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(global.fetch).toHaveBeenCalled();
      expect(data.models).toHaveLength(1);
      expect(data.models[0].id).toBe('backend-model');


