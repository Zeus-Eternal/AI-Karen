"use client";
import { useEffect, useState } from "react";
import type { ExtensionPlugin } from "@/extensions";

export interface UseExtensionsResult {
  extensions: ExtensionPlugin[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useExtensions(): UseExtensionsResult {
  const [extensions, setExtensions] = useState<ExtensionPlugin[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchExtensions = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/extensions");
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      setExtensions(Array.isArray(data.extensions) ? data.extensions : []);
      setError(null);
    } catch (err: unknown) {
      const error = err as Error;
      setError(error.message ?? "Failed to fetch extensions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExtensions();
  }, []);

  return {
    extensions,
    loading,
    error,
    refresh: fetchExtensions,
  };
}
