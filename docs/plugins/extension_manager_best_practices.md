# Extension Manager Best Practices

- Keep extension categories focused on a single domain.
- Use breadcrumbs to provide clear navigation back to higher levels.
- Enable lazy loading for heavy components using `next/dynamic` to reduce bundle size.
- Monitor resource statistics from the sidebar to detect issues early.
- Use the feature flag `KAREN_ENABLE_EXTENSIONS` to roll out changes gradually.
