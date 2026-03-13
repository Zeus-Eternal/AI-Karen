export class ErrorRecoveryService {
  async attemptRecovery(_error: Error): Promise<boolean> {
    // Mock error recovery service
    return false;
  }
  async getRecoveryStrategy(_error: Error, _context: unknown): Promise<unknown> {
    // Mock recovery strategy
    return {
      canRecover: false,
      strategy: 'none',
      retryDelay: 1000
    };
  }
}
