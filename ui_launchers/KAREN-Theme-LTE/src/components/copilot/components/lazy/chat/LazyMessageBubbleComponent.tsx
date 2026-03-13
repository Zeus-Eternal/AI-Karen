import { createLazyComponent } from '../../../utils/lazy-loading';

// Lazy load the MessageBubbleComponent
const LazyMessageBubbleComponent = createLazyComponent(
  () => import('../../chat/MessageBubbleComponent').then(module => ({ default: module.MessageBubbleComponent }))
);

export { LazyMessageBubbleComponent };