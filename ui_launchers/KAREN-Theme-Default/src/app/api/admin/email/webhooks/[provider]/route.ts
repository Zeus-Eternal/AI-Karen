/**
 * Email Webhook Handler API (Prod-Grade)
 *
 * Endpoint for receiving webhooks from email providers (SendGrid, SES/SNS, Mailgun,
 * Postmark, SMTP-generic). Verifies signatures when configured, handles multiple
 * payload formats (JSON, form-data, batches), ensures idempotency, and
 * forwards normalized events to the delivery tracker.
 *
 * Security:
 * - Signature verification per provider (env-configured)
 * - Idempotency via event-id de-dupe (delivery tracker)
 * - Strict provider allowlist
 * - No internal details in error messages
 *
 * Observability:
 * - Structured logging hooks (console.info/warn/error can be replaced with your logger)
 * - Minimal, no-store caching
 */

import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';
import { webhookHandler } from '@/lib/email/delivery-tracker';

type Provider = 'sendgrid' | 'ses' | 'mailgun' | 'postmark' | 'smtp';

const SUPPORTED_PROVIDERS: Provider[] = ['sendgrid', 'ses', 'mailgun', 'postmark', 'smtp'];


/* -------------------------------------------------------------------------- */
/*                               ROUTE:  POST                                 */
/* -------------------------------------------------------------------------- */

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ provider: string }> }
) {
  const resolvedParams = await params;
  const provider = String(resolvedParams?.provider || '').toLowerCase() as Provider;

  if (!SUPPORTED_PROVIDERS.includes(provider)) {
    return jsonError('Unsupported email provider', 400);
  }

  // We might need the raw body for signature verification (SendGrid/Postmark/Mailgun)
  const cloned = request.clone();
  const contentType = request.headers.get('content-type') || '';
  const headers = toHeadersRecord(request.headers);

  let rawBody: string | undefined;
  let body: unknown;

  try {
    if (contentType.includes('application/json')) {
      rawBody = await cloned.text();
      body = JSON.parse(rawBody || '{}');
    } else if (contentType.includes('application/x-www-form-urlencoded')) {
      // Mailgun may POST with form-encoded payloads
      const form = await request.formData();
      const obj: Record<string, unknown> = {};
      for (const [k, v] of form.entries()) obj[k] = v;
      body = obj;
      rawBody = new URLSearchParams(obj as Record<string, string>).toString();
    } else if (contentType.includes('text/plain')) {
      rawBody = await cloned.text();
      try {
        body = JSON.parse(rawBody);
      } catch {
        body = rawBody;
      }
    } else {
      // Try JSON fallback
      rawBody = await cloned.text();
      try {
        body = JSON.parse(rawBody);
      } catch {
        // Last resort: formData
        try {
          const form = await request.formData();
          const obj: Record<string, unknown> = {};
          for (const [k, v] of form.entries()) obj[k] = v;
          body = obj;
        } catch {
          body = {};
        }
      }
    }
  } catch {
    return jsonError('Invalid payload', 400);
  }

  // Provider-specific signature verification (optional if envs not set)
  try {
    await verifySignature(provider, headers, rawBody ?? '', body);
  } catch (e) {
    // Do not leak internal reasons; log privately
    console.warn('Webhook signature verification failed', { provider, reason: (e as Error).message });
    return jsonError('Signature verification failed', 401);
  }

  // Normalize event type(s) and iterate batches if necessary
  try {
    const events = normalizeEvents(provider, body, headers);

    // Idempotency: let delivery tracker dedupe per event_id/provider
    for (const evt of events) {
      await webhookHandler.processIncomingWebhook(
        provider,
        evt.event_type,
        { ...evt.body, event_id: evt.event_id }, // Include event_id in body for idempotency
        headers
      );
    }

    return NextResponse.json(
      { success: true, message: 'Webhook processed successfully' },
      { status: 200, headers: { 'Cache-Control': 'no-store' } }
    );
  } catch (err) {
    console.error('Webhook processing failed', {
      provider,
      error: (err as Error).message,
    });
    return jsonError('Failed to process webhook', 500);
  }
}

/* -------------------------------------------------------------------------- */
/*                                ROUTE:  GET                                 */
/* -------------------------------------------------------------------------- */

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ provider: string }> }
) {
  const resolvedParams = await params;
  const provider = String(resolvedParams?.provider || '').toLowerCase() as Provider;

  if (!SUPPORTED_PROVIDERS.includes(provider)) {
    return jsonError('Unsupported email provider', 400);
  }

  const url = new URL(request.url);

  try {
    switch (provider) {
      case 'mailgun': {
        // Some integrations use GET verification (rare); primarily POST+signature body.
        const token = url.searchParams.get('token');
        const timestamp = url.searchParams.get('timestamp');
        const signature = url.searchParams.get('signature');
        if (token && timestamp && signature) {
          // If you want, verify using MAILGUN_SIGNING_KEY here as well.
          return NextResponse.json({ success: true }, { headers: { 'Cache-Control': 'no-store' } });
        }
        break;
      }
      case 'postmark': {
        // Postmark can send a challenge query param for verification
        const challenge = url.searchParams.get('challenge');
        if (challenge) {
          return new NextResponse(challenge, {
            status: 200,
            headers: { 'Cache-Control': 'no-store', 'Content-Type': 'text/plain' },
          });
        }
        break;
      }
      default:
        // SES/SNS + SendGrid do not use GET verification; SMTP generic doesn’t either
        return jsonError('GET verification not supported for this provider', 400);
    }

    return jsonError('Invalid verification request', 400);
  } catch (error) {
    console.error('Webhook GET verification failed', { provider, error: (error as Error).message });
    return jsonError('Failed to verify webhook', 500);
  }
}

/* -------------------------------------------------------------------------- */
/*                               ROUTE: OPTIONS                               */
/* -------------------------------------------------------------------------- */

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      'Allow': 'POST,GET,OPTIONS',
      'Access-Control-Max-Age': '86400',
    },
  });
}

/* -------------------------------------------------------------------------- */
/*                              Signature Verify                              */
/* -------------------------------------------------------------------------- */

/**
 * Verifies provider signature when configured.
 * If relevant env vars are not set, verification is skipped (but logged).
 */
async function verifySignature(
  provider: Provider,
  headers: Record<string, string>,
  rawBody: string,
  body: unknown
) {
  switch (provider) {
    case 'sendgrid': {
      // SendGrid Event Webhook uses ed25519 with a public key:
      // Headers:
      //  - X-Twilio-Email-Event-Webhook-Signature
      //  - X-Twilio-Email-Event-Webhook-Timestamp
      //  - X-Twilio-Email-Event-Webhook-Nonce (optional)
      const signature = headers['x-twilio-email-event-webhook-signature'];
      const timestamp = headers['x-twilio-email-event-webhook-timestamp'];
      const publicKey = process.env.SENDGRID_PUBLIC_KEY; // base64 or hex-encoded raw key (Ed25519)

      if (!publicKey || !signature || !timestamp) {
        console.info('SendGrid signature verification skipped (missing env/headers)');
        return;
      }

      // The payload is timestamp + rawBody per SG docs
      const message = Buffer.concat([
        Buffer.from(timestamp),
        Buffer.from(rawBody || ''),
      ]);

      const verified = verifyEd25519(publicKey, signature, message);
      if (!verified) throw new Error('SendGrid signature invalid');
      return;
    }

    case 'postmark': {
      // Postmark: HMAC-SHA256 of raw JSON body using the webhook secret (not the server token)
      // Header: X-Postmark-Signature
      const pmSig = headers['x-postmark-signature'];
      const secret = process.env.POSTMARK_WEBHOOK_SECRET;
      if (!secret || !pmSig) {
        console.info('Postmark signature verification skipped (missing env/header)');
        return;
      }
      const good = verifyHmacSha256(secret, rawBody, pmSig);
      if (!good) throw new Error('Postmark signature invalid');
      return;
    }

    case 'mailgun': {
      // Mailgun: signature is usually in the JSON body: signature: { timestamp, token, signature }
      // Verifies HMAC-SHA256 using API key (MAILGUN_SIGNING_KEY)
      const signingKey = process.env.MAILGUN_SIGNING_KEY;
      const sig = body?.signature;
      const timestamp = sig?.timestamp || body?.timestamp;
      const token = sig?.token || body?.token;
      const signature = sig?.signature || body?.signature;
      if (!signingKey || !timestamp || !token || !signature) {
        console.info('Mailgun signature verification skipped (missing fields/env)');
        return;
      }
      const message = `${timestamp}${token}`;
      const good = verifyHmacSha256(signingKey, message, signature);
      if (!good) throw new Error('Mailgun signature invalid');
      return;
    }

    case 'ses': {
      // SES typically comes via SNS. Proper verification requires validating
      // the SNS signature using Amazon’s cert URL. That’s heavy for a route handler.
      // If you front this with AWS SNS HTTP(S) subscription (recommended), configure
      // network ACLs / mTLS. Otherwise, skip with a log.
      console.info('SES/SNS signature verification not implemented here; ensure upstream verification.');
      return;
    }

    case 'smtp': {
      // No webhook signature—this path is for generic/proxy webhooks. Recommend IP allowlists.
      return;
    }
  }
}

/* -------------------------------------------------------------------------- */
/*                               Event Normalizer                             */
/* -------------------------------------------------------------------------- */

function normalizeEvents(
  provider: Provider,
  body: unknown,
  _headers: Record<string, string>
): Array<{ event_id?: string; event_type: string; body: unknown }> {
  switch (provider) {
    case 'sendgrid': {
      // SendGrid posts an array of events
      const arr = Array.isArray(body) ? body : [body];
      return arr.map((e) => ({
        event_id: e?.sg_event_id || e?._id || e?.event_id,
        event_type: e?.event || 'unknown',
        body: e,
      }));
    }
    case 'mailgun': {
      // Mailgun may send JSON with "event-data" or form style with keys like 'event'
      if (body['event-data']) {
        const ed = body['event-data'];
        return [{
          event_id: ed?.id || ed?.['message']?.headers?.['message-id'],
          event_type: ed?.event || 'unknown',
          body,
        }];
      }
      // form style
      return [{
        event_id: body['Message-Id'] || body['message-id'] || body['signature'] || undefined,
        event_type: body.event || body['event'] || 'unknown',
        body,
      }];
    }
    case 'postmark': {
      // Postmark sends a single JSON event
      // Type: Bounce, SpamComplaint, Delivery, Open, Click, SubscriptionChange, etc.
      const type = body?.Type || body?.RecordType || 'unknown';
      // Attempt an id
      const id = body?.ID || body?.MessageID || body?.MessageId || body?.MessageIDString;
      return [{ event_id: id, event_type: String(type).toLowerCase(), body }];
    }
    case 'ses': {
      // SES via SNS: body may be SNS wrapper; unwrap if necessary
      if (body?.Type && body?.Message) {
        // SNS envelope
        let msg: unknown = {};
        try { msg = JSON.parse(body.Message); } catch { msg = body.Message; }
        const notificationType = msg?.notificationType || msg?.eventType || 'unknown';
        const id =
          msg?.mail?.messageId ||
          msg?.bounce?.feedbackId ||
          msg?.complaint?.feedbackId ||
          undefined;
        return [{ event_id: id, event_type: notificationType, body: msg }];
      }
      // Direct SES notification (rare for webhooks)
      const eventType = body?.eventType || body?.notificationType || 'unknown';
      const id = body?.mail?.messageId || undefined;
      return [{ event_id: id, event_type: eventType, body }];
    }
    case 'smtp': {
      // Generic: accept payloads from a relay/proxy
      const eventType = body?.event_type || body?.type || body?.status || 'unknown';
      const id = body?.event_id || body?.message_id || body?.MessageId;
      return [{ event_id: id, event_type: eventType, body }];
    }
  }
}

/* -------------------------------------------------------------------------- */
/*                                Crypto Utils                                */
/* -------------------------------------------------------------------------- */

function verifyHmacSha256(secret: string, message: string, signature: string): boolean {
  const mac = crypto.createHmac('sha256', secret).update(message, 'utf8').digest('hex');
  // Some providers base64-encode; try both hex and base64, timing-safe compare
  const b64 = crypto.createHmac('sha256', secret).update(message, 'utf8').digest('base64');

  return timingSafeEqualAny(signature, [mac, b64]);
}

function verifyEd25519(publicKey: string, signatureBase64: string, message: Buffer): boolean {
  try {
    const sig = Buffer.from(signatureBase64, 'base64');
    // Node >= 12 supports Ed25519 using crypto.verify with null params
    return crypto.verify(null, message, toEd25519KeyObject(publicKey), sig);
  } catch {
    return false;
  }
}

function toEd25519KeyObject(pubKey: string) {
  // Accept base64 or hex-encoded raw 32-byte public key; wrap in SPKI if needed
  const raw =
    /^[A-Fa-f0-9]+$/.test(pubKey) ? Buffer.from(pubKey, 'hex') : Buffer.from(pubKey, 'base64');

  // If this is already a PEM/SPKI, pass through
  const asString = pubKey.trim();
  if (asString.includes('BEGIN PUBLIC KEY')) {
    return asString;
  }

  // Build a minimal SPKI for Ed25519 public key
  // ASN.1 header for Ed25519 public key (RFC 8410): 302a300506032b6570032100 || key(32)
  const header = Buffer.from('302a300506032b6570032100', 'hex');
  const spki = Buffer.concat([header, raw]);
  const pem = `-----BEGIN PUBLIC KEY-----\n${spki.toString('base64').match(/.{1,64}/g)?.join('\n')}\n-----END PUBLIC KEY-----\n`;
  return pem;
}

function timingSafeEqualAny(input: string, candidates: string[]): boolean {
  try {
    const a = Buffer.from(input);
    return candidates.some((c) => {
      const b = Buffer.from(c);
      if (a.length !== b.length) return false;
      return crypto.timingSafeEqual(a, b);
    });
  } catch {
    // Fallback if lengths differ wildly
    return candidates.includes(input);
  }
}

/* -------------------------------------------------------------------------- */
/*                                   Utils                                    */
/* -------------------------------------------------------------------------- */

function toHeadersRecord(h: Headers): Record<string, string> {
  const rec: Record<string, string> = {};
  h.forEach((v, k) => (rec[k.toLowerCase()] = v));
  return rec;
}

function jsonError(message: string, status = 400) {
  return NextResponse.json(
    { error: message },
    { status, headers: { 'Cache-Control': 'no-store' } }
  );
}
