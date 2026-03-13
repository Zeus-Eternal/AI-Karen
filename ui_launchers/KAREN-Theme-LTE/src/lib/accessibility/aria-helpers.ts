/**
 * ARIA Helpers for accessibility
 * Provides utilities for managing ARIA live regions and announcements
 */

export type AriaLivePriority = 'polite' | 'assertive';

export interface UseAriaLiveRegionReturn {
  announce: (message: string, priority?: AriaLivePriority) => void;
}

/**
 * Hook for managing ARIA live regions
 * Used to announce dynamic content changes to screen readers
 */
export function useAriaLiveRegion(): UseAriaLiveRegionReturn {
  const announce = (message: string, priority: AriaLivePriority = 'polite') => {
    // Find or create live region
    let liveRegion = document.getElementById('aria-live-region');
    
    if (!liveRegion) {
      liveRegion = document.createElement('div');
      liveRegion.id = 'aria-live-region';
      liveRegion.setAttribute('aria-live', priority);
      liveRegion.setAttribute('aria-atomic', 'true');
      liveRegion.className = 'sr-only';
      document.body.appendChild(liveRegion);
    }
    
    // Announce the message
    liveRegion.textContent = message;
    
    // Clear after announcement
    setTimeout(() => {
      liveRegion.textContent = '';
    }, 1000);
  };

  return { announce };
}

export default useAriaLiveRegion;
