"use client";

import React from 'react';

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ArrowLeft, PanelLeft } from "lucide-react";
import ExtensionBreadcrumbs from "./ExtensionBreadcrumbs";
import ExtensionStats from "./ExtensionStats";
import { useExtensionContext } from "@/extensions/ExtensionContext";

export default function ExtensionHeader() {
  const {
    state: { currentCategory, level },
    dispatch,
  } = useExtensionContext();

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Extension Manager</h2>
        <Button variant="ghost" size="icon" aria-label="Toggle sidebar">
          <PanelLeft className="h-5 w-5 text-muted-foreground" />
          <span className="sr-only">Toggle sidebar</span>
        </Button>
      </div>
      <Tabs
        value={currentCategory}
        onValueChange={(val) => dispatch({ type: "SET_CATEGORY", category: val as any })}
        className="w-full"
      >
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="Plugins">Plugins</TabsTrigger>
          <TabsTrigger value="Extensions">Extensions</TabsTrigger>
        </TabsList>
      </Tabs>
      {level > 0 && (
        <Button
          variant="ghost"
          size="sm"
          className="px-1 gap-1 h-6"
          onClick={() => dispatch({ type: "GO_BACK" })}
        >
          <ArrowLeft className="h-3 w-3 " /> Back
        </Button>
      )}
      <ExtensionBreadcrumbs />
      <ExtensionStats />
    </div>
  );
}
