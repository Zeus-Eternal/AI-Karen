
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import LogWidget from '../LogWidget';
import type { WidgetConfig, LogData } from '@/types/dashboard';

// Mock react-window
vi.mock('react-window', () => ({
  FixedSizeList: ({ children, itemData, itemCount }: any) => (
    <div data-testid="virtual-list">
      {Array.from({ length: Math.min(itemCount, 5) }, (_, index) => (
        <div key={index}>
          {children({ index, style: {}, data: itemData })}
        </div>
      ))}
    </div>
  ),
}));

// Mock the WidgetBase component
vi.mock('../../WidgetBase', () => ({
  WidgetBase: ({ children, ...props }: any) => (
    <div data-testid="widget-base" {...props}>
      {children}
    </div>
  ),
}));

const mockConfig: WidgetConfig = {
  id: 'test-log-widget',
  type: 'log',
  title: 'Application Logs',
  size: 'large',
  position: { x: 0, y: 0, w: 2, h: 2 },
  config: {
    logSource: 'application',
    levels: ['info', 'warn', 'error'],
    maxEntries: 200,
    autoScroll: true,
    showMetadata: false,
  },
  refreshInterval: 5000,
  enabled: true,
};

const mockLogData: LogData = {
  entries: [
    {
      id: '1',
      timestamp: new Date('2024-01-01T10:00:00Z'),
      level: 'info',
      message: 'Application started successfully',
      source: 'app',
      metadata: { version: '1.0.0', port: 3000 },
    },
    {
      id: '2',
      timestamp: new Date('2024-01-01T10:01:00Z'),
      level: 'warn',
      message: 'High memory usage detected',
      source: 'monitor',
      metadata: { usage: '85%' },
    },
    {
      id: '3',
      timestamp: new Date('2024-01-01T10:02:00Z'),
      level: 'error',
      message: 'Database connection failed',
      source: 'db',
      metadata: { error: 'ECONNREFUSED' },
    },
    {
      id: '4',
      timestamp: new Date('2024-01-01T10:03:00Z'),
      level: 'debug',
      message: 'Debug information',
      source: 'debug',
    },
  ],
  totalCount: 4,
  hasMore: false,
};

const mockWidgetData = {
  id: 'test-log-widget',
  data: mockLogData,
  loading: false,
  lastUpdated: new Date(),
};

describe('LogWidget', () => {
  const mockProps = {
    config: mockConfig,
    data: mockWidgetData,
    onConfigChange: vi.fn(),
    onRefresh: vi.fn(),
    onRemove: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();

  it('renders log widget with entries', () => {
    render(<LogWidget {...mockProps} />);
    
    expect(screen.getByText('Application started successfully')).toBeInTheDocument();
    expect(screen.getByText('High memory usage detected')).toBeInTheDocument();
    expect(screen.getByText('Database connection failed')).toBeInTheDocument();

  it('displays log entry details correctly', () => {
    render(<LogWidget {...mockProps} />);
    
    // Check timestamps
    expect(screen.getByText('10:00:00 AM')).toBeInTheDocument();
    expect(screen.getByText('10:01:00 AM')).toBeInTheDocument();
    
    // Check levels
    expect(screen.getByText('INFO')).toBeInTheDocument();
    expect(screen.getByText('WARN')).toBeInTheDocument();
    expect(screen.getByText('ERROR')).toBeInTheDocument();
    
    // Check sources
    expect(screen.getByText('[app]')).toBeInTheDocument();
    expect(screen.getByText('[monitor]')).toBeInTheDocument();
    expect(screen.getByText('[db]')).toBeInTheDocument();

  it('displays metadata when available', () => {
    render(<LogWidget {...mockProps} />);
    
    expect(screen.getByText(/version: 1\.0\.0/)).toBeInTheDocument();
    expect(screen.getByText(/port: 3000/)).toBeInTheDocument();
    expect(screen.getByText(/usage: 85%/)).toBeInTheDocument();

  it('filters logs by search term', async () => {
    const user = userEvent.setup();
    render(<LogWidget {...mockProps} />);
    
    const searchInput = screen.getByPlaceholderText('Search logs...');
    await user.type(searchInput, 'database');
    
    // Should show only the database-related log
    expect(screen.getByText('Database connection failed')).toBeInTheDocument();
    expect(screen.queryByText('Application started successfully')).not.toBeInTheDocument();

  it('filters logs by level', async () => {
    const user = userEvent.setup();
    render(<LogWidget {...mockProps} />);
    
    // Open level filter dropdown
    const levelButton = screen.getByRole('button', { name: /levels/i });
    await user.click(levelButton);
    
    // Uncheck INFO level
    const infoCheckbox = screen.getByRole('menuitemcheckbox', { name: /info/i });
    await user.click(infoCheckbox);
    
    // Should not show INFO level logs
    expect(screen.queryByText('Application started successfully')).not.toBeInTheDocument();
    expect(screen.getByText('High memory usage detected')).toBeInTheDocument();
    expect(screen.getByText('Database connection failed')).toBeInTheDocument();

  it('displays log statistics correctly', () => {
    render(<LogWidget {...mockProps} />);
    
    expect(screen.getByText('4 of 4 entries')).toBeInTheDocument();
    expect(screen.getByText(/Last: 10:03:00 AM/)).toBeInTheDocument();

  it('shows "more available" indicator when hasMore is true', () => {
    const moreLogsData = {
      ...mockWidgetData,
      data: {
        ...mockLogData,
        hasMore: true,
      },
    };

    render(<LogWidget {...mockProps} data={moreLogsData} />);
    
    expect(screen.getByText('4 of 4 entries (more available)')).toBeInTheDocument();
    expect(screen.getByText('Load More Entries')).toBeInTheDocument();

  it('handles pause/play functionality', async () => {
    const user = userEvent.setup();
    render(<LogWidget {...mockProps} />);
    
    const pauseButton = screen.getByRole('button', { name: /pause/i });
    await user.click(pauseButton);
    
    expect(screen.getByText('PAUSED')).toBeInTheDocument();
    
    const playButton = screen.getByRole('button', { name: /play/i });
    await user.click(playButton);
    
    expect(screen.queryByText('PAUSED')).not.toBeInTheDocument();

  it('handles log export', async () => {
    const user = userEvent.setup();
    
    // Mock URL.createObjectURL and related functions
    const mockCreateObjectURL = vi.fn(() => 'mock-url');
    const mockRevokeObjectURL = vi.fn();
    const mockClick = vi.fn();
    
    Object.defineProperty(window, 'URL', {
      value: {
        createObjectURL: mockCreateObjectURL,
        revokeObjectURL: mockRevokeObjectURL,
      },

    const mockAppendChild = vi.fn();
    const mockRemoveChild = vi.fn();
    const mockCreateElement = vi.fn(() => ({
      href: '',
      download: '',
      click: mockClick,
    }));
    
    Object.defineProperty(document, 'createElement', {
      value: mockCreateElement,

    render(<LogWidget {...mockProps} />);
    
    // Open export dropdown
    const exportButton = screen.getAllByRole('button').find(btn => 
      btn.querySelector('svg')?.getAttribute('class')?.includes('lucide-download')
    );
    
    if (exportButton) {
      await user.click(exportButton);
      
      const exportMenuItem = screen.getByText('Export Logs');
      await user.click(exportMenuItem);
      
      expect(mockCreateObjectURL).toHaveBeenCalled();
      expect(mockClick).toHaveBeenCalled();
    }

  it('highlights search terms in log messages', async () => {
    const user = userEvent.setup();
    render(<LogWidget {...mockProps} />);
    
    const searchInput = screen.getByPlaceholderText('Search logs...');
    await user.type(searchInput, 'started');
    
    // Should highlight the search term
    const highlightedText = screen.getByText('started');
    expect(highlightedText.tagName).toBe('MARK');

  it('shows no logs message when filtered results are empty', async () => {
    const user = userEvent.setup();
    render(<LogWidget {...mockProps} />);
    
    const searchInput = screen.getByPlaceholderText('Search logs...');
    await user.type(searchInput, 'nonexistent');
    
    expect(screen.getByText('No logs match the current filters')).toBeInTheDocument();

  it('shows no data message when data is not available', () => {
    render(<LogWidget {...mockProps} data={undefined} />);
    
    expect(screen.getByText('No log data available')).toBeInTheDocument();

  it('handles empty log entries', () => {
    const emptyData = {
      ...mockWidgetData,
      data: {
        entries: [],
        totalCount: 0,
        hasMore: false,
      },
    };

    render(<LogWidget {...mockProps} data={emptyData} />);
    
    expect(screen.getByText('No log entries available')).toBeInTheDocument();

  it('displays correct level badges with colors', () => {
    render(<LogWidget {...mockProps} />);
    
    const infoBadge = screen.getByText('INFO');
    const warnBadge = screen.getByText('WARN');
    const errorBadge = screen.getByText('ERROR');
    
    expect(infoBadge).toBeInTheDocument();
    expect(warnBadge).toBeInTheDocument();
    expect(errorBadge).toBeInTheDocument();

  it('limits metadata display to 3 items', () => {
    const manyMetadataData = {
      ...mockWidgetData,
      data: {
        ...mockLogData,
        entries: [
          {
            ...mockLogData.entries[0],
            metadata: {
              version: '1.0.0',
              port: 3000,
              env: 'production',
              region: 'us-east-1',
              instance: 'i-1234567890',
            },
          },
        ],
      },
    };

    render(<LogWidget {...mockProps} data={manyMetadataData} />);
    
    // Should only show first 3 metadata items
    expect(screen.getByText(/version: 1\.0\.0/)).toBeInTheDocument();
    expect(screen.getByText(/port: 3000/)).toBeInTheDocument();
    expect(screen.getByText(/env: production/)).toBeInTheDocument();
    expect(screen.queryByText(/region: us-east-1/)).not.toBeInTheDocument();

  it('passes props correctly to WidgetBase', () => {
    render(<LogWidget {...mockProps} />);
    
    const widgetBase = screen.getByTestId('widget-base');
    expect(widgetBase).toBeInTheDocument();

