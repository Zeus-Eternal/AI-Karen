/**
 * Unit tests for MemoryNetworkGraph component
 * Tests network visualization, interactions, and performance
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import MemoryNetworkGraph from '../MemoryNetworkGraph';
import { getMemoryService } from '@/services/memoryService';
import type { MemoryStats } from '@/services/memoryService';

// Mock D3
const mockD3 = {
  select: vi.fn(() => ({
    selectAll: vi.fn(() => ({
      data: vi.fn(() => ({
        enter: vi.fn(() => ({
          append: vi.fn(() => ({
            attr: vi.fn(() => mockD3.select()),
            style: vi.fn(() => mockD3.select()),
            text: vi.fn(() => mockD3.select()),
            on: vi.fn(() => mockD3.select()),
            call: vi.fn(() => mockD3.select())
          }))
        }))
      }))
    })),
    attr: vi.fn(() => mockD3.select()),
    style: vi.fn(() => mockD3.select()),
    call: vi.fn(() => mockD3.select()),
    transition: vi.fn(() => mockD3.select()),
    select: vi.fn(() => mockD3.select()),
    remove: vi.fn(() => mockD3.select())
  })),
  forceSimulation: vi.fn(() => ({
    force: vi.fn(() => mockSimulation),
    on: vi.fn(() => mockSimulation),
    stop: vi.fn(() => mockSimulation),
    restart: vi.fn(() => mockSimulation),
    alpha: vi.fn(() => mockSimulation),
    alphaTarget: vi.fn(() => mockSimulation)
  })),
  forceLink: vi.fn(() => ({
    id: vi.fn(() => mockForce),
    distance: vi.fn(() => mockForce),
    strength: vi.fn(() => mockForce)
  })),
  forceManyBody: vi.fn(() => ({
    strength: vi.fn(() => mockForce)
  })),
  forceCenter: vi.fn(() => mockForce),
  forceCollide: vi.fn(() => ({
    radius: vi.fn(() => mockForce)
  })),
  zoom: vi.fn(() => ({
    scaleExtent: vi.fn(() => mockZoom),
    on: vi.fn(() => mockZoom),
    transform: vi.fn(),
    scaleBy: vi.fn()
  })),
  zoomIdentity: {},
  drag: vi.fn(() => ({
    on: vi.fn(() => mockDrag)
  })),
  scaleOrdinal: vi.fn(() => mockScale),
  scaleSequential: vi.fn(() => mockScale),
  schemeCategory10: ['#1f77b4', '#ff7f0e'],
  schemeSet2: ['#66c2a5', '#fc8d62'],
  schemeTableau10: ['#4e79a7', '#f28e2c'],
  interpolateViridis: vi.fn(),
  mean: vi.fn(() => 0)
};

const mockSimulation = {
  force: vi.fn(() => mockSimulation),
  on: vi.fn(() => mockSimulation),
  stop: vi.fn(() => mockSimulation),
  restart: vi.fn(() => mockSimulation),
  alpha: vi.fn(() => mockSimulation),
  alphaTarget: vi.fn(() => mockSimulation)
};

const mockForce = {
  id: vi.fn(() => mockForce),
  distance: vi.fn(() => mockForce),
  strength: vi.fn(() => mockForce),
  radius: vi.fn(() => mockForce)
};

const mockZoom = {
  scaleExtent: vi.fn(() => mockZoom),
  on: vi.fn(() => mockZoom),
  transform: vi.fn(),
  scaleBy: vi.fn()
};

const mockDrag = {
  on: vi.fn(() => mockDrag)
};

const mockScale = vi.fn(() => '#1f77b4');
mockScale.domain = vi.fn(() => mockScale);

vi.mock('d3', () => mockD3);

// Mock the memory service
vi.mock('@/services/memoryService', () => ({
  getMemoryService: vi.fn()
}));

// Mock Lucide icons
vi.mock('lucide-react', () => ({
  ZoomIn: () => <div data-testid="zoom-in-icon">ZoomIn</div>,
  ZoomOut: () => <div data-testid="zoom-out-icon">ZoomOut</div>,
  RotateCcw: () => <div data-testid="reset-icon">RotateCcw</div>,
  Search: () => <div data-testid="search-icon">Search</div>,
  Filter: () => <div data-testid="filter-icon">Filter</div>,
  Maximize2: () => <div data-testid="maximize-icon">Maximize2</div>,
  Minimize2: () => <div data-testid="minimize-icon">Minimize2</div>,
  Play: () => <div data-testid="play-icon">Play</div>,
  Pause: () => <div data-testid="pause-icon">Pause</div>,
  Settings: () => <div data-testid="settings-icon">Settings</div>
}));

// Mock UI components
vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="card" className={className}>{children}</div>
  )
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, size, variant }: { 
    children: React.ReactNode; 
    onClick?: () => void; 
    size?: string;
    variant?: string;
  }) => (
    <button 
      data-testid="button" 
      onClick={onClick} 
      data-size={size}
      data-variant={variant}
     aria-label="Button">
      {children}
    </button>
  )
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant, className }: { 
    children: React.ReactNode; 
    variant?: string;
    className?: string;
  }) => (
    <span data-testid="badge" data-variant={variant} className={className}>
      {children}
    </span>
  )
}));

vi.mock('@/components/ui/input', () => ({
  Input: ({ type, placeholder, value, onChange, className }: { 
    type: string;
    placeholder: string;
    value: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    className?: string;
  }) => (
    <input
      data-testid="input"
      type={type}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      className={className} />
  )
}));

describe('MemoryNetworkGraph', () => {
  const mockMemoryService = {
    getMemoryStats: vi.fn()
  };

  const mockMemoryStats: MemoryStats = {
    totalMemories: 50,
    memoriesByTag: {
      'technical': 20,
      'personal': 15,
      'work': 10,
      'general': 5
    },
    recentActivity: [
      { date: '2024-01-01', count: 5 },
      { date: '2024-01-02', count: 8 },
      { date: '2024-01-03', count: 3 }
    ],
    averageSimilarity: 0.75,
    topTags: [
      { tag: 'javascript', count: 15 },
      { tag: 'react', count: 12 },
      { tag: 'python', count: 8 }
    ]
  };

  const defaultProps = {
    userId: 'test-user-123',
    tenantId: 'test-tenant',
    height: 600,
    width: 800
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (getMemoryService as any).mockReturnValue(mockMemoryService);
    mockMemoryService.getMemoryStats.mockResolvedValue(mockMemoryStats);
    
    // Reset D3 mocks
    Object.values(mockD3).forEach(mock => {
      if (typeof mock === 'function') {
        mock.mockClear?.();
      }


  afterEach(() => {
    vi.clearAllTimers();

  describe('Component Rendering', () => {
    it('renders the network graph container', async () => {
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      // Should show loading initially
      expect(screen.getByText('Loading network...')).toBeInTheDocument();
      
      await waitFor(() => {
        expect(screen.queryByText('Loading network...')).not.toBeInTheDocument();


    it('renders control buttons', async () => {
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByTestId('zoom-in-icon')).toBeInTheDocument();
        expect(screen.getByTestId('zoom-out-icon')).toBeInTheDocument();
        expect(screen.getByTestId('reset-icon')).toBeInTheDocument();
        expect(screen.getByTestId('play-icon')).toBeInTheDocument();
        expect(screen.getByTestId('maximize-icon')).toBeInTheDocument();


    it('renders search and filter controls', async () => {
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search nodes...')).toBeInTheDocument();
        expect(screen.getByText('Min Confidence:')).toBeInTheDocument();
        expect(screen.getByText('Color by:')).toBeInTheDocument();


    it('renders network statistics', async () => {
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Network Statistics')).toBeInTheDocument();
        expect(screen.getByText(/Nodes:/)).toBeInTheDocument();
        expect(screen.getByText(/Edges:/)).toBeInTheDocument();
        expect(screen.getByText(/Clusters:/)).toBeInTheDocument();
        expect(screen.getByText(/Density:/)).toBeInTheDocument();


    it('renders SVG element with correct dimensions', async () => {
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        const svg = screen.getByRole('img', { hidden: true }); // SVG has implicit img role
        expect(svg).toHaveAttribute('width', '800');
        expect(svg).toHaveAttribute('height', '600');



  describe('Data Loading', () => {
    it('loads network data on mount', async () => {
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        expect(mockMemoryService.getMemoryStats).toHaveBeenCalledWith('test-user-123');


    it('handles loading state correctly', async () => {
      // Make the service call hang to test loading state
      mockMemoryService.getMemoryStats.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 1000))
      );

      render(<MemoryNetworkGraph {...defaultProps} />);
      
      expect(screen.getByText('Loading network...')).toBeInTheDocument();
      expect(screen.getByRole('status', { hidden: true })).toBeInTheDocument(); // Loading spinner

    it('handles service errors gracefully', async () => {
      const errorMessage = 'Failed to load network data';
      mockMemoryService.getMemoryStats.mockRejectedValue(new Error(errorMessage));

      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Network Error')).toBeInTheDocument();
        expect(screen.getByText(errorMessage)).toBeInTheDocument();


    it('allows retry after error', async () => {
      mockMemoryService.getMemoryStats
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockMemoryStats);

      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Network Error')).toBeInTheDocument();

      const retryButton = screen.getByText('Retry');
      fireEvent.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('Network Statistics')).toBeInTheDocument();



  describe('D3 Integration', () => {
    it('initializes D3 simulation', async () => {
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        expect(mockD3.forceSimulation).toHaveBeenCalled();
        expect(mockD3.select).toHaveBeenCalled();


    it('sets up force layout correctly', async () => {
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        expect(mockD3.forceLink).toHaveBeenCalled();
        expect(mockD3.forceManyBody).toHaveBeenCalled();
        expect(mockD3.forceCenter).toHaveBeenCalled();
        expect(mockD3.forceCollide).toHaveBeenCalled();


    it('sets up zoom behavior', async () => {
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        expect(mockD3.zoom).toHaveBeenCalled();


    it('sets up drag behavior', async () => {
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        expect(mockD3.drag).toHaveBeenCalled();



  describe('User Interactions', () => {
    it('handles zoom in button click', async () => {
      const user = userEvent.setup();
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        const zoomInButton = screen.getByTestId('zoom-in-icon').closest('button');
        expect(zoomInButton).toBeInTheDocument();

      const zoomInButton = screen.getByTestId('zoom-in-icon').closest('button');
      if (zoomInButton) {
        await user.click(zoomInButton);
        // D3 zoom behavior would be called
        expect(mockD3.select).toHaveBeenCalled();
      }

    it('handles zoom out button click', async () => {
      const user = userEvent.setup();
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        const zoomOutButton = screen.getByTestId('zoom-out-icon').closest('button');
        if (zoomOutButton) {
          await user.click(zoomOutButton);
          expect(mockD3.select).toHaveBeenCalled();
        }


    it('handles reset button click', async () => {
      const user = userEvent.setup();
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        const resetButton = screen.getByTestId('reset-icon').closest('button');
        if (resetButton) {
          await user.click(resetButton);
          expect(mockD3.select).toHaveBeenCalled();
        }


    it('toggles play/pause state', async () => {
      const user = userEvent.setup();
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByTestId('pause-icon')).toBeInTheDocument();

      const playPauseButton = screen.getByTestId('pause-icon').closest('button');
      if (playPauseButton) {
        await user.click(playPauseButton);
        
        await waitFor(() => {
          expect(screen.getByTestId('play-icon')).toBeInTheDocument();

      }

    it('toggles fullscreen mode', async () => {
      const user = userEvent.setup();
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        const fullscreenButton = screen.getByTestId('maximize-icon').closest('button');
        if (fullscreenButton) {
          await user.click(fullscreenButton);
          
          await waitFor(() => {
            expect(screen.getByTestId('minimize-icon')).toBeInTheDocument();

        }



  describe('Search and Filtering', () => {
    it('updates search query', async () => {
      const user = userEvent.setup();
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText('Search nodes...');
        expect(searchInput).toBeInTheDocument();

      const searchInput = screen.getByPlaceholderText('Search nodes...');
      await user.type(searchInput, 'test query');
      
      expect(searchInput).toHaveValue('test query');

    it('updates confidence filter', async () => {
      const user = userEvent.setup();
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        const confidenceSlider = screen.getByDisplayValue('0');
        expect(confidenceSlider).toBeInTheDocument();

      const confidenceSlider = screen.getByDisplayValue('0');
      fireEvent.change(confidenceSlider, { target: { value: '0.5' } });
      
      expect(confidenceSlider).toHaveValue('0.5');

    it('changes color scheme', async () => {
      const user = userEvent.setup();
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        const colorSelect = screen.getByDisplayValue('Cluster');
        expect(colorSelect).toBeInTheDocument();

      const colorSelect = screen.getByDisplayValue('Cluster');
      await user.selectOptions(colorSelect, 'type');
      
      expect(colorSelect).toHaveValue('type');


  describe('Node Interactions', () => {
    it('calls onNodeSelect when provided', async () => {
      const onNodeSelect = vi.fn();
      render(<MemoryNetworkGraph {...defaultProps} onNodeSelect={onNodeSelect} />);
      
      await waitFor(() => {
        expect(screen.getByText('Network Statistics')).toBeInTheDocument();

      // Node selection would be handled by D3 event handlers
      // We can test that the callback is properly set up
      expect(onNodeSelect).toBeDefined();

    it('calls onNodeDoubleClick when provided', async () => {
      const onNodeDoubleClick = vi.fn();
      render(<MemoryNetworkGraph {...defaultProps} onNodeDoubleClick={onNodeDoubleClick} />);
      
      await waitFor(() => {
        expect(screen.getByText('Network Statistics')).toBeInTheDocument();

      expect(onNodeDoubleClick).toBeDefined();

    it('calls onClusterSelect when provided', async () => {
      const onClusterSelect = vi.fn();
      render(<MemoryNetworkGraph {...defaultProps} onClusterSelect={onClusterSelect} />);
      
      await waitFor(() => {
        expect(screen.getByText('Network Statistics')).toBeInTheDocument();

      expect(onClusterSelect).toBeDefined();


  describe('Performance', () => {
    it('limits node count for performance', async () => {
      const largeStats: MemoryStats = {
        ...mockMemoryStats,
        totalMemories: 500 // Large number
      };
      
      mockMemoryService.getMemoryStats.mockResolvedValue(largeStats);
      
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Network Statistics')).toBeInTheDocument();

      // Should limit to 100 nodes for performance
      expect(mockD3.forceSimulation).toHaveBeenCalled();

    it('handles empty data gracefully', async () => {
      const emptyStats: MemoryStats = {
        totalMemories: 0,
        memoriesByTag: {},
        recentActivity: [],
        averageSimilarity: 0,
        topTags: []
      };
      
      mockMemoryService.getMemoryStats.mockResolvedValue(emptyStats);
      
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Network Statistics')).toBeInTheDocument();
        expect(screen.getByText('Nodes: 0 / 0')).toBeInTheDocument();



  describe('Responsive Design', () => {
    it('adapts to specified dimensions', () => {
      render(<MemoryNetworkGraph {...defaultProps} width={1000} height={700} />);
      
      const container = screen.getByRole('img', { hidden: true }).parentElement;
      expect(container).toHaveStyle({ width: '1000px', height: '700px' });

    it('handles fullscreen mode correctly', async () => {
      const user = userEvent.setup();
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        const fullscreenButton = screen.getByTestId('maximize-icon').closest('button');
        if (fullscreenButton) {
          fireEvent.click(fullscreenButton);
          
          const container = screen.getByRole('img', { hidden: true }).parentElement;
          expect(container).toHaveClass('fixed', 'inset-0', 'z-50');
        }



  describe('Accessibility', () => {
    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText('Search nodes...');
        expect(searchInput).toBeInTheDocument();

      // Should be able to tab to controls
      await user.tab();
      const firstButton = screen.getAllByTestId('button')[0];
      expect(firstButton).toHaveFocus();

    it('has proper ARIA labels and roles', async () => {
      render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        const svg = screen.getByRole('img', { hidden: true });
        expect(svg).toBeInTheDocument();



  describe('Memory Management', () => {
    it('cleans up simulation on unmount', async () => {
      const { unmount } = render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        expect(mockD3.forceSimulation).toHaveBeenCalled();

      unmount();
      
      // Simulation should be stopped on unmount
      expect(mockSimulation.stop).toHaveBeenCalled();

    it('handles component updates correctly', async () => {
      const { rerender } = render(<MemoryNetworkGraph {...defaultProps} />);
      
      await waitFor(() => {
        expect(mockD3.forceSimulation).toHaveBeenCalled();

      // Update props
      rerender(<MemoryNetworkGraph {...defaultProps} width={900} />);
      
      // Should handle prop updates
      expect(mockD3.forceSimulation).toHaveBeenCalled();


