// Main Task Management component
import { TaskManagementInterface as DefaultTaskManagementInterface } from './TaskManagementInterface';
export { TaskManagementInterface } from './TaskManagementInterface';

// Sub-components
export { TaskCreationComponent } from './TaskCreationComponent';
export { TaskProgressComponent } from './TaskProgressComponent';
export { TaskCancellationComponent } from './TaskCancellationComponent';
export { CompletedTasksComponent } from './CompletedTasksComponent';

// Type definitions
export type { Task, TaskStatus, TaskPriority, TaskFilter } from './types';

// Default exports
export default DefaultTaskManagementInterface;