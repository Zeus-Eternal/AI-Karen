import { export { SetupWizard } from './SetupWizard';
import { export { SetupRouteGuard, useSetupRouteAccess, withSetupRouteGuard, FirstRunRedirect } from './SetupRouteGuard';

// Step components
import { export { WelcomeStep } from './steps/WelcomeStep';
import { export { AdminDetailsStep } from './steps/AdminDetailsStep';
import { export { EmailVerificationStep } from './steps/EmailVerificationStep';
import { export { SetupCompleteStep } from './steps/SetupCompleteStep';

// Types
import { export type { SetupWizardProps, SetupFormData, SetupStepProps } from './SetupWizard';
import { export type { SetupRouteGuardProps } from './SetupRouteGuard';
import { export type { SetupCompleteStepProps } from './steps/SetupCompleteStep';