"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { MapPin, Star, Search, Info, TrendingUp } from "lucide-react";

export default function YelpPluginPage() {
  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3">
        <MapPin className="h-8 w-8 text-orange-600" />
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Yelp Integration</h2>
          <p className="text-sm text-muted-foreground">
            Discover and rate local businesses, restaurants, and services with detailed reviews
          </p>
        </div>
      </div>

      <Alert variant="default" className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
        <Info className="h-4 w-4 text-blue-600" />
        <AlertTitle className="text-blue-800 dark:text-blue-200">Coming Soon</AlertTitle>
        <AlertDescription className="text-blue-700 dark:text-blue-300">
          This plugin is currently under development. Full Yelp integration with search, reviews, and ratings will be available soon.
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Planned Features</CardTitle>
          <CardDescription>Upcoming capabilities for Yelp integration</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start gap-4 p-4 border rounded-lg">
            <Search className="h-8 w-8 text-blue-500 mt-1" />
            <div>
              <h4 className="font-semibold">Business Search</h4>
              <p className="text-sm text-muted-foreground">
                Search for businesses by name, location, category, or keywords
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4 p-4 border rounded-lg">
            <Star className="h-8 w-8 text-yellow-500 mt-1" />
            <div>
              <h4 className="font-semibold">Review & Ratings</h4>
              <p className="text-sm text-muted-foreground">
                Access detailed reviews and ratings from real users for businesses
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4 p-4 border rounded-lg">
            <MapPin className="h-8 w-8 text-green-500 mt-1" />
            <div>
              <h4 className="font-semibold">Location-Based Recommendations</h4>
              <p className="text-sm text-muted-foreground">
                Get personalized recommendations based on your location and preferences
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4 p-4 border rounded-lg">
            <TrendingUp className="h-8 w-8 text-purple-500 mt-1" />
            <div>
              <h4 className="font-semibold">Popular & Trending</h4>
              <p className="text-sm text-muted-foreground">
                Discover trending businesses and what's popular in your area
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Usage</CardTitle>
          <CardDescription>How to use Yelp features</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            When Yelp integration is available, you can ask Karen to help you find and rate local businesses.
          </p>
          <Alert>
            <AlertTitle className="text-sm font-semibold">Example Prompts</AlertTitle>
            <AlertDescription className="text-xs">
              <ul className="list-disc list-inside space-y-1">
                <li>"Find restaurants near me"</li>
                <li>"Search for coffee shops in San Francisco"</li>
                <li>"What are the top-rated Italian restaurants in New York?"</li>
                <li>"Show me popular businesses in downtown"</li>
              </ul>
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Privacy Notice</CardTitle>
          <CardDescription>Your data is handled securely</CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-center gap-2">
              <Info className="h-4 w-4" />
              Your location is used only for local recommendations
            </li>
            <li className="flex items-center gap-2">
              <Info className="h-4 w-4" />
              Yelp API credentials are stored securely
            </li>
            <li className="flex items-center gap-2">
              <Info className="h-4 w-4" />
              No personal information is shared without your consent
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}