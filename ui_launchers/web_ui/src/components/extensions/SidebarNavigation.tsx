"use client";

import React, { useEffect, useState } from "react";
import { useExtensionContext, navigationActions } from "@/extensions";
import { getPluginService, getExtensionService, type PluginCategory, type ExtensionInfo } from "@/services";

export default function SidebarNavigation() {
  const { state, dispatch } = useExtensionContext();
  const [pluginCategories, setPluginCategories] = useState<PluginCategory[]>([]);
  const [extensions, setExtensions] = useState<ExtensionInfo[]>([]);

  useEffect(() => {
    getPluginService()
      .getPluginsByCategory()
      .then(setPluginCategories)
      .catch(() => {});
    getExtensionService()
      .getInstalledExtensions()
      .then(setExtensions)
      .catch(() => {});
  }, []);

  if (state.currentCategory === "Plugins") {
    return (
      <div className="space-y-4">
        {pluginCategories.map((cat) => (
          <div key={cat.name} className="space-y-1">
            <p className="text-xs font-semibold text-muted-foreground uppercase sm:text-sm md:text-base">
              {cat.name}
            </p>
            <ul className="pl-2 space-y-1">
              {cat.plugins.map((p) => (
                <li key={p.name}>
                  <button
                    type="button"
                    className="text-sm hover:underline md:text-base lg:text-lg"
                    onClick={() => {
                      navigationActions
                        .navigateToPluginProvider(cat.name.toLowerCase(), p.name)
                        .forEach((action) => dispatch(action))
                    }}
                  >
                    {p.name}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    );
  }

  return (
    <ul className="space-y-1">
      {extensions.map((ext) => (
        <li key={ext.name}>
          <button
            type="button"
            className="text-sm hover:underline md:text-base lg:text-lg"
            onClick={() => {
              dispatch({
                type: "PUSH_BREADCRUMB",
                item: { level: "items", id: ext.name, name: ext.name },
              })
            }}
          >
            {ext.name}
          </button>
        </li>
      ))}
    </ul>
  );
}
