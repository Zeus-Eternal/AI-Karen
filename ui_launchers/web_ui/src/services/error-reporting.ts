export class ErrorReportingService {
  async reportError(errorData: any): Promise<void> {
    // Mock error reporting service
    console.error('Error reported:', errorData);
  }

  getStoredReports(): any[] {
    // Mock stored reports
    return [];
  }
}