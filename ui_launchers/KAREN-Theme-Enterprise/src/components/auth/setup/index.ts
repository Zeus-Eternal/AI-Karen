export { SetupWizard } from './SetupWizard';
export { SetupRouteGuard, FirstRunRedirect } from './SetupRouteGuard';
export { useSetupRouteAccess, withSetupRouteGuard } from './SetupRouteGuardAccess';

// Step components
export { WelcomeStep } from './steps/WelcomeStep';
export { AdminDetailsStep } from './steps/AdminDetailsStep';
export { EmailVerificationStep } from './steps/EmailVerificationStep';
export { SetupCompleteStep } from './steps/SetupCompleteStep';

// Types
export type { SetupWizardProps, SetupFormData, SetupStepProps } from './SetupWizard';
export type { SetupRouteGuardProps } from './SetupRouteGuard';
export type { SetupCompleteStepProps } from './steps/SetupCompleteStep';
