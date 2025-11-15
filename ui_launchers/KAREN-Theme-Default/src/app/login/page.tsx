import * as React from 'react';
import LoginPageClient from './LoginPageClient';

export default function LoginPage() {
  return (
    <React.Suspense fallback={null}>
      <LoginPageClient />
    </React.Suspense>
  );
}
