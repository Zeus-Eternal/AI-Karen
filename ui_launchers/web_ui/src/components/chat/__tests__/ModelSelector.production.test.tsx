
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { ModelSelector } from '../ModelSelector';
import { getKarenBackend } from '@/lib/karen-backend';

// Mock the karen-backend
vi.mock('@/lib/karen-backend', () => ({
  getKarenBackend: vi.fn(),
}));

// Mock the model-selection-service
vi.mock('@/lib/model-selection-service', () => ({
  modelSelectionService: {
    updateLastSelectedModel: vi.fn().mockImplementation(() => Promise.resolve()),
  },
}));

// Mock the safe-console
vi.mock('@/lib/safe-console', () => ({
  safeError: vi.fn(),
  safeWarn: vi.fn(),
  safeDebug: vi.fn(),
}));

// Mock the model-utils
vi.mock('@/lib/model-utils', () => ({
  formatFileSize: vi.fn((bytes: number) => `${bytes} B`),
  getStatusBadgeVariant: vi.fn((status: string) => {
    switch (status) {
      case 'local': return 'default';
      case 'downloading': return 'outline';
      case 'available': return 'secondary';
      default: return 'outline';
    }
  }),
  getRecommendedModels: vi.fn((models: any[]) => models),
  getModelSelectorValue: vi.fn((model: any) => `${model.provider}:${model.name}`),
  doesModelMatchValue: vi.fn((model: any, value: string) => `${model.provider}:${model.name}` === value),
}));

// Production test data - only production-ready models
const mockProductionModels = [
  {
    id: '1',
    name: 'llama-7b-chat',
    provider: 'local',
    status: 'local',
    size: 7000000000,
    capabilities: ['chat', 'text-generation'],
    metadata: { parameters: '7B' },
    type: 'text',
  },
  {
    id: '2',
    name: 'gpt-3.5-turbo',
    provider: 'openai',
    status: 'downloading',
    size: 0,
    download_progress: 45,
    capabilities: ['chat'],
    metadata: {},
    type: 'text',
  },
  {
    id: '3',
    name: 'stable-diffusion-xl',
    provider: 'huggingface',
    status: 'available',
    size: 6000000000,
    capabilities: ['image-generation'],
    metadata: {},
    type: 'image',
  },
];

const mockBackend = {
  makeRequestPublic: vi.fn(),
};

describe('ModelSelector - Production', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (getKarenBackend as any).mockReturnValue(mockBackend);
    mockBackend.makeRequestPublic.mockResolvedValue({
      models: mockProductionModels,
      total_count: 3,
      local_count: 1,
      available_count: 1,


  afterEach(() => {
    vi.clearAllMocks();

  it('should render loading state initially', () => {
    render(<ModelSelector />);
    expect(screen.getByText('Loading models...')).toBeInTheDocument();

  it('should load production models successfully', async () => {
    render(<ModelSelector />);
    
    await waitFor(() => {
      expect(mockBackend.makeRequestPublic).toHaveBeenCalledWith('/api/models/library?production=true');


  it('should filter models by task compatibility', async () => {
    render(<ModelSelector task="chat" />);
    
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();

    // Should only show chat-compatible models
    fireEvent.click(screen.getByRole('combobox'));
    
    await waitFor(() => {
      expect(screen.getByText('llama-7b-chat')).toBeInTheDocument();
      expect(screen.getByText('gpt-3.5-turbo')).toBeInTheDocument();
      // Should not show image model for chat task
      expect(screen.queryByText('stable-diffusion-xl')).not.toBeInTheDocument();


  it('should auto-select first available local model', async () => {
    const onValueChange = vi.fn();
    render(<ModelSelector onValueChange={onValueChange} autoSelect={true} />);
    
    await waitFor(() => {
      expect(onValueChange).toHaveBeenCalledWith('local:llama-7b-chat');


  it('should handle model selection', async () => {
    const onValueChange = vi.fn();
    render(<ModelSelector onValueChange={onValueChange} autoSelect={false} />);
    
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('combobox'));
    
    await waitFor(() => {
      expect(screen.getByText('llama-7b-chat')).toBeInTheDocument();

    fireEvent.click(screen.getByText('llama-7b-chat'));
    
    expect(onValueChange).toHaveBeenCalledWith('local:llama-7b-chat');

  it('should show download progress for downloading models', async () => {
    render(<ModelSelector includeDownloading={true} />);
    
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('combobox'));
    
    await waitFor(() => {
      expect(screen.getByText('45%')).toBeInTheDocument();


  it('should group models by capability', async () => {
    render(<ModelSelector />);
    
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('combobox'));
    
    await waitFor(() => {
      expect(screen.getByText('Chat & Text (2)')).toBeInTheDocument();


  it('should handle error state gracefully', async () => {
    mockBackend.makeRequestPublic.mockRejectedValue(new Error('API Error'));
    
    render(<ModelSelector />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load models')).toBeInTheDocument();


  it('should show empty state when no models available', async () => {
    mockBackend.makeRequestPublic.mockResolvedValue({
      models: [],
      total_count: 0,
      local_count: 0,
      available_count: 0,

    render(<ModelSelector task="chat" />);
    
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('combobox'));
    
    await waitFor(() => {
      expect(screen.getByText(/No chat models are ready to use/)).toBeInTheDocument();


  it('should not include blocked model names', async () => {
    const modelsWithBlocked = [
      ...mockProductionModels,
      {
        id: '4',
        name: 'cache',
        provider: 'local',
        status: 'local',
        size: 1000000,
        capabilities: ['chat'],
        metadata: {},
        type: 'text',
      },
      {
        id: '5',
        name: 'tmp',
        provider: 'local',
        status: 'local',
        size: 1000000,
        capabilities: ['chat'],
        metadata: {},
        type: 'text',
      },
    ];

    mockBackend.makeRequestPublic.mockResolvedValue({
      models: modelsWithBlocked,
      total_count: 5,
      local_count: 3,
      available_count: 1,

    render(<ModelSelector />);
    
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('combobox'));
    
    await waitFor(() => {
      expect(screen.getByText('llama-7b-chat')).toBeInTheDocument();
      // Blocked names should not appear
      expect(screen.queryByText('cache')).not.toBeInTheDocument();
      expect(screen.queryByText('tmp')).not.toBeInTheDocument();


  it('should show model details in tooltip', async () => {
    render(<ModelSelector value="local:llama-7b-chat" />);
    
    await waitFor(() => {
      expect(screen.getByText('llama-7b-chat')).toBeInTheDocument();

    // Hover over the selected model to show tooltip
    fireEvent.mouseEnter(screen.getByRole('combobox'));
    
    await waitFor(() => {
      expect(screen.getByText('llama-7b-chat')).toBeInTheDocument();


  it('should handle disabled state', () => {
    render(<ModelSelector disabled={true} />);
    
    expect(screen.getByRole('combobox')).toBeDisabled();

  it('should refresh models when refresh button is clicked', async () => {
    mockBackend.makeRequestPublic.mockRejectedValueOnce(new Error('API Error'));
    
    render(<ModelSelector />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load models')).toBeInTheDocument();

    // Reset mock to return success
    mockBackend.makeRequestPublic.mockResolvedValue({
      models: mockProductionModels,
      total_count: 3,
      local_count: 1,
      available_count: 1,

    // Click refresh button
    fireEvent.click(screen.getByRole('button'));
    
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();


