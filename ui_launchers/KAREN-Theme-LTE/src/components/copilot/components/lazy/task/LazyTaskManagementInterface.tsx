import { createLazyComponent } from '../../../utils/lazy-loading';

// Lazy load the TaskManagementInterface
const LazyTaskManagementInterface = createLazyComponent(
  () => import('../../task/TaskManagementInterface').then(module => ({ default: module.TaskManagementInterface }))
);

export { LazyTaskManagementInterface };