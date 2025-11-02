/**
 * Enhanced Plugin Marketplace Component
 *
 * Advanced marketplace with search, ratings, reviews, and installation from remote sources.
 * Based on requirements: 5.3, 5.5, 9.1, 9.2, 9.4
 */

"use client";

import React, { useState, useEffect } from "react";
import {
  Search,
  Filter,
  Star,
  Download,
  Eye,
  Share,
  ArrowLeft,
  CheckCircle,
  Award,
  Package,
  ExternalLink,
  Grid,
  List,
  SortAsc,
  SortDesc,
  BookmarkCheck,
  ShoppingCart,
  MessageSquare,
  ThumbsUp,
  Flag,
  Bookmark,
  ImageIcon,
} from "lucide-react";

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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

import { PluginMarketplaceEntry } from "@/types/plugins";

interface PluginReview {
  id: string;
  pluginId: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  rating: number;
  title: string;
  content: string;
  timestamp: Date;
  helpful: number;
  verified: boolean;
  version: string;
}

interface MarketplaceFilters {
  category: string[];
  pricing: string[];
  rating: number;
  verified: boolean;
  featured: boolean;
  compatibility: string[];
  tags: string[];
}

interface EnhancedPluginMarketplaceProps {
  onClose: () => void;
  onInstall: (plugin: PluginMarketplaceEntry) => void;
  onPurchase?: (plugin: PluginMarketplaceEntry) => void;
}

// Mock enhanced marketplace data
const mockEnhancedPlugins: PluginMarketplaceEntry[] = [
  {
    id: "slack-integration-pro",
    name: "Slack Integration Pro",
    description:
      "Advanced Slack integration with AI-powered message analysis, sentiment tracking, and automated responses. Includes team productivity insights and custom workflow automation.",
    version: "2.1.0",
    author: { name: "Kari AI Team", verified: true },
    category: "integration",
    tags: ["slack", "messaging", "ai", "automation", "analytics"],
    downloads: 5420,
    rating: 4.8,
    reviewCount: 89,
    featured: true,
    verified: true,
    compatibility: {
      minVersion: "1.0.0",
      platforms: ["node"],
    },
    screenshots: [
      "/screenshots/slack-pro-1.png",
      "/screenshots/slack-pro-2.png",
      "/screenshots/slack-pro-3.png",
    ],
    pricing: { type: "paid", price: 29.99, currency: "USD" },
    installUrl: "https://marketplace.kari.ai/plugins/slack-integration-pro",
    manifest: {
      id: "slack-integration-pro",
      name: "Slack Integration Pro",
      version: "2.1.0",
      description: "Advanced Slack integration with AI-powered features",
      author: { name: "Kari AI Team", email: "plugins@kari.ai" },
      license: "Commercial",
      homepage: "https://docs.kari.ai/plugins/slack-pro",
      repository: "https://github.com/kari-ai/slack-pro-plugin",
      keywords: ["slack", "messaging", "ai"],
      category: "integration",
      runtime: { platform: ["node"], nodeVersion: ">=16.0.0" },
      dependencies: [],
      systemRequirements: {
        minMemory: 128,
        minDisk: 50,
      },
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
    id: "ai-content-generator",
    name: "AI Content Generator",
    description:
      "Generate high-quality content using advanced AI models. Create blog posts, social media content, marketing copy, and more with customizable templates and brand voice.",
    version: "1.5.2",
    author: { name: "ContentAI Inc", verified: true },
    category: "ai",
    tags: ["content", "ai", "writing", "marketing", "seo"],
    downloads: 3210,
    rating: 4.6,
    reviewCount: 67,
    featured: true,
    verified: true,
    compatibility: {
      minVersion: "1.0.0",
      platforms: ["node"],
    },
    screenshots: [
      "/screenshots/content-gen-1.png",
      "/screenshots/content-gen-2.png",
    ],
    pricing: { type: "freemium", price: 19.99, currency: "USD" },
    installUrl: "https://marketplace.kari.ai/plugins/ai-content-generator",
    manifest: {
      id: "ai-content-generator",
      name: "AI Content Generator",
      version: "1.5.2",
      description: "Generate high-quality content using advanced AI models",
      author: { name: "ContentAI Inc" },
      license: "Commercial",
      keywords: ["content", "ai", "writing"],
      category: "ai",
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

const mockReviews: PluginReview[] = [
  {
    id: "review-1",
    pluginId: "slack-integration-pro",
    userId: "user-1",
    userName: "Sarah Johnson",
    userAvatar: "/avatars/sarah.jpg",
    rating: 5,
    title: "Excellent plugin with great AI features",
    content:
      "This plugin has transformed how our team uses Slack. The AI-powered message analysis is incredibly accurate and the automated responses save us hours every week. The sentiment tracking helps us understand team morale better.",
    timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
    helpful: 12,
    verified: true,
    version: "2.1.0",
  },
  {
    id: "review-2",
    pluginId: "slack-integration-pro",
    userId: "user-2",
    userName: "Mike Chen",
    rating: 4,
    title: "Good plugin but could use more customization",
    content:
      "Works well overall and the integration is smooth. Would love to see more customization options for the automated responses. The analytics dashboard is very helpful for tracking team productivity.",
    timestamp: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000),
    helpful: 8,
    verified: false,
    version: "2.0.1",
  },
  {
    id: "review-3",
    pluginId: "ai-content-generator",
    userId: "user-3",
    userName: "Emily Rodriguez",
    rating: 5,
    title: "Amazing content quality",
    content:
      "The AI-generated content is surprisingly good. I use it for blog posts and social media content. The templates are well-designed and the brand voice customization works perfectly.",
    timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
    helpful: 15,
    verified: true,
    version: "1.5.2",
  },
];

export const EnhancedPluginMarketplace: React.FC<
  EnhancedPluginMarketplaceProps
> = ({ onClose, onInstall, onPurchase }) => {
  const [plugins, setPlugins] =
    useState<PluginMarketplaceEntry[]>(mockEnhancedPlugins);
  const [reviews, setReviews] = useState<PluginReview[]>(mockReviews);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPlugin, setSelectedPlugin] =
    useState<PluginMarketplaceEntry | null>(null);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [sortBy, setSortBy] = useState<
    "popular" | "rating" | "recent" | "name" | "price"
  >("popular");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [showFilters, setShowFilters] = useState(false);
  const [bookmarkedPlugins, setBookmarkedPlugins] = useState<Set<string>>(
    new Set()
  );

  const [filters, setFilters] = useState<MarketplaceFilters>({
    category: [],
    pricing: [],
    rating: 0,
    verified: false,
    featured: false,
    compatibility: [],
    tags: [],
  });

  // Get unique values for filters
  const filterOptions = React.useMemo(() => {
    const categories = Array.from(new Set(plugins.map((p) => p.category)));
    const pricingTypes = Array.from(
      new Set(plugins.map((p) => p.pricing.type))
    );
    const allTags = Array.from(new Set(plugins.flatMap((p) => p.tags)));
    const platforms = Array.from(
      new Set(plugins.flatMap((p) => p.compatibility.platforms))
    );

    return { categories, pricingTypes, allTags, platforms };
  }, [plugins]);

  // Filter and sort plugins
  const filteredPlugins = React.useMemo(() => {
    let filtered = plugins;

    // Search filter
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

    // Category filter
    if (filters.category.length > 0) {
      filtered = filtered.filter((plugin) =>
        filters.category.includes(plugin.category)
      );
    }

    // Pricing filter
    if (filters.pricing.length > 0) {
      filtered = filtered.filter((plugin) =>
        filters.pricing.includes(plugin.pricing.type)
      );
    }

    // Rating filter
    if (filters.rating > 0) {
      filtered = filtered.filter((plugin) => plugin.rating >= filters.rating);
    }

    // Verified filter
    if (filters.verified) {
      filtered = filtered.filter((plugin) => plugin.verified);
    }

    // Featured filter
    if (filters.featured) {
      filtered = filtered.filter((plugin) => plugin.featured);
    }

    // Tags filter
    if (filters.tags.length > 0) {
      filtered = filtered.filter((plugin) =>
        filters.tags.some((tag) => plugin.tags.includes(tag))
      );
    }

    // Sort
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;

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
        case "price":
          aValue = a.pricing.price || 0;
          bValue = b.pricing.price || 0;
          break;
        default:
          return 0;
      }

      if (sortOrder === "asc") {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });

    return filtered;
  }, [plugins, searchQuery, filters, sortBy, sortOrder]);

  const handleInstall = (plugin: PluginMarketplaceEntry) => {
    if (plugin.pricing.type === "paid" && onPurchase) {
      onPurchase(plugin);
    } else {
      onInstall(plugin);
    }
    onClose();
  };

  const toggleBookmark = (pluginId: string) => {
    setBookmarkedPlugins((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(pluginId)) {
        newSet.delete(pluginId);
      } else {
        newSet.add(pluginId);
      }
      return newSet;
    });
  };

  const renderStars = (rating: number, size: "sm" | "md" = "sm") => {
    const starSize = size === "sm" ? "w-3 h-3" : "w-4 h-4";
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`${starSize} ${
          i < Math.floor(rating)
            ? "text-yellow-500 fill-current"
            : i < rating
            ? "text-yellow-500 fill-current opacity-50"
            : "text-gray-300"
        }`}
      />
    ));
  };

  const renderPluginCard = (plugin: PluginMarketplaceEntry) => {
    const isBookmarked = bookmarkedPlugins.has(plugin.id);

    return (
      <Card
        key={plugin.id}
        className="hover:shadow-lg transition-all duration-200 group"
      >
        <CardContent className="p-0">
          {/* Plugin Image/Icon */}
          <div className="relative h-48 bg-gradient-to-br from-blue-500 to-purple-600 rounded-t-lg">
            <div className="absolute inset-0 flex items-center justify-center">
              <Package className="w-16 h-16 text-white opacity-80" />
            </div>
            <div className="absolute top-3 right-3 flex gap-2">
              {plugin.featured && (
                <Badge variant="default" className="text-xs">
                  <Award className="w-3 h-3 mr-1" />
                  Featured
                </Badge>
              )}
              {plugin.verified && (
                <Badge variant="secondary" className="text-xs">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Verified
                </Badge>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="absolute top-3 left-3 text-white hover:bg-white/20"
              onClick={(e) => {
                e.stopPropagation();
                toggleBookmark(plugin.id);
              }}
            >
              {isBookmarked ? (
                <BookmarkCheck className="w-4 h-4" />
              ) : (
                <Bookmark className="w-4 h-4" />
              )}
            </Button>
          </div>

          <div className="p-4">
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <h3 className="font-semibold text-lg line-clamp-1">
                  {plugin.name}
                </h3>
                <p className="text-sm text-muted-foreground">
                  by {plugin.author.name}
                </p>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-1 mb-1">
                  {renderStars(plugin.rating)}
                  <span className="text-xs text-muted-foreground ml-1">
                    {plugin.rating}
                  </span>
                </div>
                <div className="text-xs text-muted-foreground">
                  {plugin.reviewCount} reviews
                </div>
              </div>
            </div>

            <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
              {plugin.description}
            </p>

            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  {plugin.category}
                </Badge>
                <Badge
                  variant={
                    plugin.pricing.type === "free" ? "secondary" : "default"
                  }
                  className="text-xs"
                >
                  {plugin.pricing.type === "free"
                    ? "Free"
                    : plugin.pricing.type === "freemium"
                    ? "Freemium"
                    : `$${plugin.pricing.price}`}
                </Badge>
              </div>
              <div className="text-xs text-muted-foreground">
                {plugin.downloads.toLocaleString()} downloads
              </div>
            </div>

            <div className="flex items-center gap-1 mb-4">
              {plugin.tags.slice(0, 3).map((tag) => (
                <Badge key={tag} variant="outline" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {plugin.tags.length > 3 && (
                <span className="text-xs text-muted-foreground">
                  +{plugin.tags.length - 3}
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedPlugin(plugin);
                }}
              >
                <Eye className="w-3 h-3 mr-1" />
                Details
              </Button>
              <Button
                size="sm"
                className="flex-1"
                onClick={(e) => {
                  e.stopPropagation();
                  handleInstall(plugin);
                }}
              >
                {plugin.pricing.type === "paid" ? (
                  <>
                    <ShoppingCart className="w-3 h-3 mr-1" />
                    Buy
                  </>
                ) : (
                  <>
                    <Download className="w-3 h-3 mr-1" />
                    Install
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderPluginReviews = (pluginId: string) => {
    const pluginReviews = reviews.filter((r) => r.pluginId === pluginId);

    if (pluginReviews.length === 0) {
      return (
        <div className="text-center py-8">
          <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <h3 className="text-lg font-medium mb-2">No Reviews Yet</h3>
          <p className="text-muted-foreground">
            Be the first to review this plugin
          </p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {pluginReviews.map((review) => (
          <Card key={review.id}>
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <Avatar className="w-10 h-10">
                  <AvatarImage src={review.userAvatar} />
                  <AvatarFallback>
                    {review.userName
                      .split(" ")
                      .map((n) => n[0])
                      .join("")}
                  </AvatarFallback>
                </Avatar>

                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{review.userName}</span>
                        {review.verified && (
                          <Badge variant="outline" className="text-xs">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Verified
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <div className="flex items-center gap-1">
                          {renderStars(review.rating)}
                        </div>
                        <span className="text-xs text-muted-foreground">
                          v{review.version}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {review.timestamp.toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <h4 className="font-medium mb-2">{review.title}</h4>
                  <p className="text-sm text-muted-foreground mb-3">
                    {review.content}
                  </p>

                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="sm" className="text-xs">
                      <ThumbsUp className="w-3 h-3 mr-1" />
                      Helpful ({review.helpful})
                    </Button>
                    <Button variant="ghost" size="sm" className="text-xs">
                      <Flag className="w-3 h-3 mr-1" />
                      Report
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={onClose}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Plugins
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Plugin Marketplace</h1>
          <p className="text-muted-foreground">
            Discover and install plugins to extend Kari AI
          </p>
        </div>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4">
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search plugins..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button
                variant="outline"
                onClick={() => setShowFilters(!showFilters)}
              >
                <Filter className="w-4 h-4 mr-2" />
                Filters
              </Button>
            </div>

            {showFilters && (
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 p-4 bg-muted/50 rounded-lg">
                <div>
                  <Label className="text-sm font-medium mb-2 block">
                    Category
                  </Label>
                  <div className="space-y-2">
                    {filterOptions.categories.map((category) => (
                      <div
                        key={category}
                        className="flex items-center space-x-2"
                      >
                        <Checkbox
                          id={`category-${category}`}
                          checked={filters.category.includes(category)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setFilters((prev) => ({
                                ...prev,
                                category: [...prev.category, category],
                              }));
                            } else {
                              setFilters((prev) => ({
                                ...prev,
                                category: prev.category.filter(
                                  (c) => c !== category
                                ),
                              }));
                            }
                          }}
                        />
                        <Label
                          htmlFor={`category-${category}`}
                          className="text-sm capitalize"
                        >
                          {category}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <Label className="text-sm font-medium mb-2 block">
                    Pricing
                  </Label>
                  <div className="space-y-2">
                    {filterOptions.pricingTypes.map((type) => (
                      <div key={type} className="flex items-center space-x-2">
                        <Checkbox
                          id={`pricing-${type}`}
                          checked={filters.pricing.includes(type)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setFilters((prev) => ({
                                ...prev,
                                pricing: [...prev.pricing, type],
                              }));
                            } else {
                              setFilters((prev) => ({
                                ...prev,
                                pricing: prev.pricing.filter((p) => p !== type),
                              }));
                            }
                          }}
                        />
                        <Label
                          htmlFor={`pricing-${type}`}
                          className="text-sm capitalize"
                        >
                          {type}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <Label className="text-sm font-medium mb-2 block">
                    Rating
                  </Label>
                  <Select
                    value={filters.rating.toString()}
                    onValueChange={(value) =>
                      setFilters((prev) => ({ ...prev, rating: Number(value) }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Any rating" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="0">Any rating</SelectItem>
                      <SelectItem value="4">4+ stars</SelectItem>
                      <SelectItem value="3">3+ stars</SelectItem>
                      <SelectItem value="2">2+ stars</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className="text-sm font-medium mb-2 block">
                    Options
                  </Label>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="verified"
                        checked={filters.verified}
                        onCheckedChange={(checked) =>
                          setFilters((prev) => ({
                            ...prev,
                            verified: Boolean(checked),
                          }))
                        }
                      />
                      <Label htmlFor="verified" className="text-sm">
                        Verified only
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="featured"
                        checked={filters.featured}
                        onCheckedChange={(checked) =>
                          setFilters((prev) => ({
                            ...prev,
                            featured: Boolean(checked),
                          }))
                        }
                      />
                      <Label htmlFor="featured" className="text-sm">
                        Featured only
                      </Label>
                    </div>
                  </div>
                </div>

                <div>
                  <Label className="text-sm font-medium mb-2 block">Sort</Label>
                  <div className="space-y-2">
                    <Select
                      value={sortBy}
                      onValueChange={(value: any) => setSortBy(value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="popular">Most Popular</SelectItem>
                        <SelectItem value="rating">Highest Rated</SelectItem>
                        <SelectItem value="recent">Most Recent</SelectItem>
                        <SelectItem value="name">Name</SelectItem>
                        <SelectItem value="price">Price</SelectItem>
                      </SelectContent>
                    </Select>
                    <div className="flex gap-1">
                      <Button
                        variant={sortOrder === "desc" ? "default" : "outline"}
                        size="sm"
                        onClick={() => setSortOrder("desc")}
                      >
                        <SortDesc className="w-3 h-3" />
                      </Button>
                      <Button
                        variant={sortOrder === "asc" ? "default" : "outline"}
                        size="sm"
                        onClick={() => setSortOrder("asc")}
                      >
                        <SortAsc className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {filteredPlugins.length} plugin
                {filteredPlugins.length !== 1 ? "s" : ""} found
              </p>

              <div className="flex items-center gap-2">
                <div className="flex items-center border rounded-md">
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
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {filteredPlugins.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-medium mb-2">No plugins found</h3>
            <p className="text-muted-foreground">
              Try adjusting your search or filters
            </p>
          </CardContent>
        </Card>
      ) : (
        <div
          className={
            viewMode === "grid"
              ? "grid gap-6 md:grid-cols-2 lg:grid-cols-3"
              : "space-y-4"
          }
        >
          {filteredPlugins.map((plugin) => renderPluginCard(plugin))}
        </div>
      )}

      {/* Plugin Detail Dialog */}
      <Dialog
        open={!!selectedPlugin}
        onOpenChange={() => setSelectedPlugin(null)}
      >
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          {selectedPlugin && (
            <>
              <DialogHeader>
                <div className="flex items-start gap-4">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <Package className="w-8 h-8 text-white" />
                  </div>
                  <div className="flex-1">
                    <DialogTitle className="flex items-center gap-2 text-xl">
                      {selectedPlugin.name}
                      {selectedPlugin.verified && (
                        <CheckCircle className="w-5 h-5 text-blue-600" />
                      )}
                      {selectedPlugin.featured && (
                        <Badge variant="default" className="text-xs">
                          <Award className="w-3 h-3 mr-1" />
                          Featured
                        </Badge>
                      )}
                    </DialogTitle>
                    <DialogDescription className="text-base">
                      by {selectedPlugin.author.name} • v
                      {selectedPlugin.version}
                    </DialogDescription>
                    <div className="flex items-center gap-4 mt-2">
                      <div className="flex items-center gap-1">
                        {renderStars(selectedPlugin.rating, "md")}
                        <span className="ml-1 font-medium">
                          {selectedPlugin.rating}
                        </span>
                        <span className="text-muted-foreground">
                          ({selectedPlugin.reviewCount} reviews)
                        </span>
                      </div>
                      <Badge
                        variant={
                          selectedPlugin.pricing.type === "free"
                            ? "secondary"
                            : "default"
                        }
                      >
                        {selectedPlugin.pricing.type === "free"
                          ? "Free"
                          : selectedPlugin.pricing.type === "freemium"
                          ? "Freemium"
                          : `$${selectedPlugin.pricing.price}`}
                      </Badge>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => toggleBookmark(selectedPlugin.id)}
                    >
                      {bookmarkedPlugins.has(selectedPlugin.id) ? (
                        <BookmarkCheck className="w-4 h-4" />
                      ) : (
                        <Bookmark className="w-4 h-4" />
                      )}
                    </Button>
                    <Button variant="outline" size="sm">
                      <Share className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </DialogHeader>

              <Tabs defaultValue="overview" className="mt-6">
                <TabsList>
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="reviews">
                    Reviews ({selectedPlugin.reviewCount})
                  </TabsTrigger>
                  <TabsTrigger value="details">Details</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-6">
                  <div>
                    <p className="text-sm leading-relaxed">
                      {selectedPlugin.description}
                    </p>
                  </div>

                  {selectedPlugin.screenshots.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-3">Screenshots</h4>
                      <div className="grid grid-cols-2 gap-4">
                        {selectedPlugin.screenshots.map((screenshot, index) => (
                          <div
                            key={index}
                            className="aspect-video bg-muted rounded-lg flex items-center justify-center"
                          >
                            <ImageIcon className="w-8 h-8 text-muted-foreground" />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium mb-3">Information</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Downloads</span>
                          <span>
                            {selectedPlugin.downloads.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Category</span>
                          <Badge variant="outline" className="text-xs">
                            {selectedPlugin.category}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span>License</span>
                          <span>{selectedPlugin.manifest.license}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Compatibility</span>
                          <span>
                            {selectedPlugin.compatibility.platforms.join(", ")}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-3">Tags</h4>
                      <div className="flex flex-wrap gap-1">
                        {selectedPlugin.tags.map((tag) => (
                          <Badge
                            key={tag}
                            variant="outline"
                            className="text-xs"
                          >
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t">
                    <div className="flex items-center gap-2">
                      {selectedPlugin.manifest.homepage && (
                        <Button variant="outline" size="sm" asChild>
                          <a
                            href={selectedPlugin.manifest.homepage}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <ExternalLink className="w-4 h-4 mr-2" />
                            Website
                          </a>
                        </Button>
                      )}
                      {selectedPlugin.manifest.repository && (
                        <Button variant="outline" size="sm" asChild>
                          <a
                            href={selectedPlugin.manifest.repository}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <ExternalLink className="w-4 h-4 mr-2" />
                            Repository
                          </a>
                        </Button>
                      )}
                    </div>

                    <Button onClick={() => handleInstall(selectedPlugin)}>
                      {selectedPlugin.pricing.type === "paid" ? (
                        <>
                          <ShoppingCart className="w-4 h-4 mr-2" />
                          Buy for ${selectedPlugin.pricing.price}
                        </>
                      ) : (
                        <>
                          <Download className="w-4 h-4 mr-2" />
                          Install Plugin
                        </>
                      )}
                    </Button>
                  </div>
                </TabsContent>

                <TabsContent value="reviews" className="space-y-4">
                  {renderPluginReviews(selectedPlugin.id)}
                </TabsContent>

                <TabsContent value="details" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium mb-3">System Requirements</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Min Memory</span>
                          <span>
                            {selectedPlugin.manifest.systemRequirements
                              .minMemory || "N/A"}{" "}
                            MB
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Min Disk</span>
                          <span>
                            {selectedPlugin.manifest.systemRequirements
                              .minDisk || "N/A"}{" "}
                            MB
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Platform</span>
                          <span>
                            {selectedPlugin.compatibility.platforms.join(", ")}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-3">Security</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Sandboxed</span>
                          <Badge
                            variant={
                              selectedPlugin.manifest.sandboxed
                                ? "default"
                                : "destructive"
                            }
                          >
                            {selectedPlugin.manifest.sandboxed ? "Yes" : "No"}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span>Network Access</span>
                          <Badge
                            variant={
                              selectedPlugin.manifest.securityPolicy
                                .allowNetworkAccess
                                ? "destructive"
                                : "default"
                            }
                          >
                            {selectedPlugin.manifest.securityPolicy
                              .allowNetworkAccess
                              ? "Allowed"
                              : "Blocked"}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span>File System</span>
                          <Badge
                            variant={
                              selectedPlugin.manifest.securityPolicy
                                .allowFileSystemAccess
                                ? "destructive"
                                : "default"
                            }
                          >
                            {selectedPlugin.manifest.securityPolicy
                              .allowFileSystemAccess
                              ? "Allowed"
                              : "Blocked"}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};
