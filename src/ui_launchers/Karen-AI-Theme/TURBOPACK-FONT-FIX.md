# Next.js Build Issue - Turbopack Google Fonts Resolution

## Problem

When using Next.js 15 with Turbopack (`--turbopack` flag), you may encounter this build error:

```
Module not found: Can't resolve '@vercel/turbopack-next/internal/font/google/font'
```

This error occurs because Turbopack has compatibility issues with the Next.js Google Fonts loader in Next.js 15.

## Solutions

### Solution 1: Remove Turbopack (Recommended)

**Update `package.json`:**
```json
{
  "scripts": {
    "dev": "next dev -p 3000"  // Remove --turbopack
  }
}
```

This uses the standard Webpack bundler, which has full compatibility with Next.js Google Fonts.

### Solution 2: Use CSS Font Loading (Alternative)

If you prefer to keep Turbopack, modify the font loading approach:

1. **Update `globals.css`:**
   Uncomment the CSS font imports at the top of the file.

2. **Update `layout.tsx`:**
   Remove the Next.js font imports and use CSS variables instead:

```tsx
// Remove these imports:
// import { Inter, Roboto_Mono } from 'next/font/google';

// Remove these font instantiations:
// const inter = Inter({...});
// const robotoMono = Roboto_Mono({...});

// Update the body className:
<body className="font-sans antialiased">
```

## Verification

After applying either solution, run:

```bash
npm run build  # Should complete successfully
npm run dev    # Should start without font errors
```

## Why This Happens

- Turbopack is Next.js's experimental bundler
- In Next.js 15, Turbopack's Google Fonts integration has compatibility issues
- The `@vercel/turbopack-next/internal/font/google/font` module path is internal and not properly resolved
- Standard Webpack handles this correctly

## Performance Impact

- **Without Turbopack**: Slightly slower builds, full compatibility
- **With Turbopack + CSS fonts**: Faster builds, manual font optimization required
- **With Turbopack + Next.js fonts**: Currently broken in Next.js 15

## Recommendation

Use Solution 1 (remove Turbopack) for production applications. Turbopack is still experimental and may have other compatibility issues. Once Turbopack has stable Google Fonts support in Next.js, you can re-enable it.