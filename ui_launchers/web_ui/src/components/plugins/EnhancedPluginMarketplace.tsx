"use client";

import React, { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import {
  Search,
  Filter,
  Grid,
  List,
  SortAsc,
  SortDesc,
  ArrowLeft,
  Package,
  Award,
  CheckCircle,
  Bookmark,
  BookmarkCheck,
  Eye,
  ShoppingCart,
  Download,
  MessageSquare,
  ThumbsUp,
  Flag,
  Image as ImageIcon,
  ExternalLink,
  Share,
  Star,
} from "lucide-react";

import type { PluginMarketplaceEntry } from "@/types/plugins";

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

/* ------------------------- Mock Data ------------------------- */

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
      systemRequirements: { minMemory: 128, minDisk: 50 },
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
    screenshots: ["/screenshots/content-gen-1.png", "/screenshots/content-gen-2.png"],
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
      "This plugin has transformed how our team uses Slack. The AI analysis is accurate and the automated responses save hours each week. Sentiment tracking gives real morale insight.",
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
    title: "Great, could use more customization",
    content:
      "Smooth integration overall. Would love more options for customizing automated responses. Analytics are helpful.",
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
    title: "Surprisingly strong content",
    content:
      "Great for blog and social posts. Templates are solid and brand-voice tuning works really well.",
    timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
    helpful: 15,
    verified: true,
    version: "1.5.2",
  },
];

/* ----------------------- Component ----------------------- */

export const EnhancedPluginMarketplace: React.FC<EnhancedPluginMarketplaceProps> = ({
  onClose,
  onInstall,
  onPurchase,
}) => {
  const [plugins, setPlugins] = useState<PluginMarketplaceEntry[]>(mockEnhancedPlugins);
  const [reviews] = useState<PluginReview[]>(mockReviews);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPlugin, setSelectedPlugin] = useState<PluginMarketplaceEntry | null>(null);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [sortBy, setSortBy] = useState<"popular" | "rating" | "recent" | "name" | "price">(
    "popular"
  );
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [showFilters, setShowFilters] = useState(false);
  const [bookmarkedPlugins, setBookmarkedPlugins] = useState<Set<string>>(new Set());

  const [filters, setFilters] = useState<MarketplaceFilters>({
    category: [],
    pricing: [],
    rating: 0,
    verified: false,
    featured: false,
    compatibility: [],
    tags: [],
  });

  const filterOptions = useMemo(() => {
    const categories = Array.from(new Set(plugins.map((p) => p.category)));
    const pricingTypes = Array.from(new Set(plugins.map((p) => p.pricing.type)));
    const allTags = Array.from(new Set(plugins.flatMap((p) => p.tags)));
    const platforms = Array.from(new Set(plugins.flatMap((p) => p.compatibility.platforms)));
    return { categories, pricingTypes, allTags, platforms };
  }, [plugins]);

  const filteredPlugins = useMemo(() => {
    let filtered = [...plugins];

    // Search
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.description.toLowerCase().includes(q) ||
          p.tags.some((t) => t.toLowerCase().includes(q)) ||
          p.author.name.toLowerCase().includes(q)
      );
    }

    // Category
    if (filters.category.length) {
      filtered = filtered.filter((p) => filters.category.includes(p.category));
    }

    // Pricing
    if (filters.pricing.length) {
      filtered = filtered.filter((p) => filters.pricing.includes(p.pricing.type));
    }

    // Rating
    if (filters.rating > 0) {
      filtered = filtered.filter((p) => p.rating >= filters.rating);
    }

    // Verified
    if (filters.verified) {
      filtered = filtered.filter((p) => p.verified);
    }

    // Featured
    if (filters.featured) {
      filtered = filtered.filter((p) => p.featured);
    }

    // Tags (any)
    if (filters.tags.length) {
      filtered = filtered.filter((p) => filters.tags.some((t) => p.tags.includes(t)));
    }

    // Sort
    filtered.sort((a, b) => {
      let aVal: any;
      let bVal: any;
      switch (sortBy) {
        case "popular":
          aVal = a.downloads;
          bVal = b.downloads;
          break;
        case "rating":
          aVal = a.rating;
          bVal = b.rating;
          break;
        case "recent":
          aVal = a.version;
          bVal = b.version;
          break;
        case "name":
          aVal = a.name.toLowerCase();
          bVal = b.name.toLowerCase();
          break;
        case "price":
          aVal = a.pricing.price || 0;
          bVal = b.pricing.price || 0;
          break;
        default:
          aVal = 0;
          bVal = 0;
      }
      if (sortOrder === "asc") return aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
      return aVal > bVal ? -1 : aVal < bVal ? 1 : 0;
    });

    return filtered;
  }, [plugins, searchQuery, filters, sortBy, sortOrder]);

  const handleInstall = (plugin: PluginMarketplaceEntry) => {
    if (plugin.pricing.type === "paid" && onPurchase) onPurchase(plugin);
    else onInstall(plugin);
    onClose();
  };

  const toggleBookmark = (pluginId: string) => {
    setBookmarkedPlugins((prev) => {
      const next = new Set(prev);
      if (next.has(pluginId)) next.delete(pluginId);
      else next.add(pluginId);
      return next;
    });
  };

  const renderStars = (rating: number, size: "sm" | "md" = "sm") => {
    const starSize = size === "sm" ? "w-3 h-3" : "w-4 h-4";
    return (
      <div className="flex items-center">
        {Array.from({ length: 5 }, (_, i) => (
          <Star
            key={i}
            className={`${starSize} ${
              i < Math.floor(rating)
                ? "text-yellow-500 fill-yellow-500"
                : i < rating
                ? "text-yellow-500 fill-yellow-500 opacity-50"
                : "text-gray-300"
            }`}
          />
        ))}
      </div>
    );
  };

  const renderPluginCard = (plugin: PluginMarketplaceEntry) => {
    const isBookmarked = bookmarkedPlugins.has(plugin.id);
    return (
      <Card
        key={plugin.id}
        className={`transition-all duration-200 ${viewMode === "list" ? "" : "hover:shadow-lg"}`}
      >
        <CardContent className="p-0 sm:p-4 md:p-6">
          {/* Banner */}
          <div className="relative h-48 bg-gradient-to-br from-blue-500 to-purple-600 rounded-t-lg">
            <div className="absolute inset-0 flex items-center justify-center">
              <Package className="w-16 h-16 text-white opacity-80" />
            </div>
            <div className="absolute top-3 right-3 flex gap-2">
              {plugin.featured && (
                <Badge variant="default" className="flex items-center gap-1">
                  <Award className="w-3 h-3" />
                  Featured
                </Badge>
              )}
              {plugin.verified && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  <CheckCircle className="w-3 h-3" />
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
              {isBookmarked ? <BookmarkCheck className="w-4 h-4" /> : <Bookmark className="w-4 h-4" />}
            </Button>
          </div>

          {/* Body */}
          <div className="p-4 sm:p-4 md:p-6">
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <h3 className="font-semibold text-lg line-clamp-1">{plugin.name}</h3>
                <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                  by {plugin.author.name}
                </p>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-1 mb-1 justify-end">
                  {renderStars(plugin.rating)}
                  <span className="text-xs text-muted-foreground ml-1 sm:text-sm md:text-base">
                    {plugin.rating.toFixed(1)}
                  </span>
                </div>
                <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                  {plugin.reviewCount} reviews
                </div>
              </div>
            </div>

            <p className="text-sm text-muted-foreground mb-3 line-clamp-2 md:text-base lg:text-lg">
              {plugin.description}
            </p>

            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="capitalize">
                  {plugin.category}
                </Badge>
                <Badge
                  variant={plugin.pricing.type === "free" ? "secondary" : "default"}
                  className="capitalize"
                >
                  {plugin.pricing.type === "free"
                    ? "Free"
                    : plugin.pricing.type === "freemium"
                    ? "Freemium"
                    : `$${plugin.pricing.price}`}
                </Badge>
              </div>
              <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                {plugin.downloads.toLocaleString()} downloads
              </div>
            </div>

            <div className="flex items-center gap-1 mb-4 flex-wrap">
              {plugin.tags.slice(0, 3).map((tag) => (
                <Badge key={tag} variant="outline" className="capitalize">
                  {tag}
                </Badge>
              ))}
              {plugin.tags.length > 3 && (
                <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
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
                Preview
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
    if (!pluginReviews.length) {
      return (
        <div className="text-center py-8">
          <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <h3 className="text-lg font-medium mb-2">No Reviews Yet</h3>
          <p className="text-muted-foreground">Be the first to share your experience.</p>
        </div>
      );
    }
    return (
      <div className="space-y-4">
        {pluginReviews.map((review) => (
          <Card key={review.id}>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-start gap-3">
                <Avatar className="w-10 h-10">
                  <AvatarImage src={review.userAvatar} />
                  <AvatarFallback>
                    {review.userName
                      .split(" ")
                      .map((n) => n[0])
                      .join("")
                      .slice(0, 2)
                      .toUpperCase()}
                  </AvatarFallback>
                </Avatar>

                <div className="flex-1">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{review.userName}</span>
                        {review.verified && (
                          <Badge variant="outline" className="flex items-center gap-1">
                            <CheckCircle className="w-3 h-3" />
                            Verified
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        {renderStars(review.rating)}
                        <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                          v{review.version}
                        </span>
                        <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                          {review.timestamp.toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <h4 className="font-medium mb-2">{review.title}</h4>
                  <p className="text-sm text-muted-foreground mb-3 md:text-base lg:text-lg">
                    {review.content}
                  </p>

                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="sm" className="text-xs sm:text-sm md:text-base">
                      <ThumbsUp className="w-3 h-3 mr-1" />
                      Helpful ({review.helpful})
                    </Button>
                    <Button variant="ghost" size="sm" className="text-xs sm:text-sm md:text-base">
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
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Plugin Marketplace</h1>
          <p className="text-muted-foreground">Discover, purchase, and install plugins.</p>
        </div>
      </div>

      {/* Search + Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4">
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search plugins…"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button variant="outline" onClick={() => setShowFilters((v) => !v)}>
                <Filter className="w-4 h-4 mr-2" />
                Filters
              </Button>
            </div>

            {showFilters && (
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 p-4 bg-muted/50 rounded-lg">
                {/* Category */}
                <div>
                  <Label className="text-sm font-medium mb-2 block">Category</Label>
                  <div className="space-y-2">
                    {filterOptions.categories.map((category) => (
                      <div key={category} className="flex items-center space-x-2 capitalize">
                        <Checkbox
                          id={`category-${category}`}
                          checked={filters.category.includes(category)}
                          onCheckedChange={(checked) =>
                            setFilters((prev) => ({
                              ...prev,
                              category: checked
                                ? [...prev.category, category]
                                : prev.category.filter((c) => c !== category),
                            }))
                          }
                        />
                        <Label htmlFor={`category-${category}`} className="text-sm md:text-base lg:text-lg">
                          {category}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Pricing */}
                <div>
                  <Label className="text-sm font-medium mb-2 block">Pricing</Label>
                  <div className="space-y-2 capitalize">
                    {filterOptions.pricingTypes.map((type) => (
                      <div key={type} className="flex items-center space-x-2">
                        <Checkbox
                          id={`pricing-${type}`}
                          checked={filters.pricing.includes(type)}
                          onCheckedChange={(checked) =>
                            setFilters((prev) => ({
                              ...prev,
                              pricing: checked
                                ? [...prev.pricing, type]
                                : prev.pricing.filter((p) => p !== type),
                            }))
                          }
                        />
                        <Label htmlFor={`pricing-${type}`} className="text-sm md:text-base lg:text-lg">
                          {type}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Rating */}
                <div>
                  <Label className="text-sm font-medium mb-2 block">Minimum Rating</Label>
                  <Select
                    value={String(filters.rating)}
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

                {/* Flags */}
                <div>
                  <Label className="text-sm font-medium mb-2 block">Flags</Label>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="verified"
                        checked={filters.verified}
                        onCheckedChange={(checked) =>
                          setFilters((prev) => ({ ...prev, verified: Boolean(checked) }))
                        }
                      />
                      <Label htmlFor="verified" className="text-sm md:text-base lg:text-lg">
                        Verified only
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="featured"
                        checked={filters.featured}
                        onCheckedChange={(checked) =>
                          setFilters((prev) => ({ ...prev, featured: Boolean(checked) }))
                        }
                      />
                      <Label htmlFor="featured" className="text-sm md:text-base lg:text-lg">
                        Featured only
                      </Label>
                    </div>
                  </div>
                </div>

                {/* Sort */}
                <div>
                  <Label className="text-sm font-medium mb-2 block">Sort</Label>
                  <div className="space-y-2">
                    <Select value={sortBy} onValueChange={(v: any) => setSortBy(v)}>
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
              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                {filteredPlugins.length} plugin{filteredPlugins.length !== 1 ? "s" : ""} found
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
            <p className="text-muted-foreground">Try adjusting your search or filters.</p>
          </CardContent>
        </Card>
      ) : (
        <div className={viewMode === "grid" ? "grid gap-6 md:grid-cols-2 lg:grid-cols-3" : "space-y-4"}>
          {filteredPlugins.map((plugin) => renderPluginCard(plugin))}
        </div>
      )}

      {/* Plugin Detail Dialog */}
      <Dialog open={!!selectedPlugin} onOpenChange={() => setSelectedPlugin(null)}>
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
                      {selectedPlugin.verified && <CheckCircle className="w-5 h-5 text-blue-600" />}
                      {selectedPlugin.featured && (
                        <Badge variant="default" className="flex items-center gap-1">
                          <Award className="w-3 h-3" />
                          Featured
                        </Badge>
                      )}
                    </DialogTitle>
                    <DialogDescription className="text-base">
                      by {selectedPlugin.author.name} • v{selectedPlugin.version}
                    </DialogDescription>
                    <div className="flex items-center gap-4 mt-2">
                      <div className="flex items-center gap-1">
                        {renderStars(selectedPlugin.rating, "md")}
                        <span className="ml-1 font-medium">{selectedPlugin.rating.toFixed(1)}</span>
                        <span className="text-muted-foreground">
                          ({selectedPlugin.reviewCount} reviews)
                        </span>
                      </div>
                      <Badge
                        variant={selectedPlugin.pricing.type === "free" ? "secondary" : "default"}
                        className="capitalize"
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
                    <Button variant="outline" size="sm" onClick={() => toggleBookmark(selectedPlugin.id)}>
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
                  <TabsTrigger value="reviews">Reviews ({selectedPlugin.reviewCount})</TabsTrigger>
                  <TabsTrigger value="details">Details</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-6">
                  <p className="text-sm leading-relaxed md:text-base lg:text-lg">
                    {selectedPlugin.description}
                  </p>

                  {!!selectedPlugin.screenshots.length && (
                    <div>
                      <h4 className="font-medium mb-3">Screenshots</h4>
                      <div className="grid grid-cols-2 gap-4">
                        {selectedPlugin.screenshots.map((_, idx) => (
                          <div
                            key={idx}
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
                      <div className="space-y-2 text-sm md:text-base lg:text-lg">
                        <div className="flex justify-between">
                          <span>Downloads</span>
                          <span>{selectedPlugin.downloads.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Category</span>
                          <Badge variant="outline" className="capitalize">
                            {selectedPlugin.category}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span>License</span>
                          <span>{selectedPlugin.manifest.license}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Compatibility</span>
                          <span>{selectedPlugin.compatibility.platforms.join(", ")}</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-3">Tags</h4>
                      <div className="flex flex-wrap gap-1">
                        {selectedPlugin.tags.map((tag) => (
                          <Badge key={tag} variant="outline" className="capitalize">
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
                            Homepage
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
                          Install
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
                      <div className="space-y-2 text-sm md:text-base lg:text-lg">
                        <div className="flex justify-between">
                          <span>Min Memory</span>
                          <span>{selectedPlugin.manifest.systemRequirements.minMemory ?? "N/A"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Min Disk</span>
                          <span>{selectedPlugin.manifest.systemRequirements.minDisk ?? "N/A"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Platform</span>
                          <span>{selectedPlugin.compatibility.platforms.join(", ")}</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-3">Security</h4>
                      <div className="space-y-2 text-sm md:text-base lg:text-lg">
                        <div className="flex justify-between">
                          <span>Sandboxed</span>
                          <Badge variant={selectedPlugin.manifest.sandboxed ? "default" : "destructive"}>
                            {selectedPlugin.manifest.sandboxed ? "Yes" : "No"}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span>Network Access</span>
                          <Badge
                            variant={
                              selectedPlugin.manifest.securityPolicy.allowNetworkAccess
                                ? "destructive"
                                : "default"
                            }
                          >
                            {selectedPlugin.manifest.securityPolicy.allowNetworkAccess
                              ? "Allowed"
                              : "Blocked"}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span>File System</span>
                          <Badge
                            variant={
                              selectedPlugin.manifest.securityPolicy.allowFileSystemAccess
                                ? "destructive"
                                : "default"
                            }
                          >
                            {selectedPlugin.manifest.securityPolicy.allowFileSystemAccess
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
