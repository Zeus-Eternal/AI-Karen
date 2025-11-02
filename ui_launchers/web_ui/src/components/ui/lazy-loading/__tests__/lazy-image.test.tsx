import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { LazyImage, useImagePreloader } from '../lazy-image';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: React.forwardRef<HTMLDivElement, any>(({ children, ...props }, ref) => (
      <div ref={ref} {...props}>{children}</div>
    )),
    img: React.forwardRef<HTMLImageElement, any>(({ children, ...props }, ref) => (
      <img ref={ref} {...props}>{children}</img>
    )),
  },
}));

// Mock lucide-react
vi.mock('lucide-react', () => ({
  ImageIcon: ({ className }: { className?: string }) => (
    <div className={className} data-testid="image-icon">Image</div>
  ),
  AlertCircle: ({ className }: { className?: string }) => (
    <div className={className} data-testid="alert-circle" role="alert">Error</div>
  ),
}));

// Mock IntersectionObserver
const mockIntersectionObserver = vi.fn();
mockIntersectionObserver.mockReturnValue({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),

Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  configurable: true,
  value: mockIntersectionObserver,

Object.defineProperty(global, 'IntersectionObserver', {
  writable: true,
  configurable: true,
  value: mockIntersectionObserver,

describe('LazyImage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockIntersectionObserver.mockClear();

  it('should show placeholder initially', () => {
    render(
      <LazyImage
        src="test-image.jpg"
        alt="Test image"
        className="w-32 h-32 "
      />
    );

    expect(screen.getByTestId('image-icon')).toBeInTheDocument();

  it('should show custom fallback when provided', () => {
    const CustomFallback = () => <div data-testid="custom-fallback">Custom Placeholder</div>;

    render(
      <LazyImage
        src="test-image.jpg"
        alt="Test image"
        fallback={<CustomFallback />}
      />
    );

    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();

  it('should observe intersection and load image when in view', async () => {
    const mockObserve = vi.fn();
    const mockUnobserve = vi.fn();
    
    mockIntersectionObserver.mockImplementation((callback) => ({
      observe: mockObserve,
      unobserve: mockUnobserve,
      disconnect: vi.fn(),
    }));

    render(
      <LazyImage
        src="test-image.jpg"
        alt="Test image"
      />
    );

    expect(mockIntersectionObserver).toHaveBeenCalled();
    expect(mockObserve).toHaveBeenCalled();

  it('should handle image load success', async () => {
    const onLoad = vi.fn();
    
    // Mock intersection observer to immediately trigger
    mockIntersectionObserver.mockImplementation((callback) => {
      // Simulate intersection
      setTimeout(() => {
        callback([{ isIntersecting: true }]);
      }, 0);
      
      return {
        observe: vi.fn(),
        unobserve: vi.fn(),
        disconnect: vi.fn(),
      };

    render(
      <LazyImage
        src="test-image.jpg"
        alt="Test image"
        onLoad={onLoad}
      />
    );

    // Wait for intersection to trigger
    await waitFor(() => {
      const img = screen.getByRole('img', { hidden: true });
      expect(img).toBeInTheDocument();

    // Simulate image load
    const img = screen.getByRole('img', { hidden: true });
    fireEvent.load(img);

    expect(onLoad).toHaveBeenCalled();

  it('should handle image load error', async () => {
    const onError = vi.fn();
    
    // Mock intersection observer to immediately trigger
    mockIntersectionObserver.mockImplementation((callback) => {
      setTimeout(() => {
        callback([{ isIntersecting: true }]);
      }, 0);
      
      return {
        observe: vi.fn(),
        unobserve: vi.fn(),
        disconnect: vi.fn(),
      };

    render(
      <LazyImage
        src="invalid-image.jpg"
        alt="Test image"
        onError={onError}
      />
    );

    // Wait for intersection to trigger
    await waitFor(() => {
      const img = screen.getByRole('img', { hidden: true });
      expect(img).toBeInTheDocument();

    // Simulate image error
    const img = screen.getByRole('img', { hidden: true });
    fireEvent.error(img);

    expect(onError).toHaveBeenCalled();
    
    // Should show error fallback
    await waitFor(() => {
      expect(screen.getByTestId('alert-circle')).toBeInTheDocument();


  it('should show custom error fallback', async () => {
    const CustomErrorFallback = () => <div data-testid="custom-error">Custom Error</div>;
    
    mockIntersectionObserver.mockImplementation((callback) => {
      setTimeout(() => {
        callback([{ isIntersecting: true }]);
      }, 0);
      
      return {
        observe: vi.fn(),
        unobserve: vi.fn(),
        disconnect: vi.fn(),
      };

    render(
      <LazyImage
        src="invalid-image.jpg"
        alt="Test image"
        errorFallback={<CustomErrorFallback />}
      />
    );

    await waitFor(() => {
      const img = screen.getByRole('img', { hidden: true });
      fireEvent.error(img);

    await waitFor(() => {
      expect(screen.getByTestId('custom-error')).toBeInTheDocument();


  it('should support blur data URL placeholder', () => {
    render(
      <LazyImage
        src="test-image.jpg"
        alt="Test image"
        blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ"
      />
    );

    const blurImg = screen.getByRole('img', { hidden: true });
    expect(blurImg).toHaveAttribute('src', 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ');

  it('should use custom threshold and rootMargin', () => {
    const mockObserver = {
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn(),
    };

    mockIntersectionObserver.mockReturnValue(mockObserver);

    render(
      <LazyImage
        src="test-image.jpg"
        alt="Test image"
        threshold={0.5}
        rootMargin="100px"
      />
    );

    expect(mockIntersectionObserver).toHaveBeenCalledWith(
      expect.any(Function),
      expect.objectContaining({
        threshold: 0.5,
        rootMargin: '100px',
      })
    );


describe('useImagePreloader', () => {
  // Mock Image constructor
  const mockImage = {
    onload: null as (() => void) | null,
    onerror: null as (() => void) | null,
    src: '',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock Image constructor
    global.Image = vi.fn(() => mockImage) as any;

  it('should preload images successfully', async () => {
    const TestComponent = () => {
      const { preloadImages, isImageLoaded, loadedImages } = useImagePreloader();
      
      React.useEffect(() => {
        preloadImages(['image1.jpg', 'image2.jpg']);
      }, [preloadImages]);

      return (
        <div>
          <div data-testid="loaded-count">{loadedImages.length}</div>
          <div data-testid="image1-loaded">{isImageLoaded('image1.jpg').toString()}</div>
        </div>
      );
    };

    render(<TestComponent />);

    expect(global.Image).toHaveBeenCalledTimes(2);

    // Simulate successful image loads
    if (mockImage.onload) {
      mockImage.src = 'image1.jpg';
      mockImage.onload();
      mockImage.src = 'image2.jpg';
      mockImage.onload();
    }

    await waitFor(() => {
      expect(screen.getByTestId('loaded-count')).toHaveTextContent('2');
      expect(screen.getByTestId('image1-loaded')).toHaveTextContent('true');


  it('should handle image preload failures', async () => {
    const TestComponent = () => {
      const { preloadImages, isImageFailed, failedImages } = useImagePreloader();
      
      React.useEffect(() => {
        preloadImages(['invalid-image.jpg']);
      }, [preloadImages]);

      return (
        <div>
          <div data-testid="failed-count">{failedImages.length}</div>
          <div data-testid="image-failed">{isImageFailed('invalid-image.jpg').toString()}</div>
        </div>
      );
    };

    render(<TestComponent />);

    // Simulate image load error
    if (mockImage.onerror) {
      mockImage.src = 'invalid-image.jpg';
      mockImage.onerror();
    }

    await waitFor(() => {
      expect(screen.getByTestId('failed-count')).toHaveTextContent('1');
      expect(screen.getByTestId('image-failed')).toHaveTextContent('true');


  it('should return promise results for batch preloading', async () => {
    const { preloadImages } = useImagePreloader();
    
    const promise = preloadImages(['image1.jpg', 'image2.jpg']);

    // Simulate one success and one failure
    setTimeout(() => {
      if (mockImage.onload) {
        mockImage.src = 'image1.jpg';
        mockImage.onload();
      }
      if (mockImage.onerror) {
        mockImage.src = 'image2.jpg';
        mockImage.onerror();
      }
    }, 0);

    const results = await promise;
    
    expect(results).toHaveLength(2);
    expect(results[0].status).toBe('fulfilled');
    expect(results[1].status).toBe('rejected');

