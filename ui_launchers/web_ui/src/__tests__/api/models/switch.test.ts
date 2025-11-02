import { NextRequest } from 'next/server';
import { POST } from '@/app/api/models/switch/route';

// Mock the model selection service
jest.mock('@/lib/model-selection-service', () => ({
  modelSelectionService: {
    getAvailableModels: jest.fn(),
    getSelectionStats: jest.fn(),
    selectModel: jest.fn(),
  }
}));

describe('/api/models/switch', () => {
  beforeEach(() => {
    jest.clearAllMocks();

  describe('POST - Switch Model', () => {
    it('should switch models successfully', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        {
          id: 'source-model',
          name: 'Source Model',
          provider: 'llama-cpp',
          capabilities: ['chat']
        },
        {
          id: 'target-model',
          name: 'Target Model',
          provider: 'stable-diffusion',
          capabilities: ['text2img', 'img2img']
        }
      ]);

      (modelSelectionService.getSelectionStats as jest.Mock).mockResolvedValue({
        selectedModel: { id: 'source-model' }

      (modelSelectionService.selectModel as jest.Mock).mockResolvedValue({
        success: true

      const request = new NextRequest('http://localhost:3000/api/models/switch', {
        method: 'POST',
        body: JSON.stringify({
          from_model_id: 'source-model',
          to_model_id: 'target-model',
          preserve_context: true
        })

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.success).toBe(true);
      expect(data.from_model).toBe('source-model');
      expect(data.to_model).toBe('target-model');
      expect(data.context_preserved).toBe(true);
      expect(data.capabilities_changed.added).toEqual(['text2img', 'img2img']);
      expect(data.capabilities_changed.removed).toEqual(['chat']);
      expect(data.switch_time).toBeGreaterThan(0);
      expect(response.headers.get('X-From-Provider')).toBe('llama-cpp');
      expect(response.headers.get('X-To-Provider')).toBe('stable-diffusion');

    it('should return error for missing to_model_id', async () => {
      const request = new NextRequest('http://localhost:3000/api/models/switch', {
        method: 'POST',
        body: JSON.stringify({})

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe('Missing required field: to_model_id');

    it('should return error for non-existent target model', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([]);

      const request = new NextRequest('http://localhost:3000/api/models/switch', {
        method: 'POST',
        body: JSON.stringify({ to_model_id: 'non-existent' })

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(404);
      expect(data.error).toBe('Target model not found');

    it('should handle switching to same model', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        {
          id: 'same-model',
          name: 'Same Model',
          provider: 'llama-cpp',
          capabilities: ['chat']
        }
      ]);

      (modelSelectionService.getSelectionStats as jest.Mock).mockResolvedValue({
        selectedModel: { id: 'same-model' }

      const request = new NextRequest('http://localhost:3000/api/models/switch', {
        method: 'POST',
        body: JSON.stringify({ to_model_id: 'same-model' })

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.success).toBe(true);
      expect(data.message).toBe('Already using target model');
      expect(data.capabilities_changed.added).toEqual([]);
      expect(data.capabilities_changed.removed).toEqual([]);

    it('should handle switch failure', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        { id: 'target-model', name: 'Target Model', provider: 'llama-cpp' }
      ]);

      (modelSelectionService.getSelectionStats as jest.Mock).mockResolvedValue({
        selectedModel: { id: 'current-model' }

      (modelSelectionService.selectModel as jest.Mock).mockResolvedValue({
        success: false,
        error: 'Switch failed'

      const request = new NextRequest('http://localhost:3000/api/models/switch', {
        method: 'POST',
        body: JSON.stringify({ to_model_id: 'target-model' })

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(500);
      expect(data.error).toBe('Model switch failed');
      expect(data.message).toBe('Switch failed');

    it('should auto-detect from_model when not provided', async () => {
      const { modelSelectionService } = await import('@/lib/model-selection-service');
      
      (modelSelectionService.getAvailableModels as jest.Mock).mockResolvedValue([
        { id: 'current-model', name: 'Current Model', provider: 'llama-cpp', capabilities: ['chat'] },
        { id: 'target-model', name: 'Target Model', provider: 'transformers', capabilities: ['text-generation'] }
      ]);

      (modelSelectionService.getSelectionStats as jest.Mock).mockResolvedValue({
        selectedModel: { id: 'current-model' }

      (modelSelectionService.selectModel as jest.Mock).mockResolvedValue({
        success: true

      const request = new NextRequest('http://localhost:3000/api/models/switch', {
        method: 'POST',
        body: JSON.stringify({ to_model_id: 'target-model' })

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.from_model).toBe('current-model');
      expect(data.to_model).toBe('target-model');


