import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useOptimisticUpdates, useOptimisticForm, useOptimisticList } from '../use-optimistic-updates';

// Mock the UI store
const mockSetLoading = vi.fn();
const mockSetError = vi.fn();
const mockClearError = vi.fn();

vi.mock('../../store', () => ({
  useUIStore: {
    getState: () => ({
      setLoading: mockSetLoading,
      setError: mockSetError,
      clearError: mockClearError,
    }),
  },
  selectLoadingState: vi.fn(),
  selectErrorState: vi.fn(),
}));

describe('useOptimisticUpdates', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should perform optimistic update successfully', async () => {
    const { result } = renderHook(() => useOptimisticUpdates());
    
    const mockUpdateFn = vi.fn().mockResolvedValue('success');
    const mockOptimisticUpdate = vi.fn();
    const mockOnSuccess = vi.fn();
    
    await act(async () => {
      const response = await result.current.performOptimisticUpdate({
        key: 'test-update',
        updateFn: mockUpdateFn,
        optimisticUpdate: mockOptimisticUpdate,
        onSuccess: mockOnSuccess,
      });
      
      expect(response).toBe('success');
    });
    
    expect(mockOptimisticUpdate).toHaveBeenCalled();
    expect(mockUpdateFn).toHaveBeenCalled();
    expect(mockOnSuccess).toHaveBeenCalledWith('success');
    expect(mockClearError).toHaveBeenCalledWith('test-update');
    expect(mockSetLoading).toHaveBeenCalledWith('test-update', true);
    expect(mockSetLoading).toHaveBeenCalledWith('test-update', false);
  });

  it('should handle errors and retry', async () => {
    const { result } = renderHook(() => useOptimisticUpdates());
    
    const mockUpdateFn = vi.fn()
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValue('success');
    const mockOptimisticUpdate = vi.fn();
    const mockRevertUpdate = vi.fn();
    const mockOnSuccess = vi.fn();
    
    await act(async () => {
      const response = await result.current.performOptimisticUpdate({
        key: 'test-retry',
        updateFn: mockUpdateFn,
        optimisticUpdate: mockOptimisticUpdate,
        revertUpdate: mockRevertUpdate,
        onSuccess: mockOnSuccess,
        retryConfig: { maxRetries: 2, retryDelay: 10 },
      });
      
      expect(response).toBe('success');
    });
    
    expect(mockUpdateFn).toHaveBeenCalledTimes(2);
    expect(mockOnSuccess).toHaveBeenCalledWith('success');
  });

  it('should revert on max retries reached', async () => {
    const { result } = renderHook(() => useOptimisticUpdates());
    
    const mockUpdateFn = vi.fn().mockRejectedValue(new Error('Persistent error'));
    const mockOptimisticUpdate = vi.fn();
    const mockRevertUpdate = vi.fn();
    const mockOnError = vi.fn();
    
    await act(async () => {
      try {
        await result.current.performOptimisticUpdate({
          key: 'test-revert',
          updateFn: mockUpdateFn,
          optimisticUpdate: mockOptimisticUpdate,
          revertUpdate: mockRevertUpdate,
          onError: mockOnError,
          retryConfig: { maxRetries: 1, retryDelay: 10 },
        });
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
      }
    });
    
    expect(mockRevertUpdate).toHaveBeenCalled();
    expect(mockOnError).toHaveBeenCalled();
    expect(mockSetError).toHaveBeenCalledWith('test-revert', 'Persistent error');
  });

  it('should track optimistic states', () => {
    const { result } = renderHook(() => useOptimisticUpdates());
    
    act(() => {
      result.current.performOptimisticUpdate({
        key: 'test-state',
        updateFn: () => new Promise(resolve => setTimeout(resolve, 100)),
        optimisticUpdate: () => {},
      });
    });
    
    expect(result.current.isOptimistic('test-state')).toBe(true);
    expect(result.current.optimisticStates['test-state']).toBe(true);
  });
});

describe('useOptimisticForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should handle form submission with optimistic updates', async () => {
    const { result } = renderHook(() => useOptimisticForm());
    
    const formData = { name: 'John', email: 'john@example.com' };
    const mockSubmitFn = vi.fn().mockResolvedValue({ id: 1, ...formData });
    const mockOnSuccess = vi.fn();
    
    await act(async () => {
      await result.current.submitForm(formData, mockSubmitFn, {
        key: 'form-submit',
        onSuccess: mockOnSuccess,
      });
    });
    
    expect(mockSubmitFn).toHaveBeenCalledWith(formData);
    expect(mockOnSuccess).toHaveBeenCalledWith({ id: 1, ...formData });
    expect(result.current.formData).toBe(null);
    expect(result.current.isSubmitting).toBe(false);
  });

  it('should track form submission state', async () => {
    const { result } = renderHook(() => useOptimisticForm());
    
    const formData = { name: 'John' };
    const mockSubmitFn = vi.fn().mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve(formData), 100))
    );
    
    act(() => {
      result.current.submitForm(formData, mockSubmitFn);
    });
    
    expect(result.current.isSubmitting).toBe(true);
    expect(result.current.submittedData).toEqual(formData);
    
    await waitFor(() => {
      expect(result.current.isSubmitting).toBe(false);
    });
  });

  it('should reset form state', () => {
    const { result } = renderHook(() => useOptimisticForm());
    
    act(() => {
      result.current.submitForm({ name: 'John' }, vi.fn());
    });
    
    act(() => {
      result.current.resetForm();
    });
    
    expect(result.current.formData).toBe(null);
    expect(result.current.submittedData).toBe(null);
    expect(result.current.isSubmitting).toBe(false);
  });
});

describe('useOptimisticList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should add items optimistically', async () => {
    const initialItems = [{ id: 1, name: 'Item 1' }];
    const { result } = renderHook(() => useOptimisticList(initialItems));
    
    const newItem = { id: 2, name: 'Item 2' };
    const mockAddFn = vi.fn().mockResolvedValue(newItem);
    
    act(() => {
      result.current.addItem(newItem, mockAddFn);
    });
    
    // Item should be added optimistically
    expect(result.current.items).toHaveLength(2);
    expect(result.current.items).toContain(newItem);
    
    await waitFor(() => {
      expect(mockAddFn).toHaveBeenCalledWith(newItem);
    });
  });

  it('should remove items optimistically', async () => {
    const initialItems = [
      { id: 1, name: 'Item 1' },
      { id: 2, name: 'Item 2' },
    ];
    const { result } = renderHook(() => useOptimisticList(initialItems));
    
    const itemToRemove = initialItems[0];
    const mockRemoveFn = vi.fn().mockResolvedValue(undefined);
    
    act(() => {
      result.current.removeItem(itemToRemove, mockRemoveFn);
    });
    
    // Item should be removed optimistically
    expect(result.current.items).toHaveLength(1);
    expect(result.current.items).not.toContain(itemToRemove);
    
    await waitFor(() => {
      expect(mockRemoveFn).toHaveBeenCalledWith(itemToRemove);
    });
  });

  it('should update items optimistically', async () => {
    const initialItems = [{ id: 1, name: 'Item 1' }];
    const { result } = renderHook(() => useOptimisticList(initialItems));
    
    const oldItem = initialItems[0];
    const newItem = { id: 1, name: 'Updated Item 1' };
    const mockUpdateFn = vi.fn().mockResolvedValue(newItem);
    
    act(() => {
      result.current.updateItem(oldItem, newItem, mockUpdateFn);
    });
    
    // Item should be updated optimistically
    expect(result.current.items).toHaveLength(1);
    expect(result.current.items[0]).toEqual(newItem);
    
    await waitFor(() => {
      expect(mockUpdateFn).toHaveBeenCalledWith(oldItem, newItem);
    });
  });

  it('should revert changes on error', async () => {
    const initialItems = [{ id: 1, name: 'Item 1' }];
    const { result } = renderHook(() => useOptimisticList(initialItems));
    
    const newItem = { id: 2, name: 'Item 2' };
    const mockAddFn = vi.fn().mockRejectedValue(new Error('Add failed'));
    
    act(() => {
      result.current.addItem(newItem, mockAddFn);
    });
    
    // Item should be added optimistically
    expect(result.current.items).toHaveLength(2);
    
    await waitFor(() => {
      // Item should be reverted on error
      expect(result.current.items).toHaveLength(1);
      expect(result.current.items).not.toContain(newItem);
    });
  });
});