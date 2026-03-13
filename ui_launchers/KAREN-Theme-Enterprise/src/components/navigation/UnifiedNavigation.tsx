"use client";

import React, { useState } from 'react';
import { Search, X, ArrowLeft } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider as UiSidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar';
import { useNavigation, navigationItems, type NavigationItem } from '@/providers/NavigationProvider';

interface UnifiedNavigationProps {
  className?: string;
}

export const UnifiedNavigation: React.FC<UnifiedNavigationProps> = ({ className }) => {
  const {
    activeView,
    setActiveView,
    navigateBack,
    canNavigateBack,
    searchQuery,
    setSearchQuery,
    filteredNavigationItems,
    isSearchMode,
    setIsSearchMode,
  } = useNavigation();

  const handleNavigationItemClick = (item: NavigationItem) => {
    setActiveView(item.id);
  };

  const handleSearchToggle = () => {
    setIsSearchMode(!isSearchMode);
    if (isSearchMode) {
      setSearchQuery('');
    }
  };

  const mainNavigationItems = navigationItems.filter(item => item.category === 'main');
  const pluginNavigationItems = navigationItems.filter(item => item.category === 'plugin');

  return (
    <UiSidebarProvider>
      <Sidebar className={cn("border-r", className)}>
        <SidebarHeader className="p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold tracking-tight">Navigation</h2>
            <div className="flex items-center gap-2">
              {canNavigateBack && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={navigateBack}
                  aria-label="Go back"
                  title="Go back to previous view"
                >
                  <ArrowLeft className="h-4 w-4" />
                </Button>
              )}
              <Button
                variant="ghost"
                size="icon"
                onClick={handleSearchToggle}
                aria-label={isSearchMode ? "Close search" : "Search navigation"}
                title={isSearchMode ? "Close search" : "Search navigation"}
                className={isSearchMode ? "text-primary" : ""}
              >
                {isSearchMode ? <X className="h-4 w-4" /> : <Search className="h-4 w-4" />}
              </Button>
            </div>
          </div>
          
          {isSearchMode && (
            <div className="mt-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
                <input
                  type="text"
                  placeholder="Search navigation..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  aria-label="Search navigation items"
                  className="w-full pl-10 pr-10 h-10 rounded-md border border-input bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  autoFocus
                />
                {searchQuery && (
                  <button
                    type="button"
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    aria-label="Clear search"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          )}
        </SidebarHeader>

        <SidebarContent className="px-2">
          {isSearchMode ? (
            <div className="space-y-4">
              <div className="text-sm text-muted-foreground">
                {filteredNavigationItems.length === 0 
                  ? "No navigation items found"
                  : `Found ${filteredNavigationItems.length} item${filteredNavigationItems.length !== 1 ? 's' : ''}`
                }
              </div>
              
              <SidebarMenu>
                {filteredNavigationItems.map((item) => (
                  <SidebarMenuItem key={item.id}>
                    <SidebarMenuButton
                      onClick={() => handleNavigationItemClick(item)}
                      isActive={activeView === item.id}
                      className="w-full"
                      aria-label={item.description}
                      tooltip={item.description}
                    >
                      <span className="mr-3" aria-hidden="true">{item.icon}</span>
                      <span className="flex-1">{item.label}</span>
                      {item.badge && (
                        <Badge variant="secondary" className="ml-auto">
                          {item.badge}
                        </Badge>
                      )}
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </div>
          ) : (
            <>
              {/* Main Navigation */}
              <SidebarGroup>
                <SidebarGroupLabel>Main</SidebarGroupLabel>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {mainNavigationItems.map((item) => (
                      <SidebarMenuItem key={item.id}>
                        <SidebarMenuButton
                          onClick={() => handleNavigationItemClick(item)}
                          isActive={activeView === item.id}
                          className="w-full"
                          aria-label={item.description}
                          tooltip={item.description}
                          disabled={item.disabled}
                        >
                          <span className="mr-3" aria-hidden="true">{item.icon}</span>
                          <span className="flex-1">{item.label}</span>
                          {item.badge && (
                            <Badge variant="secondary" className="ml-auto">
                              {item.badge}
                            </Badge>
                          )}
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenu>
                </SidebarGroupContent>
              </SidebarGroup>

              <Separator className="my-2" />

              {/* Plugin Navigation */}
              <SidebarGroup>
                <SidebarGroupLabel>Plugins</SidebarGroupLabel>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {pluginNavigationItems.map((item) => (
                      <SidebarMenuItem key={item.id}>
                        <SidebarMenuButton
                          onClick={() => handleNavigationItemClick(item)}
                          isActive={activeView === item.id}
                          className="w-full"
                          aria-label={item.description}
                          tooltip={item.description}
                          disabled={item.disabled}
                        >
                          <span className="mr-3" aria-hidden="true">{item.icon}</span>
                          <span className="flex-1">{item.label}</span>
                          {item.badge && (
                            <Badge variant="secondary" className="ml-auto">
                              {item.badge}
                            </Badge>
                          )}
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenu>
                </SidebarGroupContent>
              </SidebarGroup>
            </>
          )}
        </SidebarContent>

        <SidebarFooter className="p-2 border-t">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Karen AI Menu</span>
            {isSearchMode && (
              <span>{filteredNavigationItems.length} items</span>
            )}
          </div>
        </SidebarFooter>
      </Sidebar>
    </UiSidebarProvider>
  );
};

export default UnifiedNavigation;