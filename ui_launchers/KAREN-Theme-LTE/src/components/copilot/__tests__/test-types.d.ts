// Type definitions for testing

// Jest types
declare namespace jest {
  interface Mock<T extends (...args: any[]) => any> {
    (...args: Parameters<T>): ReturnType<T>;
    mock: {
      calls: Parameters<T>[];
    };
    mockImplementation: (fn: T) => Mock<T>;
    mockClear: () => void;
    mockReset: () => void;
    mockRestore: () => void;
    mockReturnValue: (value: ReturnType<T>) => Mock<T>;
    mockResolvedValue: (value: ReturnType<T>) => Mock<T>;
    mockRejectedValue: (value: any) => Mock<T>;
  }

  interface MockedFunction<T extends (...args: any[]) => any> extends Mock<T> {
    mock: {
      calls: Parameters<T>[];
    };
  }

  function fn<T extends (...args: any[]) => any>(implementation?: T): Mock<T>;
}

// Global types for testing
declare const describe: (name: string, fn: () => void) => void;
declare const test: (name: string, fn: () => void) => void;
declare const beforeEach: (fn: () => void) => void;
declare const afterEach: (fn: () => void) => void;
declare const beforeAll: (fn: () => void) => void;
declare const afterAll: (fn: () => void) => void;

// Expect types
declare const expect: {
  <T = any>(actual: T): {
    toBe: (expected: T) => void;
    toEqual: (expected: T) => void;
    toBeDefined: () => void;
    toBeUndefined: () => void;
    toBeNull: () => void;
    toBeTruthy: () => void;
    toBeFalsy: () => void;
    toContain: (expected: any) => void;
    toHaveBeenCalled: () => void;
    toHaveBeenCalledTimes: (n: number) => void;
    toHaveBeenCalledWith: (...args: any[]) => void;
    toHaveBeenCalledBefore: (mock: jest.Mock<any>) => void;
    toHaveLastReturnedWith: (value: any) => void;
    toHaveNthReturnedWith: (n: number, value: any) => void;
    toHaveReturned: () => void;
    toHaveReturnedTimes: (n: number) => void;
    toHaveReturnedWith: (value: any) => void;
    toThrow: (expected?: any) => void;
    toThrowError: (expected?: any) => void;
    not: any;
    resolves: {
      toEqual: (expected: any) => Promise<void>;
      toBe: (expected: any) => Promise<void>;
    };
    rejects: {
      toEqual: (expected: any) => Promise<void>;
      toBe: (expected: any) => Promise<void>;
      toThrow: (expected?: any) => Promise<void>;
    };
    // Testing Library matchers
    toHaveLength: (length: number) => void;
    toBeGreaterThan: (value: number) => void;
    toBeLessThan: (value: number) => void;
    toHaveAttribute: (name: string, value?: string) => void;
    toHaveClass: (className: string) => void;
    toHaveTextContent: (text: string) => void;
    toHaveStyle: (style: Record<string, string>) => void;
    toBeInTheDocument: () => void;
    toBeDisabled: () => void;
  };
  // Testing Library utility functions
  objectContaining: (obj: any) => any;
  arrayContaining: (arr: any[]) => any;
  stringContaining: (str: string) => any;
  stringMatching: (pattern: RegExp) => any;
  any: (type: any) => any;
};

// Global mock objects
declare const jest: {
  fn: <T extends (...args: any[]) => any>(implementation?: T) => jest.Mock<T>;
  mock: (moduleName: string, factory?: () => any) => void;
  unmock: (moduleName: string) => void;
  clearAllMocks: () => void;
  resetAllMocks: () => void;
  restoreAllMocks: () => void;
  useFakeTimers: () => void;
  useRealTimers: () => void;
  runAllTimers: () => void;
  runOnlyPendingTimers: () => void;
  advanceTimersByTime: (msToRun: number) => void;
  clearAllTimers: () => void;
  spyOn: (obj: any, methodName: string) => any;
};

// Testing Library types
declare const screen: {
  getByText: (text: string | RegExp) => HTMLElement;
  getByTestId: (testId: string) => HTMLElement;
  getByRole: (role: string) => HTMLElement;
  getByLabelText: (text: string | RegExp) => HTMLElement;
  getByPlaceholderText: (text: string | RegExp) => HTMLElement;
  getByAltText: (text: string | RegExp) => HTMLElement;
  getByTitle: (text: string | RegExp) => HTMLElement;
  getByDisplayValue: (value: string | RegExp) => HTMLElement;
  queryByText: (text: string | RegExp) => HTMLElement | null;
  queryByTestId: (testId: string) => HTMLElement | null;
  queryByRole: (role: string) => HTMLElement | null;
  queryByLabelText: (text: string | RegExp) => HTMLElement | null;
  queryByPlaceholderText: (text: string | RegExp) => HTMLElement | null;
  queryByAltText: (text: string | RegExp) => HTMLElement | null;
  queryByTitle: (text: string | RegExp) => HTMLElement | null;
  queryByDisplayValue: (value: string | RegExp) => HTMLElement | null;
  findAllByText: (text: string | RegExp) => Promise<HTMLElement[]>;
  findAllByTestId: (testId: string) => Promise<HTMLElement[]>;
  findAllByRole: (role: string) => Promise<HTMLElement[]>;
  findAllByLabelText: (text: string | RegExp) => Promise<HTMLElement[]>;
  findAllByPlaceholderText: (text: string | RegExp) => Promise<HTMLElement[]>;
  findAllByAltText: (text: string | RegExp) => Promise<HTMLElement[]>;
  findAllByTitle: (text: string | RegExp) => Promise<HTMLElement[]>;
  findAllByDisplayValue: (value: string | RegExp) => Promise<HTMLElement[]>;
  findByText: (text: string | RegExp) => Promise<HTMLElement>;
  findByTestId: (testId: string) => Promise<HTMLElement>;
  findByRole: (role: string) => Promise<HTMLElement>;
  findByLabelText: (text: string | RegExp) => Promise<HTMLElement>;
  findByPlaceholderText: (text: string | RegExp) => Promise<HTMLElement>;
  findByAltText: (text: string | RegExp) => Promise<HTMLElement>;
  findByTitle: (text: string | RegExp) => Promise<HTMLElement>;
  findByDisplayValue: (value: string | RegExp) => Promise<HTMLElement>;
};

// React Testing Library types
declare const render: (
  ui: React.ReactElement,
  options?: {
    container?: HTMLElement;
    baseElement?: HTMLElement;
    hydrate?: boolean;
    wrapper?: React.ComponentType<{ children: React.ReactNode }>;
  }
) => {
  container: HTMLElement;
  baseElement: HTMLElement;
  debug: (baseElement?: HTMLElement) => void;
  rerender: (ui: React.ReactElement) => void;
  unmount: () => void;
};

// FireEvent types
declare const fireEvent: {
  click: (element: HTMLElement) => void;
  change: (element: HTMLElement, value: any) => void;
  submit: (element: HTMLElement) => void;
  keyDown: (element: HTMLElement, key: string) => void;
  keyUp: (element: HTMLElement, key: string) => void;
  focus: (element: HTMLElement) => void;
  blur: (element: HTMLElement) => void;
};

// UserEvent types
declare const userEvent: {
  type: (element: HTMLElement, text: string) => Promise<void>;
  click: (element: HTMLElement) => Promise<void>;
  clear: (element: HTMLElement) => Promise<void>;
  tab: () => Promise<void>;
  keyboard: (text: string) => Promise<void>;
};