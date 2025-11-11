declare module "vite" {
  export type PluginOption = unknown;

  export interface UserConfig {
    plugins?: PluginOption[];
    resolve?: Record<string, unknown>;
    server?: Record<string, unknown>;
    build?: Record<string, unknown>;
    optimizeDeps?: Record<string, unknown>;
    [key: string]: unknown;
  }

  export function defineConfig<T extends UserConfig>(config: T): T;
}

declare module "@vitejs/plugin-react-swc" {
  import type { PluginOption } from "vite";

  interface ReactPluginOptions {
    [key: string]: unknown;
  }

  export default function reactPlugin(
    options?: ReactPluginOptions
  ): PluginOption;
}
