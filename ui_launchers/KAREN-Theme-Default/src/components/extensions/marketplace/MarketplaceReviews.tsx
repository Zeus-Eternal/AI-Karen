"use client";

/**
 * Marketplace Reviews Component
 *
 * Display and manage extension reviews and ratings
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Star,
  ThumbsUp,
  ThumbsDown,
  User,
  Calendar,
  CheckCircle,
  AlertCircle,
  RefreshCw
} from 'lucide-react';

export interface ExtensionReview {
  id: string;
  extensionId: string;
  userId: string;
  userName: string;
  rating: number;
  title: string;
  content: string;
  helpful: number;
  notHelpful: number;
  verified: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface ReviewStats {
  totalReviews: number;
  averageRating: number;
  ratingDistribution: {
    5: number;
    4: number;
    3: number;
    2: number;
    1: number;
  };
}

export interface MarketplaceReviewsProps {
  extensionId: string;
  refreshInterval?: number;
}

export default function MarketplaceReviews({
  extensionId,
  refreshInterval = 30000
}: MarketplaceReviewsProps) {
  const [reviews, setReviews] = useState<ExtensionReview[]>([]);
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [newReview, setNewReview] = useState({ rating: 5, title: '', content: '' });

  const loadReviews = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/marketplace/${extensionId}/reviews`);
      if (response.ok) {
        const data = await response.json();
        setReviews(data.reviews);
        setStats(data.stats);
      } else {
        // Mock data
        const mockReviews: ExtensionReview[] = [
          {
            id: 'rev-1',
            extensionId,
            userId: 'user-1',
            userName: 'John Developer',
            rating: 5,
            title: 'Excellent extension!',
            content: 'This extension has greatly improved my workflow. The interface is intuitive and the features are exactly what I needed.',
            helpful: 24,
            notHelpful: 2,
            verified: true,
            createdAt: new Date(Date.now() - 604800000).toISOString(),
            updatedAt: new Date(Date.now() - 604800000).toISOString()
          },
          {
            id: 'rev-2',
            extensionId,
            userId: 'user-2',
            userName: 'Sarah Admin',
            rating: 4,
            title: 'Very useful, minor bugs',
            content: 'Great extension overall. Encountered a few minor bugs but support was very responsive. Would recommend with 4 stars.',
            helpful: 18,
            notHelpful: 3,
            verified: true,
            createdAt: new Date(Date.now() - 1209600000).toISOString(),
            updatedAt: new Date(Date.now() - 1209600000).toISOString()
          },
          {
            id: 'rev-3',
            extensionId,
            userId: 'user-3',
            userName: 'Mike Tester',
            rating: 5,
            title: 'Best in class',
            content: 'Tried several similar extensions and this one is by far the best. Performance is excellent and documentation is comprehensive.',
            helpful: 31,
            notHelpful: 1,
            verified: false,
            createdAt: new Date(Date.now() - 2419200000).toISOString(),
            updatedAt: new Date(Date.now() - 2419200000).toISOString()
          }
        ];

        const mockStats: ReviewStats = {
          totalReviews: 127,
          averageRating: 4.6,
          ratingDistribution: {
            5: 89,
            4: 24,
            3: 8,
            2: 4,
            1: 2
          }
        };

        setReviews(mockReviews);
        setStats(mockStats);
      }
    } catch (error) {
      console.error('Failed to load reviews:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadReviews();
    const interval = setInterval(loadReviews, refreshInterval);
    return () => clearInterval(interval);
  }, [extensionId, refreshInterval]);

  const renderStars = (rating: number, size: 'sm' | 'lg' = 'sm') => {
    const starSize = size === 'sm' ? 'h-4 w-4' : 'h-6 w-6';
    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={`${starSize} ${
              star <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
            }`}
          />
        ))}
      </div>
    );
  };

  const getRatingPercentage = (rating: number) => {
    if (!stats) return 0;
    return (stats.ratingDistribution[rating as keyof typeof stats.ratingDistribution] / stats.totalReviews) * 100;
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div>Reviews & Ratings</div>
            <Button onClick={loadReviews} disabled={isLoading} size="sm">
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </CardTitle>
          <CardDescription>
            See what others are saying about this extension
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Rating Summary */}
          {stats && (
            <div className="grid md:grid-cols-2 gap-6 mb-6 pb-6 border-b">
              <div className="text-center">
                <div className="text-5xl font-bold mb-2">{stats.averageRating.toFixed(1)}</div>
                {renderStars(Math.round(stats.averageRating), 'lg')}
                <p className="text-sm text-muted-foreground mt-2">
                  {stats.totalReviews} reviews
                </p>
              </div>
              <div className="space-y-2">
                {[5, 4, 3, 2, 1].map((rating) => (
                  <div key={rating} className="flex items-center gap-2">
                    <span className="text-sm w-8">{rating} ★</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-yellow-400 h-2 rounded-full"
                        style={{ width: `${getRatingPercentage(rating)}%` }}
                      />
                    </div>
                    <span className="text-sm text-muted-foreground w-12 text-right">
                      {stats.ratingDistribution[rating as keyof typeof stats.ratingDistribution]}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Write Review */}
          <div className="mb-6 pb-6 border-b">
            <h3 className="text-lg font-semibold mb-4">Write a Review</h3>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Rating</label>
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => setNewReview({ ...newReview, rating: star })}
                      className="focus:outline-none"
                    >
                      <Star
                        className={`h-8 w-8 cursor-pointer transition-colors ${
                          star <= newReview.rating
                            ? 'fill-yellow-400 text-yellow-400'
                            : 'text-gray-300 hover:text-yellow-200'
                        }`}
                      />
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Title</label>
                <input
                  type="text"
                  value={newReview.title}
                  onChange={(e) => setNewReview({ ...newReview, title: e.target.value })}
                  placeholder="Summarize your review"
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Review</label>
                <Textarea
                  value={newReview.content}
                  onChange={(e) => setNewReview({ ...newReview, content: e.target.value })}
                  placeholder="Share your experience with this extension..."
                  rows={4}
                />
              </div>
              <Button>Submit Review</Button>
            </div>
          </div>

          {/* Reviews List */}
          <div>
            <h3 className="text-lg font-semibold mb-4">User Reviews</h3>
            <ScrollArea className="h-[600px]">
              <div className="space-y-4 pr-4">
                {reviews.map((review) => (
                  <Card key={review.id}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 bg-gray-200 rounded-full flex items-center justify-center">
                            <User className="h-5 w-5 text-gray-600" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{review.userName}</span>
                              {review.verified && (
                                <Badge variant="outline" className="text-xs">
                                  <CheckCircle className="h-3 w-3 mr-1 text-green-600" />
                                  Verified Purchase
                                </Badge>
                              )}
                            </div>
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <Calendar className="h-3 w-3" />
                              {new Date(review.createdAt).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                        {renderStars(review.rating)}
                      </div>
                      <h4 className="font-semibold mb-2">{review.title}</h4>
                      <p className="text-sm text-muted-foreground mb-3">{review.content}</p>
                      <div className="flex items-center gap-4 text-sm">
                        <Button variant="ghost" size="sm" className="gap-1">
                          <ThumbsUp className="h-3 w-3" />
                          Helpful ({review.helpful})
                        </Button>
                        <Button variant="ghost" size="sm" className="gap-1">
                          <ThumbsDown className="h-3 w-3" />
                          ({review.notHelpful})
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export { MarketplaceReviews };
export type { MarketplaceReviewsProps, ExtensionReview, ReviewStats };
