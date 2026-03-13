import LoginPageClient from './LoginPageClient';
import { Suspense } from 'react';

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="w-full max-w-md mx-auto">
        <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg px-8 pt-6 pb-8 mb-4">
          <h1 className="text-2xl font-bold text-center mb-6 text-gray-800 dark:text-white">
            Loading...
          </h1>
          <div>Loading...</div>
        </div>
      </div>
    }>
      <LoginPageClient />
    </Suspense>
  );
}
