"use client";

import * as React from 'react';

export function useContainerQuery(containerName: string, query: string): boolean {
  const [matches, setMatches] = React.useState(false);

  React.useEffect(() => {
    if (!window.CSS || !window.CSS.supports || !window.CSS.supports('container-type', 'inline-size')) {
      return;
    }

    const mediaQuery = window.matchMedia(`@container ${containerName} ${query}`);

    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    setMatches(mediaQuery.matches);
    mediaQuery.addEventListener('change', handleChange);

    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, [containerName, query]);

  return matches;
}

type ContainerDimensions = {
  width: number;
  height: number;
  size: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
};

export function useContainerSize(ref: React.RefObject<HTMLElement>): ContainerDimensions {
  const [dimensions, setDimensions] = React.useState<ContainerDimensions>({
    width: 0,
    height: 0,
    size: 'xs',
  });

  React.useEffect(() => {
    if (!ref.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;

        let size: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' = 'xs';

        if (width >= 1536) size = '2xl';
        else if (width >= 1280) size = 'xl';
        else if (width >= 1024) size = 'lg';
        else if (width >= 768) size = 'md';
        else if (width >= 640) size = 'sm';

        setDimensions({ width, height, size });
      }
    });

    resizeObserver.observe(ref.current);

    return () => {
      resizeObserver.disconnect();
    };
  }, [ref]);

  return dimensions;
}

export default useContainerQuery;
