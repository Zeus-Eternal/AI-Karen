"use client";

/**
 * @file PluginStorePage.tsx
 * @description Main page for browsing and managing plugins from the plugin store.
 * Integrates with the plugin store API to discover, install, and manage plugins.
 */

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PlugZap, Package, TrendingUp, Star, AlertTriangle, RefreshCw, Loader2 } from 'lucide-react';
import { usePluginStore } from '@/stores/PluginStore';
import { PluginGrid } from './PluginGrid';
import { SearchBar } from './SearchBar';
import { CategoryFilter } from './CategoryFilter';

export default function PluginStorePage() {
  const {
    plugins,
    loading,
    error,
    searchParams,
    searchResponse,
    categories,
    trendingPlugins,
    installingPlugins,
    setSearchParams,
    searchPlugins,
    refreshPlugins,
    installPlugin,
    loadCategories,
    loadTrending,
    getPluginDetails,
    clearError,
  } = usePluginStore();

  const [selectedCategory, setSelectedCategory] = useState(searchParams.category);

  useEffect(() => {
    loadCategories();
    loadTrending();
    searchPlugins();
  }, [loadCategories, loadTrending, searchPlugins]);

  useEffect(() => {
    setSearchParams({ category: selectedCategory });
  }, [selectedCategory, setSearchParams]);

  const handleSearch = (params: typeof searchParams) => {
    setSearchParams(params);
    searchPlugins();
  };

  const handleInstall = async (pluginId: string, version?: string) => {
    try {
      await installPlugin(pluginId, version);
    } catch (error) {
      console.error('Failed to install plugin:', error);
    }
  };

  const handleDetails = (pluginId: string) => {
    getPluginDetails(pluginId);
  };

  const handleDiscover = (pluginId: string) => {
    console.log('Discover plugin:', pluginId);
  };

  const handleCategoryChange = (category: typeof selectedCategory) => {
    setSelectedCategory(category);
  };

  const handlePageChange = (page: number) => {
    setSearchParams({ page });
    searchPlugins();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <PlugZap className="h-8 w-8 text-primary" />
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">Plugin Store</h2>
            <p className="text-sm text-muted-foreground">
              Discover and install plugins to enhance Karen AI capabilities
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refreshPlugins()}
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription className="flex items-center justify-between">
            <span>{error}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearError}
              className="h-6"
            >
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="browse" className="w-full">
        <TabsList className="grid w-full grid-cols-3 lg:w-[400px]">
          <TabsTrigger value="browse">
            <Package className="h-4 w-4 mr-2" />
            Browse
          </TabsTrigger>
          <TabsTrigger value="trending">
            <TrendingUp className="h-4 w-4 mr-2" />
            Trending
          </TabsTrigger>
          <TabsTrigger value="installed">
            <Star className="h-4 w-4 mr-2" />
            Installed
          </TabsTrigger>
        </TabsList>

        <TabsContent value="browse" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Discover Plugins</CardTitle>
              <CardDescription>
                Browse the marketplace and install plugins to extend Karen AI&apos;s capabilities
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col lg:flex-row gap-4">
                <div className="flex-1">
                  <SearchBar
                    params={searchParams}
                    onSearch={handleSearch}
                    placeholder="Search for plugins..."
                  />
                </div>
              </div>

              {categories.length > 0 && (
                <CategoryFilter
                  categories={categories}
                  selectedCategory={selectedCategory}
                  onCategoryChange={handleCategoryChange}
                />
              )}

              <PluginGrid
                plugins={plugins}
                loading={loading}
                total={searchResponse?.total}
                page={searchParams.page}
                perPage={searchParams.per_page}
                totalPages={searchResponse?.total_pages}
                hasNext={searchResponse?.has_next}
                hasPrev={searchParams.page > 1}
                onPageChange={handlePageChange}
                onInstall={handleInstall}
                onDetails={handleDetails}
                onDiscover={handleDiscover}
                installingPlugins={installingPlugins}
                emptyMessage={
                  selectedCategory
                    ? `No plugins found in ${categories.find(c => c.name === selectedCategory)?.display_name || selectedCategory}`
                    : 'No plugins found. Try adjusting your search or filters.'
                }
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trending" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Trending Plugins</CardTitle>
              <CardDescription>
                Popular plugins that are being installed by the community
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading && trendingPlugins.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
                  <p className="text-sm text-muted-foreground">Loading trending plugins...</p>
                </div>
              ) : trendingPlugins.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <TrendingUp className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-sm text-muted-foreground">No trending plugins available yet</p>
                </div>
              ) : (
                <PluginGrid
                  plugins={trendingPlugins}
                  loading={loading}
                  onInstall={handleInstall}
                  onDetails={handleDetails}
                  onDiscover={handleDiscover}
                  installingPlugins={installingPlugins}
                  emptyMessage="No trending plugins found"
                />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="installed" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Installed Plugins</CardTitle>
              <CardDescription>
                Manage plugins that are currently installed on your system
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
                  <p className="text-sm text-muted-foreground">Loading installed plugins...</p>
                </div>
              ) : plugins.filter(p => p.status === 'installed').length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Package className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-sm text-muted-foreground mb-2">No plugins installed yet</p>
                  <Button variant="outline" onClick={() => searchPlugins()}>
                    Browse Plugin Store
                  </Button>
                </div>
              ) : (
                <PluginGrid
                  plugins={plugins.filter(p => p.status === 'installed')}
                  loading={loading}
                  onDetails={handleDetails}
                  installingPlugins={installingPlugins}
                  emptyMessage="No installed plugins found"
                />
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
