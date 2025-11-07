"use client";

import React, { useState } from "react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

import {
  Search,
  Download,
  Eye,
  RefreshCw,
  SortAsc,
  SortDesc,
  Grid,
  List,
  Package,
  Star,
  Award,
  CheckCircle,
  ArrowLeft,
  Heart,
  Share,
  ExternalLink,
} from "lucide-react";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import { PluginMarketplaceEntry } from "@/types/plugins";

/**
 * Plugin Marketplace Component
 *
 * Browse and install plugins from the marketplace with search, ratings, and installation.
 * Based on requirements: 5.3, 5.5, 9.1, 9.2, 9.4
 */

export interface PluginMarketplaceProps {
  onClose: () => void;
  onInstall: (plugin: PluginMarketplaceEntry) => void;
}

// Mock marketplace data
const mockMarketplacePlugins: PluginMarketplaceEntry[] = [
  {
    id: "slack-integration",
    name: "Slack Integration",
    description:
      "Connect with Slack workspaces and manage messages through AI chat interface",
    version: "1.0.0",
    author: { name: "Kari AI Team", verified: true },
    category: "integration",
    tags: ["slack", "messaging", "team", "communication"],
    downloads: 1250,
    rating: 4.5,
    reviewCount: 23,
    featured: true,
    verified: true,
    compatibility: {
      minVersion: "1.0.0",
      platforms: ["node"],
    },
    screenshots: [],
    pricing: { type: "free" },
    installUrl: "https://marketplace.kari.ai/plugins/slack-integration",
    manifest: {
      id: "slack-integration",
      name: "Slack Integration",
      version: "1.0.0",
      description:
        "Connect with Slack workspaces and manage messages through AI chat interface",
      author: { name: "Kari AI Team", email: "plugins@kari.ai" },
      license: "MIT",
      homepage: "https://docs.kari.ai/plugins/slack",
      repository: "https://github.com/kari-ai/slack-plugin",
      keywords: ["slack", "messaging", "team"],
      category: "integration",
      runtime: { platform: ["node"], nodeVersion: ">=16.0.0" },
      dependencies: [],
      systemRequirements: {},
      permissions: [],
      sandboxed: true,
      securityPolicy: {
        allowNetworkAccess: true,
        allowFileSystemAccess: false,
        allowSystemCalls: false,
      },
      configSchema: [],
      apiVersion: "1.0",
    },
  },
  {
    id: "database-connector",
    name: "Database Connector",
    description:
      "Connect to various databases and execute queries through natural language",
    version: "2.1.0",
    author: { name: "Community Developer", verified: false },
    category: "integration",
    tags: ["database", "sql", "query", "data"],
    downloads: 890,
    rating: 4.2,
    reviewCount: 15,
    featured: false,
    verified: false,
    compatibility: {
      minVersion: "1.0.0",
      platforms: ["node"],
    },
    screenshots: [],
    pricing: { type: "free" },
    installUrl: "https://marketplace.kari.ai/plugins/database-connector",
    manifest: {
      id: "database-connector",
      name: "Database Connector",
      version: "2.1.0",
      description:
        "Connect to various databases and execute queries through natural language",
      author: { name: "Community Developer" },
      license: "Apache-2.0",
      keywords: ["database", "sql", "query"],
      category: "integration",
      runtime: { platform: ["node"], nodeVersion: ">=14.0.0" },
      dependencies: [],
      systemRequirements: {},
      permissions: [],
      sandboxed: false,
      securityPolicy: {
        allowNetworkAccess: true,
        allowFileSystemAccess: true,
        allowSystemCalls: false,
      },
      configSchema: [],
      apiVersion: "1.0",
    },
  },
  {
    id: "weather-service",
    name: "Weather Service",
    description:
      "Get current weather information and forecasts for any location",
    version: "1.3.0",
    author: { name: "Weather Corp", verified: true },
    category: "utility",
    tags: ["weather", "forecast", "location", "api"],
    downloads: 2150,
    rating: 4.8,
    reviewCount: 45,
    featured: true,
    verified: true,
    compatibility: {
      minVersion: "1.0.0",
      platforms: ["node"],
    },
    screenshots: [],
    pricing: { type: "freemium", price: 9.99, currency: "USD" },
    installUrl: "https://marketplace.kari.ai/plugins/weather-service",
    manifest: {
      id: "weather-service",
      name: "Weather Service",
      version: "1.3.0",
      description:
        "Get current weather information and forecasts for any location",
      author: { name: "Weather Corp" },
      license: "Commercial",
      keywords: ["weather", "forecast"],
      category: "utility",
      runtime: { platform: ["node"] },
      dependencies: [],
      systemRequirements: {},
      permissions: [],
      sandboxed: true,
      securityPolicy: {
        allowNetworkAccess: true,
        allowFileSystemAccess: false,
        allowSystemCalls: false,
      },
      configSchema: [],
      apiVersion: "1.0",
    },
  },
  {
    id: "email-automation",
    name: "Email Automation",
    description:
      "Automate email workflows with AI-powered responses and scheduling",
    version: "1.1.0",
    author: { name: "AutoMail Inc", verified: true },
    category: "automation",
    tags: ["email", "automation", "scheduling", "ai"],
    downloads: 567,
    rating: 4.3,
    reviewCount: 12,
    featured: false,
    verified: true,
    compatibility: {
      minVersion: "1.0.0",
      platforms: ["node"],
    },
    screenshots: [],
    pricing: { type: "paid", price: 19.99, currency: "USD" },
    installUrl: "https://marketplace.kari.ai/plugins/email-automation",
    manifest: {
      id: "email-automation",
      name: "Email Automation",
      version: "1.1.0",
      description:
        "Automate email workflows with AI-powered responses and scheduling",
      author: { name: "AutoMail Inc" },
      license: "Commercial",
      keywords: ["email", "automation"],
      category: "workflow",
      runtime: { platform: ["node"] },
      dependencies: [],
      systemRequirements: {},
      permissions: [],
      sandboxed: true,
      securityPolicy: {
        allowNetworkAccess: true,
        allowFileSystemAccess: false,
        allowSystemCalls: false,
      },
      configSchema: [],
      apiVersion: "1.0",
    },
  },
];

export const PluginMarketplace: React.FC<PluginMarketplaceProps> = ({
  onClose,
  onInstall,
}) => {
  const [plugins] = useState<PluginMarketplaceEntry[]>(mockMarketplacePlugins);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"popular" | "rating" | "recent" | "name">(
    "popular"
  );
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [selectedPlugin, setSelectedPlugin] =
    useState<PluginMarketplaceEntry | null>(null);
  const [showOnlyFree, setShowOnlyFree] = useState(false);
  const [showOnlyVerified, setShowOnlyVerified] = useState(false);

  const categories = React.useMemo(() => {
    const cats = Array.from(new Set(plugins.map((p) => p.category)));
    return ["all", ...cats.sort()];
  }, [plugins]);

  const filteredPlugins = React.useMemo(() => {
    let filtered = [...plugins];

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (plugin) =>
          plugin.name.toLowerCase().includes(query) ||
          plugin.description.toLowerCase().includes(query) ||
          plugin.tags.some((tag) => tag.toLowerCase().includes(query)) ||
          plugin.author.name.toLowerCase().includes(query)
      );
    }

    if (selectedCategory !== "all") {
      filtered = filtered.filter(
        (plugin) => plugin.category === selectedCategory
      );
    }

    if (showOnlyFree) {
      filtered = filtered.filter(
        (plugin) => plugin.pricing.type === "free"
      );
    }

    if (showOnlyVerified) {
      filtered = filtered.filter((plugin) => plugin.verified);
    }

    filtered.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortBy) {
        case "popular":
          aValue = a.downloads;
          bValue = b.downloads;
          break;
        case "rating":
          aValue = a.rating;
          bValue = b.rating;
          break;
        case "recent":
          aValue = a.version;
          bValue = b.version;
          break;
        case "name":
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        default:
          return 0;
      }

      if (sortOrder === "asc") {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      }
      return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
    });

    return filtered;
  }, [
    plugins,
    searchQuery,
    selectedCategory,
    sortBy,
    sortOrder,
    showOnlyFree,
    showOnlyVerified,
  ]);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      // Hook real marketplace API here when wired.
    } finally {
      setLoading(false);
    }
  };

  const handleInstall = (plugin: PluginMarketplaceEntry) => {
    onInstall(plugin);
    onClose();
  };

  const renderStars = (rating: number) =>
    Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`w-3 h-3 ${
          i < Math.floor(rating)
            ? "text-yellow-500 fill-current"
            : i < rating
            ? "text-yellow-500 fill-current opacity-50"
            : "text-gray-300"
        }`}
      />
    ));

  const renderPluginCard = (plugin: PluginMarketplaceEntry) => (
    <Card
      key={plugin.id}
      className="hover:shadow-md transition-shadow cursor-pointer"
    >
      <CardContent className="p-4 sm:p-4 md:p-6">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-semibold text-lg">{plugin.name}</h3>
              {plugin.verified && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <CheckCircle className="w-4 h-4 text-blue-600" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Verified plugin</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
              {plugin.featured && (
                <Badge
                  variant="default"
                  className="text-xs sm:text-sm md:text-base flex items-center gap-1"
                >
                  <Award className="w-3 h-3" />
                  Featured
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground mb-2 line-clamp-2 md:text-base lg:text-lg">
              {plugin.description}
            </p>
            <div className="flex items-center gap-2 mb-2">
              <div className="flex items-center gap-1">
                {renderStars(plugin.rating)}
                <span className="text-xs text-muted-foreground ml-1 sm:text-sm md:text-base">
                  {plugin.rating} ({plugin.reviewCount})
                </span>
              </div>
              <Separator orientation="vertical" className="h-4" />
              <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                {plugin.downloads.toLocaleString()} downloads
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className="text-xs sm:text-sm md:text-base"
            >
              {plugin.category}
            </Badge>
            <Badge
              variant={
                plugin.pricing.type === "free" ? "secondary" : "default"
              }
              className="text-xs sm:text-sm md:text-base"
            >
              {plugin.pricing.type === "free"
                ? "Free"
                : plugin.pricing.type === "freemium"
                ? "Freemium"
                : `$${plugin.pricing.price}`}
            </Badge>
          </div>

          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                setSelectedPlugin(plugin);
              }}
            >
              <Eye className="w-3 h-3" />
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                handleInstall(plugin);
              }}
            >
              <Download className="w-3 h-3 mr-1" />
              Install
            </Button>
          </div>
        </div>

        <div className="flex items-center gap-1 mt-3">
          {plugin.tags.slice(0, 3).map((tag) => (
            <Badge
              key={tag}
              variant="outline"
              className="text-xs sm:text-sm md:text-base"
            >
              {tag}
            </Badge>
          ))}
          {plugin.tags.length > 3 && (
            <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
              +{plugin.tags.length - 3} more
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );

  const renderPluginList = (plugin: PluginMarketplaceEntry) => (
    <Card
      key={plugin.id}
      className="hover:shadow-sm transition-shadow cursor-pointer"
    >
      <CardContent className="p-4 sm:p-4 md:p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 flex-1">
            <div className="w-12 h-12 bg-muted rounded-lg flex items-center justify-center">
              <Package className="w-6 h-6 text-muted-foreground" />
            </div>

            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-semibold">{plugin.name}</h3>
                <Badge
                  variant="outline"
                  className="text-xs sm:text-sm md:text-base"
                >
                  v{plugin.version}
                </Badge>
                {plugin.verified && (
                  <CheckCircle className="w-4 h-4 text-blue-600" />
                )}
                {plugin.featured && (
                  <Badge
                    variant="default"
                    className="text-xs sm:text-sm md:text-base"
                  >
                    Featured
                  </Badge>
                )}
              </div>
              <p className="text-sm text-muted-foreground mb-2 md:text-base lg:text-lg">
                {plugin.description}
              </p>
              <div className="flex items-center gap-4 text-xs text-muted-foreground sm:text-sm md:text-base">
                <div className="flex items-center gap-1">
                  {renderStars(plugin.rating)}
                  <span className="ml-1">{plugin.rating}</span>
                </div>
                <span>{plugin.downloads.toLocaleString()} downloads</span>
                <span>by {plugin.author.name}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge
              variant={
                plugin.pricing.type === "free" ? "secondary" : "default"
              }
              className="text-xs sm:text-sm md:text-base"
            >
              {plugin.pricing.type === "free"
                ? "Free"
                : plugin.pricing.type === "freemium"
                ? "Freemium"
                : `$${plugin.pricing.price}`}
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                setSelectedPlugin(plugin);
              }}
            >
              <Eye className="w-4 h-4" />
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                handleInstall(plugin);
              }}
            >
              <Download className="w-4 h-4 mr-2" />
              Install
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={onClose}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Plugin Marketplace</h1>
          <p className="text-muted-foreground">
            Discover and install plugins to extend Kari AI.
          </p>
        </div>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex-1 max-w-md">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search plugins..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Select
                value={selectedCategory}
                onValueChange={setSelectedCategory}
              >
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="All Categories" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((category) => (
                    <SelectItem key={category} value={category}>
                      {category === "all"
                        ? "All Categories"
                        : category.charAt(0).toUpperCase() +
                          category.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={sortBy}
                onValueChange={(value) =>
                  setSortBy(
                    value as "popular" | "rating" | "recent" | "name"
                  )
                }
              >
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="popular">Popular</SelectItem>
                  <SelectItem value="rating">Rating</SelectItem>
                  <SelectItem value="recent">Recent</SelectItem>
                  <SelectItem value="name">Name</SelectItem>
                </SelectContent>
              </Select>

              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setSortOrder(sortOrder === "asc" ? "desc" : "asc")
                }
              >
                {sortOrder === "asc" ? (
                  <SortAsc className="w-4 h-4" />
                ) : (
                  <SortDesc className="w-4 h-4" />
                )}
              </Button>

              <Separator orientation="vertical" className="h-6" />

              <div className="flex items-center border rounded-md overflow-hidden">
                <Button
                  variant={viewMode === "grid" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setViewMode("grid")}
                  className="rounded-r-none"
                >
                  <Grid className="w-4 h-4" />
                </Button>
                <Button
                  variant={viewMode === "list" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setViewMode("list")}
                  className="rounded-l-none"
                >
                  <List className="w-4 h-4" />
                </Button>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={loading}
              >
                <RefreshCw
                  className={`w-4 h-4 ${
                    loading ? "animate-spin" : ""
                  }`}
                />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
            {filteredPlugins.length} plugin
            {filteredPlugins.length !== 1 ? "s" : ""} found
          </p>
        </div>

        {filteredPlugins.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-medium mb-2">
                No plugins found
              </h3>
              <p className="text-muted-foreground">
                Try adjusting your search or filters.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div
            className={
              viewMode === "grid"
                ? "grid gap-4 md:grid-cols-2 lg:grid-cols-3"
                : "space-y-4"
            }
          >
            {filteredPlugins.map((plugin) =>
              viewMode === "grid"
                ? renderPluginCard(plugin)
                : renderPluginList(plugin)
            )}
          </div>
        )}
      </div>

      {/* Plugin Detail Dialog */}
      <Dialog
        open={!!selectedPlugin}
        onOpenChange={(open) => {
          if (!open) setSelectedPlugin(null);
        }}
      >
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          {selectedPlugin && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-muted rounded-lg flex items-center justify-center">
                    <Package className="w-6 h-6 text-muted-foreground" />
                  </div>
                  <div>
                    <DialogTitle className="flex items-center gap-2">
                      {selectedPlugin.name}
                      {selectedPlugin.verified && (
                        <CheckCircle className="w-5 h-5 text-blue-600" />
                      )}
                      {selectedPlugin.featured && (
                        <Badge
                          variant="default"
                          className="text-xs sm:text-sm md:text-base flex items-center gap-1"
                        >
                          <Award className="w-3 h-3" />
                          Featured
                        </Badge>
                      )}
                    </DialogTitle>
                    <DialogDescription>
                      by {selectedPlugin.author.name} • v
                      {selectedPlugin.version}
                    </DialogDescription>
                  </div>
                </div>
              </DialogHeader>

              <div className="space-y-6">
                <div>
                  <p className="text-sm md:text-base lg:text-lg">
                    {selectedPlugin.description}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <h4 className="font-medium text-sm md:text-base lg:text-lg">
                      Rating
                    </h4>
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1">
                        {renderStars(selectedPlugin.rating)}
                      </div>
                      <span className="text-sm md:text-base lg:text-lg">
                        {selectedPlugin.rating} (
                        {selectedPlugin.reviewCount} reviews)
                      </span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="font-medium text-sm md:text-base lg:text-lg">
                      Downloads
                    </h4>
                    <p className="text-sm md:text-base lg:text-lg">
                      {selectedPlugin.downloads.toLocaleString()}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <h4 className="font-medium text-sm md:text-base lg:text-lg">
                      Category
                    </h4>
                    <Badge
                      variant="outline"
                      className="text-xs sm:text-sm md:text-base"
                    >
                      {selectedPlugin.category}
                    </Badge>
                  </div>

                  <div className="space-y-2">
                    <h4 className="font-medium text-sm md:text-base lg:text-lg">
                      Pricing
                    </h4>
                    <Badge
                      variant={
                        selectedPlugin.pricing.type === "free"
                          ? "secondary"
                          : "default"
                      }
                      className="text-xs sm:text-sm md:text-base"
                    >
                      {selectedPlugin.pricing.type === "free"
                        ? "Free"
                        : selectedPlugin.pricing.type === "freemium"
                        ? "Freemium"
                        : `$${selectedPlugin.pricing.price}`}
                    </Badge>
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="font-medium text-sm md:text-base lg:text-lg">
                    Tags
                  </h4>
                  <div className="flex flex-wrap gap-1">
                    {selectedPlugin.tags.map((tag) => (
                      <Badge
                        key={tag}
                        variant="outline"
                        className="text-xs sm:text-sm md:text-base"
                      >
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="font-medium text-sm md:text-base lg:text-lg">
                    Compatibility
                  </h4>
                  <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                    <p>
                      Minimum version:{" "}
                      {selectedPlugin.compatibility.minVersion}
                    </p>
                    <p>
                      Platforms:{" "}
                      {selectedPlugin.compatibility.platforms.join(", ")}
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4 border-t">
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      <Heart className="w-4 h-4 mr-2" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <Share className="w-4 h-4 mr-2" />
                    </Button>
                    {selectedPlugin.manifest.homepage && (
                      <Button variant="outline" size="sm" asChild>
                        <a
                          href={selectedPlugin.manifest.homepage}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <ExternalLink className="w-4 h-4 mr-2" />
                          Docs
                        </a>
                      </Button>
                    )}
                  </div>

                  <Button
                    variant="default"
                    onClick={() => handleInstall(selectedPlugin)}
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Install Plugin
                  </Button>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PluginMarketplace;
