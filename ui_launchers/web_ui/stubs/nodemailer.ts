export interface MockTransport {
  sendMail: (options: Record<string, any>) => Promise<{ messageId: string }>;
  verify: () => Promise<boolean>;
}

const mockTransportState = {
  createCalls: 0,
  sendCalls: [] as Record<string, any>[],
  verifyCalls: 0,
};

export const createTransport = (): MockTransport => {
  mockTransportState.createCalls += 1;
  return {
    async sendMail(options: Record<string, any>) {
      mockTransportState.sendCalls.push(options);
      return { messageId: 'mock-transport-id' };
    },
    async verify() {
      mockTransportState.verifyCalls += 1;
      return true;
    },
  };
};

export default {
  createTransport,
  mockTransportState,
};
