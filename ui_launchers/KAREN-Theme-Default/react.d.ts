/// <reference types="react" />
/// <reference types="react-dom" />

import * as React from 'react';

declare global {
  namespace React {
    // Re-export React types to ensure they're available globally
  }
}

export = React;
export as namespace React;