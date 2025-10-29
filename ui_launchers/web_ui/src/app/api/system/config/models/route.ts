/**
 * System Model Configuration API
 * 
 * Manages system-wide model configuration including default models
 * and global model selection settings.
 */

import { NextRequest, NextResponse } from 'next/server';
import { getDatabaseClient } from '@/lib/database/client';

/**
 * GET /api/system/config/models
 * Get system model configuration
 */
export async function GET(request: NextRequest) {
  try {
    // For now, return mock system configuration
    // In production, this would query system configuration from database
    const mockConfig = {
      defaultModel: 'Phi-3-mini-4k-instruct-q4.gguf', // System default model - better than TinyLlama
      fallbackModel: 'Phi-3-mini-4k-instruct-q4.gguf',
      autoSelectEnabled: true,
      preferLocalModels: true,
      allowedProviders: ['openai', 'local', 'huggingface'],
      maxConcurrentModels: 3,
      modelSelectionTimeout: 60000, // 60 seconds - increased timeout
      enableModelCaching: true,
      cacheExpirationTime: 300000 // 5 minutes
    };

    return NextResponse.json(mockConfig);

  } catch (error) {
    console.error('Error getting system model configuration:', error);
    return NextResponse.json(
      { error: 'Failed to get system model configuration' },
      { status: 500 }
    );
  }
}

/**
 * PUT /api/system/config/models
 * Update system model configuration (admin only)
 */
export async function PUT(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Validate the request body
    const allowedFields = [
      'defaultModel',
      'fallbackModel',
      'autoSelectEnabled',
      'preferLocalModels',
      'allowedProviders',
      'maxConcurrentModels',
      'modelSelectionTimeout',
      'enableModelCaching',
      'cacheExpirationTime'
    ];
    
    const config: Record<string, any> = {};
    for (const field of allowedFields) {
      if (field in body) {
        config[field] = body[field];
      }
    }

    // For now, just log the configuration
    // In production, this would save to database and require admin authentication
    console.log('Saving system model configuration:', config);

    // Mock successful response
    return NextResponse.json({
      success: true,
      message: 'System model configuration updated successfully',
      config
    });

  } catch (error) {
    console.error('Error updating system model configuration:', error);
    return NextResponse.json(
      { error: 'Failed to update system model configuration' },
      { status: 500 }
    );
  }
}