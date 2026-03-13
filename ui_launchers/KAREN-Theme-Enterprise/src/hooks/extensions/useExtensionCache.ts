"use client";
import { useRef } from "react";

export function useExtensionCache(config?: Record<string, unknown>) {
  const cacheRef = useRef<Record<string, unknown>>({});

  const get = (key: string) => cacheRef.current[key];
  const set = (key: string, value: unknown) => {
    cacheRef.current[key] = value;
  };
  const clear = () => {
    cacheRef.current = {};
  };

  return { get, set, clear, config };
}
