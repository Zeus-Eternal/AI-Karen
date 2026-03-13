"use client";

import { useCallback, useState } from 'react';

export function useImagePreloader() {
  const [loadedImages, setLoadedImages] = useState<Set<string>>(new Set());
  const [failedImages, setFailedImages] = useState<Set<string>>(new Set());

  const preloadImages = useCallback((urls: string[]) => {
    const promises = urls.map((url) => {
      return new Promise<string>((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
          setLoadedImages((previous) => new Set([...previous, url]));
          resolve(url);
        };
        img.onerror = () => {
          setFailedImages((previous) => new Set([...previous, url]));
          reject(new Error(`Failed to load image: ${url}`));
        };
        img.src = url;
      });
    });

    return Promise.allSettled(promises);
  }, []);

  const isImageLoaded = useCallback((url: string) => {
    return loadedImages.has(url);
  }, [loadedImages]);

  const isImageFailed = useCallback((url: string) => {
    return failedImages.has(url);
  }, [failedImages]);

  return {
    preloadImages,
    isImageLoaded,
    isImageFailed,
    loadedImages: Array.from(loadedImages),
    failedImages: Array.from(failedImages),
  };
}

export default useImagePreloader;
