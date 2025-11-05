import { useState, useEffect, useCallback } from 'react';

interface DeviceInfo {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isTouchDevice: boolean;
  screenSize: 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  orientation: 'portrait' | 'landscape';
  platform: string;
}

export const useDeviceDetection = (): DeviceInfo => {
  const [deviceInfo, setDeviceInfo] = useState<DeviceInfo>({
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    isTouchDevice: false,
    screenSize: 'lg',
    orientation: 'landscape',
    platform: 'unknown',
  });

  useEffect(() => {
    const updateDeviceInfo = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      const userAgent = navigator.userAgent.toLowerCase();

      // Detect screen size based on Tailwind breakpoints
      let screenSize: DeviceInfo['screenSize'] = 'sm';
      if (width >= 1536) screenSize = '2xl';
      else if (width >= 1280) screenSize = 'xl';
      else if (width >= 1024) screenSize = 'lg';
      else if (width >= 768) screenSize = 'md';
      else screenSize = 'sm';

      // Detect device type
      const isMobile = width < 768 || /android|webos|iphone|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
      const isTablet = (width >= 768 && width < 1024) || /ipad|android(?!.*mobile)/i.test(userAgent);
      const isDesktop = !isMobile && !isTablet;

      // Detect touch capability
      const isTouchDevice = 'ontouchstart' in window || 
                             navigator.maxTouchPoints > 0 || 
                             // @ts-ignore
                             navigator.msMaxTouchPoints > 0;

      // Detect orientation
      const orientation = height > width ? 'portrait' : 'landscape';

      // Detect platform
      let platform = 'unknown';
      if (userAgent.includes('win')) platform = 'windows';
      else if (userAgent.includes('mac')) platform = 'macos';
      else if (userAgent.includes('linux')) platform = 'linux';
      else if (userAgent.includes('android')) platform = 'android';
      else if (userAgent.includes('iphone') || userAgent.includes('ipad')) platform = 'ios';

      setDeviceInfo({
        isMobile,
        isTablet,
        isDesktop,
        isTouchDevice,
        screenSize,
        orientation,
        platform,
      });
    };

    // Initial detection
    updateDeviceInfo();

    // Listen for resize events
    window.addEventListener('resize', updateDeviceInfo);
    window.addEventListener('orientationchange', updateDeviceInfo);

    return () => {
      window.removeEventListener('resize', updateDeviceInfo);
      window.removeEventListener('orientationchange', updateDeviceInfo);
    };
  }, []);

  return deviceInfo;
};

/**
 * Hook for responsive design based on screen size
 */
export const useResponsiveDesign = () => {
  const { screenSize, isMobile, isTablet, isDesktop } = useDeviceDetection();

  const isSmall = screenSize === 'sm';
  const isMedium = screenSize === 'md';
  const isLarge = screenSize === 'lg';
  const isExtraLarge = screenSize === 'xl' || screenSize === '2xl';

  return {
    screenSize,
    isMobile,
    isTablet,
    isDesktop,
    isSmall,
    isMedium,
    isLarge,
    isExtraLarge,
    // Responsive values
    chatHeight: isMobile ? 'calc(100vh - 120px)' : '600px',
    messageMaxWidth: isMobile ? '95%' : isTablet ? '85%' : '75%',
    inputHeight: isMobile ? '60px' : '48px',
    sidebarWidth: isMobile ? '100%' : isTablet ? '320px' : '280px',
  };
};

/**
 * Hook for touch gesture preferences
 */
export const useTouchGestures = () => {
  const { isTouchDevice, isMobile } = useDeviceDetection();
  
  return {
    enableSwipeGestures: isTouchDevice && isMobile,
    enablePullToRefresh: isTouchDevice && isMobile,
    enableLongPress: isTouchDevice,
    swipeThreshold: isMobile ? 50 : 100, // Adjusted threshold
    longPressDelay: 500, // Standard long press delay
  };
};

export default useDeviceDetection;
