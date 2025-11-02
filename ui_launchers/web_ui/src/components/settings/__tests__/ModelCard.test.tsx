
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import ModelCard from '../ModelCard';

const mockModel = {
  id: 'tinyllama-1.1b-chat-q4',
  name: 'TinyLlama 1.1B Chat Q4_K_M',
  provider: 'llama-cpp',
  size: 669000000,
  description: 'A compact 1.1B parameter language model optimized for chat applications',
  capabilities: ['text-generation', 'chat', 'local-inference'],
  status: 'available' as const,
  metadata: {
    parameters: '1.1B',
    quantization: 'Q4_K_M',
    memory_requirement: '~1GB',
    context_length: 2048,
    license: 'Apache 2.0',
    tags: ['chat', 'small', 'efficient']
  }
};

const mockLocalModel = {
  ...mockModel,
  id: 'local-model',
  name: 'Local Model',
  status: 'local' as const,
  local_path: '/path/to/model.gguf',
  disk_usage: 1000000000,
  last_used: Date.now() / 1000 - 3600 // 1 hour ago
};

const mockDownloadingModel = {
  ...mockModel,
  id: 'downloading-model',
  name: 'Downloading Model',
  status: 'downloading' as const,
  download_progress: 65.5
};

const mockErrorModel = {
  ...mockModel,
  id: 'error-model',
  name: 'Error Model',
  status: 'error' as const
};

describe('ModelCard', () => {
  const mockOnDownload = vi.fn();
  const mockOnDelete = vi.fn();
  const mockOnCancel = vi.fn();
  const mockOnInfo = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

  describe('Available Model', () => {
    it('renders available model correctly', () => {
      render(
        <ModelCard
          model={mockModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      expect(screen.getByText('TinyLlama 1.1B Chat Q4_K_M')).toBeInTheDocument();
      expect(screen.getByText('A compact 1.1B parameter language model optimized for chat applications')).toBeInTheDocument();
      expect(screen.getByText('llama-cpp')).toBeInTheDocument();
      expect(screen.getByText('638.01 MB')).toBeInTheDocument(); // Formatted size
      expect(screen.getByText('Available')).toBeInTheDocument();

    it('displays model metadata', () => {
      render(
        <ModelCard
          model={mockModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      expect(screen.getByText('1.1B')).toBeInTheDocument();
      expect(screen.getByText('Q4_K_M')).toBeInTheDocument();
      expect(screen.getByText('~1GB')).toBeInTheDocument();
      expect(screen.getByText('Apache 2.0')).toBeInTheDocument();
      expect(screen.getByText('2048')).toBeInTheDocument();

    it('displays capabilities as badges', () => {
      render(
        <ModelCard
          model={mockModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      expect(screen.getByText('text-generation')).toBeInTheDocument();
      expect(screen.getByText('chat')).toBeInTheDocument();
      expect(screen.getByText('local-inference')).toBeInTheDocument();

    it('shows download button for available model', () => {
      render(
        <ModelCard
          model={mockModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const downloadButton = screen.getByRole('button', { name: /download/i });
      expect(downloadButton).toBeInTheDocument();
      expect(downloadButton).not.toBeDisabled();

    it('calls onDownload when download button is clicked', async () => {
      render(
        <ModelCard
          model={mockModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const downloadButton = screen.getByRole('button', { name: /download/i });
      fireEvent.click(downloadButton);

      await waitFor(() => {
        expect(mockOnDownload).toHaveBeenCalledWith('tinyllama-1.1b-chat-q4');


    it('shows info button', () => {
      render(
        <ModelCard
          model={mockModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const infoButton = screen.getByRole('button', { name: /info/i });
      expect(infoButton).toBeInTheDocument();

    it('calls onInfo when info button is clicked', async () => {
      render(
        <ModelCard
          model={mockModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const infoButton = screen.getByRole('button', { name: /info/i });
      fireEvent.click(infoButton);

      await waitFor(() => {
        expect(mockOnInfo).toHaveBeenCalledWith(mockModel);



  describe('Local Model', () => {
    it('renders local model correctly', () => {
      render(
        <ModelCard
          model={mockLocalModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      expect(screen.getByText('Local Model')).toBeInTheDocument();
      expect(screen.getByText('Local')).toBeInTheDocument();
      expect(screen.getByText('953.67 MB')).toBeInTheDocument(); // Disk usage

    it('shows delete button for local model', () => {
      render(
        <ModelCard
          model={mockLocalModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      expect(deleteButton).toBeInTheDocument();

    it('calls onDelete when delete button is clicked', async () => {
      render(
        <ModelCard
          model={mockLocalModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(mockOnDelete).toHaveBeenCalledWith('local-model');


    it('displays last used time', () => {
      render(
        <ModelCard
          model={mockLocalModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      expect(screen.getByText(/last used/i)).toBeInTheDocument();
      expect(screen.getByText(/1 hour ago/i)).toBeInTheDocument();

    it('displays local path', () => {
      render(
        <ModelCard
          model={mockLocalModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      expect(screen.getByText('/path/to/model.gguf')).toBeInTheDocument();


  describe('Downloading Model', () => {
    it('renders downloading model correctly', () => {
      render(
        <ModelCard
          model={mockDownloadingModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      expect(screen.getByText('Downloading Model')).toBeInTheDocument();
      expect(screen.getByText('Downloading')).toBeInTheDocument();
      expect(screen.getByText('65.5%')).toBeInTheDocument();

    it('shows progress bar for downloading model', () => {
      render(
        <ModelCard
          model={mockDownloadingModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toBeInTheDocument();
      expect(progressBar).toHaveAttribute('aria-valuenow', '65.5');

    it('shows cancel button for downloading model', () => {
      render(
        <ModelCard
          model={mockDownloadingModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      expect(cancelButton).toBeInTheDocument();

    it('calls onCancel when cancel button is clicked', async () => {
      render(
        <ModelCard
          model={mockDownloadingModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      await waitFor(() => {
        expect(mockOnCancel).toHaveBeenCalledWith('downloading-model');


    it('disables download button for downloading model', () => {
      render(
        <ModelCard
          model={mockDownloadingModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const downloadButton = screen.queryByRole('button', { name: /download/i });
      expect(downloadButton).not.toBeInTheDocument();


  describe('Error Model', () => {
    it('renders error model correctly', () => {
      render(
        <ModelCard
          model={mockErrorModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      expect(screen.getByText('Error Model')).toBeInTheDocument();
      expect(screen.getByText('Error')).toBeInTheDocument();

    it('shows error styling', () => {
      render(
        <ModelCard
          model={mockErrorModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const errorBadge = screen.getByText('Error');
      expect(errorBadge).toHaveClass('bg-destructive');

    it('shows retry button for error model', () => {
      render(
        <ModelCard
          model={mockErrorModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const retryButton = screen.getByRole('button', { name: /retry/i });
      expect(retryButton).toBeInTheDocument();


  describe('Compact Mode', () => {
    it('renders in compact mode', () => {
      render(
        <ModelCard
          model={mockModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
          compact={true}
        />
      );

      expect(screen.getByText('TinyLlama 1.1B Chat Q4_K_M')).toBeInTheDocument();
      
      // In compact mode, description should be truncated or hidden
      const description = screen.queryByText('A compact 1.1B parameter language model optimized for chat applications');
      expect(description).not.toBeInTheDocument();

    it('shows fewer details in compact mode', () => {
      render(
        <ModelCard
          model={mockModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
          compact={true}
        />
      );

      // Should show essential info but not all metadata
      expect(screen.getByText('TinyLlama 1.1B Chat Q4_K_M')).toBeInTheDocument();
      expect(screen.getByText('638.01 MB')).toBeInTheDocument();
      
      // Detailed metadata might be hidden in compact mode
      expect(screen.queryByText('Context Length')).not.toBeInTheDocument();


  describe('Model Status Badges', () => {
    it('shows correct badge color for available status', () => {
      render(
        <ModelCard
          model={mockModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const statusBadge = screen.getByText('Available');
      expect(statusBadge).toHaveClass('bg-blue-100');

    it('shows correct badge color for local status', () => {
      render(
        <ModelCard
          model={mockLocalModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const statusBadge = screen.getByText('Local');
      expect(statusBadge).toHaveClass('bg-green-100');

    it('shows correct badge color for downloading status', () => {
      render(
        <ModelCard
          model={mockDownloadingModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const statusBadge = screen.getByText('Downloading');
      expect(statusBadge).toHaveClass('bg-yellow-100');

    it('shows correct badge color for error status', () => {
      render(
        <ModelCard
          model={mockErrorModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const statusBadge = screen.getByText('Error');
      expect(statusBadge).toHaveClass('bg-destructive');


  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      render(
        <ModelCard
          model={mockModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const downloadButton = screen.getByRole('button', { name: /download/i });
      expect(downloadButton).toHaveAttribute('aria-label', expect.stringContaining('Download'));
      
      const infoButton = screen.getByRole('button', { name: /info/i });
      expect(infoButton).toHaveAttribute('aria-label', expect.stringContaining('Info'));

    it('has proper heading structure', () => {
      render(
        <ModelCard
          model={mockModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const heading = screen.getByRole('heading', { name: 'TinyLlama 1.1B Chat Q4_K_M' });
      expect(heading).toBeInTheDocument();

    it('has proper progress bar attributes for downloading model', () => {
      render(
        <ModelCard
          model={mockDownloadingModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '65.5');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');


  describe('Edge Cases', () => {
    it('handles model without metadata', () => {
      const modelWithoutMetadata = {
        ...mockModel,
        metadata: undefined
      };

      render(
        <ModelCard
          model={modelWithoutMetadata}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      expect(screen.getByText('TinyLlama 1.1B Chat Q4_K_M')).toBeInTheDocument();
      // Should not crash and should still render basic info

    it('handles model without capabilities', () => {
      const modelWithoutCapabilities = {
        ...mockModel,
        capabilities: []
      };

      render(
        <ModelCard
          model={modelWithoutCapabilities}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      expect(screen.getByText('TinyLlama 1.1B Chat Q4_K_M')).toBeInTheDocument();
      // Should not show capability badges but should not crash

    it('handles very long model names', () => {
      const modelWithLongName = {
        ...mockModel,
        name: 'This is a very long model name that should be handled gracefully without breaking the layout or causing issues'
      };

      render(
        <ModelCard
          model={modelWithLongName}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      expect(screen.getByText(modelWithLongName.name)).toBeInTheDocument();

    it('handles zero size models', () => {
      const zeroSizeModel = {
        ...mockModel,
        size: 0
      };

      render(
        <ModelCard
          model={zeroSizeModel}
          onDownload={mockOnDownload}
          onDelete={mockOnDelete}
          onCancel={mockOnCancel}
          onInfo={mockOnInfo}
        />
      );

      expect(screen.getByText('0 B')).toBeInTheDocument();


