import { createLazyComponent } from '../../../utils/lazy-loading';

// Lazy load the VoiceRecorderComponent
const LazyVoiceRecorderComponent = createLazyComponent(
  () => import('../../chat/VoiceRecorderComponent').then(module => ({ default: module.VoiceRecorderComponent }))
);

export { LazyVoiceRecorderComponent };