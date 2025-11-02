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