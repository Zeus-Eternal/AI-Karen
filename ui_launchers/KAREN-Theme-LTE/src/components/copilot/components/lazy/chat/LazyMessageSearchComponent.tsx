import { createLazyComponent } from '../../../utils/lazy-loading';

// Lazy load the MessageSearchComponent
const LazyMessageSearchComponent = createLazyComponent(
  () => import('../../chat/MessageSearchComponent').then(module => ({ default: module.MessageSearchComponent }))
);

export { LazyMessageSearchComponent };