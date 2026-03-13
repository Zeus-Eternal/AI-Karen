import { createLazyComponent } from '../../../utils/lazy-loading';

// Lazy load the ExtensionManagerComponent
const LazyExtensionManagerComponent = createLazyComponent(
  () => import('../../extensions/ExtensionManagerComponent').then(module => ({ default: module.ExtensionManagerComponent }))
);

export { LazyExtensionManagerComponent };