import * as React from 'react';

function SimpleLoading() {
  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg px-8 pt-6 pb-8 mb-4">
        <h1 className="text-2xl font-bold text-center mb-6 text-gray-800 dark:text-white">
          Loading...
        </h1>
      </div>
    </div>
  );
}

// Dynamically import the actual providers component only on the client side
const DynamicProviders = React.lazy(() => import('./providers-inner').then(mod => ({ default: mod.Providers })));

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <React.Suspense fallback={<SimpleLoading />}>
      <DynamicProviders>
        {children}
      </DynamicProviders>
    </React.Suspense>
  );
}
