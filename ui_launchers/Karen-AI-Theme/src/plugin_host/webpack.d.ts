/* eslint-disable @typescript-eslint/no-explicit-any */
declare module '*.tsx' {
  const component: React.ComponentType<Record<string, unknown>>;
  export default component;
}

declare module '*.jsx' {
  const component: React.ComponentType<Record<string, unknown>>;
  export default component;
}

// Webpack require.context type declarations
interface RequireContext {
  keys(): string[];
  (id: string): any;
  <T>(id: string): T;
  resolve(id: string): string;
  id: string;
}

interface NodeRequire {
  context(
    directory: string,
    useSubdirectories: boolean,
    regExp: RegExp
  ): RequireContext;
}

declare namespace NodeJS {
  interface Require extends NodeRequire {}
}