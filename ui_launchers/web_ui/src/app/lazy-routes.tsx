'use client';

import { createLazyRoute } from '@/components/ui/lazy-loading';

// Lazy load heavy components and routes
export const LazyChatPage = createLazyRoute(
  () => import('./chat/page'),
  {
    preload: false, // Don't preload by default
  }
);

export const LazyModelsPage = createLazyRoute(
  () => import('./models/page'),
  {
    preload: false,
  }
);

export const LazyDeveloperPage = createLazyRoute(
  () => import('./developer/page'),
  {
    preload: false,
  }
);

export const LazyProfilePage = createLazyRoute(
  () => import('./profile/page'),
  {
    preload: false,
  }
);

// Heavy components that should be lazy loaded
// Temporarily commented out - copilot page doesn't exist yet
// export const LazyCopilotPage = createLazyRoute(
//   () => import('./copilot/page'),
//   {
//     preload: false,
//   }
// );

// Test components for lazy loading
export const LazyTestPage = createLazyRoute(
  () => import('./test/page'),
  {
    preload: false,
  }
);

// Model selector test (likely heavy with charts/visualizations)
export const LazyModelSelectorTest = createLazyRoute(
  () => import('./model-selector-test/page'),
  {
    preload: false,
  }
);

// Chat test page
export const LazyChatTest = createLazyRoute(
  () => import('./chat-test/page'),
  {
    preload: false,
  }
);