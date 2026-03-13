import { createLazyComponent } from '../../../utils/lazy-loading';

// Lazy load the ExtensionUIRenderer
const LazyExtensionUIRenderer = createLazyComponent(
  () => import('../../extensions/ExtensionUIRenderer')
);

export { LazyExtensionUIRenderer };