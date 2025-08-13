# Privacy Compliance

This document outlines how the system protects sensitive user data when returning memory context.

## PII Redaction

All memory queries pass text through the `PIIRedactor` utility from `StructuredLoggingService` before being returned in a `ContextHit`. The redactor scrubs common personally identifiable information (PII) patterns such as emails, phone numbers, and credit card numbers.

## Preview Field

Each `ContextHit` includes an optional `preview` field containing a shortened redacted snippet for display purposes. The full unredacted text remains stored securely on the server and is never exposed in API responses.

This approach helps maintain compliance with privacy regulations while still allowing clients to show relevant context.
