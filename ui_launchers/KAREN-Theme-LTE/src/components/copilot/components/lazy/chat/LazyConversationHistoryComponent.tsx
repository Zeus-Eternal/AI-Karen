import { createLazyComponent } from '../../../utils/lazy-loading';

// Lazy load the ConversationHistoryComponent
const LazyConversationHistoryComponent = createLazyComponent(
  () => import('../../chat/ConversationHistoryComponent').then(module => ({ default: module.ConversationHistoryComponent }))
);

export { LazyConversationHistoryComponent };