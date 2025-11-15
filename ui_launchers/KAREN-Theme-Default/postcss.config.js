export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
    // Add CSS minification in production
    ...(process.env.NODE_ENV === 'production'
      ? {
          cssnano: {
            preset: [
              'default',
              {
                discardComments: {
                  removeAll: true,
                },
                // Reduce calc() precision
                calc: {
                  precision: 5,
                },
                // Merge duplicate rules
                mergeLonghand: true,
                mergeRules: true,
                // Minify selectors
                minifySelectors: true,
                // Normalize whitespace
                normalizeWhitespace: true,
                // Remove duplicates
                discardDuplicates: true,
                // Minify gradients
                minifyGradients: true,
              },
            ],
          },
        }
      : {}),
  },
};
