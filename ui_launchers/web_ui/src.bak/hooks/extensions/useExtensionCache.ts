"use client";
import { useRef } from "react";
import type { ExtensionCacheConfig } from "@/services/extensions";

export function useExtensionCache(config?: Partial<ExtensionCacheConfig>) {
  const cacheRef = useRef<Record<string, any>>({});

  const get = (key: string) => cacheRef.current[key];
  const set = (key: string, value: any) => {
    cacheRef.current[key] = value;
  };
  const clear = () => {
    cacheRef.current = {};
  };

  return { get, set, clear, config };
}
