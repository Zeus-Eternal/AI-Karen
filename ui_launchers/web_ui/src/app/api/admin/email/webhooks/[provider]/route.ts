/**
 * Email Webhook Handler API
 * 
 * API endpoint for receiving webhooks from email service providers
 * to track delivery status, bounces, and other email events.
 */

import { NextRequest, NextResponse } from 'next/server';
import { webhookHandler } from '@/lib/email/delivery-tracker';

/**
 * POST /api/admin/email/webhooks/[provider]
 * Handle incoming webhooks from email providers
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ provider: string }> }
) {
  const { provider: providerName } = await params;
  const provider = providerName.toLowerCase();
  
  try {
    
    // Validate provider
    const supportedProviders = ['sendgrid', 'ses', 'mailgun', 'postmark', 'smtp'];
    if (!supportedProviders.includes(provider)) {
      return NextResponse.json(
        { error: 'Unsupported email provider' },
        { status: 400 }
      );
    }

    // Get request headers and body
    const headers: Record<string, string> = {};
    request.headers.forEach((value, key) => {
      headers[key] = value;
    });

    const body = await request.json();

    // Extract event type based on provider
    let eventType: string;
    switch (provider) {
      case 'sendgrid':
        eventType = body.event || 'unknown';
        break;
      case 'ses':
        eventType = body.eventType || body.notificationType || 'unknown';
        break;
      case 'mailgun':
        eventType = body.event || 'unknown';
        break;
      case 'postmark':
        eventType = body.Type || 'unknown';
        break;
      default:
        eventType = body.event_type || body.type || 'unknown';
    }

    // Process webhook
    await webhookHandler.processIncomingWebhook(provider, eventType, body, headers);

    // Return success response
    return NextResponse.json({ success: true, message: 'Webhook processed successfully' });

  } catch (error) {
    console.error(`Error processing ${provider} webhook:`, error);
    
    // Return error but don't expose internal details
    return NextResponse.json(
      { error: 'Failed to process webhook' },
      { status: 500 }
    );
  }
}

/**
 * GET /api/admin/email/webhooks/[provider]
 * Webhook verification endpoint (for providers that require GET verification)
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ provider: string }> }
) {
  const { provider: providerName } = await params;
  const provider = providerName.toLowerCase();
  
  try {
    const { searchParams } = new URL(request.url);

    // Handle provider-specific verification
    switch (provider) {
      case 'mailgun':
        // Mailgun webhook verification
        const token = searchParams.get('token');
        const timestamp = searchParams.get('timestamp');
        const signature = searchParams.get('signature');
        
        if (token && timestamp && signature) {
          // In a real implementation, verify the signature
          return NextResponse.json({ success: true });
        }
        break;
        
      case 'postmark':
        // Postmark webhook verification
        const challenge = searchParams.get('challenge');
        if (challenge) {
          return new NextResponse(challenge, { status: 200 });
        }
        break;
        
      default:
        return NextResponse.json(
          { error: 'GET verification not supported for this provider' },
          { status: 400 }
        );
    }

    return NextResponse.json(
      { error: 'Invalid verification request' },
      { status: 400 }
    );

  } catch (error) {
    console.error(`Error verifying ${provider} webhook:`, error);
    return NextResponse.json(
      { error: 'Failed to verify webhook' },
      { status: 500 }
    );
  }
}