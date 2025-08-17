"use client";
import { useState } from "react";

export interface MarketplaceExtension {
  id: string;
  name: string;
}

export function useExtensionMarketplace() {
  const [extensions, setExtensions] = useState<MarketplaceExtension[]>([]);
  return { extensions, refresh: async () => setExtensions([]) };
}
