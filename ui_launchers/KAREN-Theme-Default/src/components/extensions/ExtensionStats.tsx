"use client";

import { useEffect, useState } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { getPluginService } from "@/services/pluginService";
import { getExtensionService } from "@/services/extensionService";
export default function ExtensionStats() {
  const [pluginCount, setPluginCount] = useState(0);
  const [extensionCount, setExtensionCount] = useState(0);
  useEffect(() => {
    async function load() {
      try {
        const plugins = await getPluginService().getAvailablePlugins();
        setPluginCount(plugins.length);
      } catch {
      }
      try {
        const exts = await getExtensionService().getInstalledExtensions();
        setExtensionCount(exts.length);
      } catch {
      }
    }
    load();
  }, []);
  return (
    <Card>
      <CardContent className="py-2 text-sm grid grid-cols-2 gap-2 md:text-base lg:text-lg">
        <div className="flex items-center justify-between">
          <span>Plugins</span>
          <span className="font-medium">{pluginCount}</span>
        </div>
        <div className="flex items-center justify-between">
          <span>Extensions</span>
          <span className="font-medium">{extensionCount}</span>
        </div>
      </CardContent>
    </Card>
  );
}
