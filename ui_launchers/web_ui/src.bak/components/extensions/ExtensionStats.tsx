"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { getPluginService, getExtensionService } from "@/services";

export default function ExtensionStats() {
  const [pluginCount, setPluginCount] = useState(0);
  const [extensionCount, setExtensionCount] = useState(0);

  useEffect(() => {
    async function load() {
      try {
        const plugins = await getPluginService().getAvailablePlugins();
        setPluginCount(plugins.length);
      } catch (error) {
        console.error("Failed to load plugins", error);
      }
      try {
        const exts = await getExtensionService().getInstalledExtensions();
        setExtensionCount(exts.length);
      } catch (error) {
        console.error("Failed to load extensions", error);
      }
    }
    load();
  }, []);

  return (
    <Card>
      <CardContent className="py-2 text-sm grid grid-cols-2 gap-2">
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
