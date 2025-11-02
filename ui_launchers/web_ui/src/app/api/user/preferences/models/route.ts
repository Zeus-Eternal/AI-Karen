/**
 * User Model Preferences API
 * 
 * Manages user preferences for model selection including last selected model,
 * default model, and other selection preferences.
 */
import { NextRequest, NextResponse } from 'next/server';
import { getDatabaseClient } from '@/lib/database/client';
/**
 * GET /api/user/preferences/models
 * Get user model selection preferences
 */
export async function GET(request: NextRequest) {
  try {
    // For now, return mock preferences
    // In production, this would query the user preferences from database
    const mockPreferences = {
      lastSelectedModel: 'Phi-3-mini-4k-instruct-q4.gguf',
      defaultModel: 'Phi-3-mini-4k-instruct-q4.gguf',
      preferredProviders: ['local', 'openai'],
      preferLocal: true,
      autoSelectFallback: true
    };
    return NextResponse.json(mockPreferences);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to get user model preferences' },
      { status: 500 }
    );
  }
}
/**
 * PUT /api/user/preferences/models
 * Update user model selection preferences
 */
export async function PUT(request: NextRequest) {
  try {
    const body = await request.json();
    // Validate the request body
    const allowedFields = [
      'lastSelectedModel',
      'defaultModel', 
      'preferredProviders',
      'preferLocal',
      'autoSelectFallback'
    ];
    const preferences: Record<string, any> = {};
    for (const field of allowedFields) {
      if (field in body) {
        preferences[field] = body[field];
      }
    }
    // For now, just log the preferences
    // In production, this would save to database
    // Mock successful response
    return NextResponse.json({
      success: true,
      message: 'Model preferences updated successfully',
      preferences

  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to update user model preferences' },
      { status: 500 }
    );
  }
}
