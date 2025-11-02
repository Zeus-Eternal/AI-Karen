/**
 * Extension Page Fallback Component
 * 
 * Shown when no extension matches the current route
 */
'use client';

import Link from 'next/link';
import { useExtensionRoutes } from '@/lib/extensions/hooks';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { ArrowLeft, Puzzle, Search } from 'lucide-react';
interface ExtensionPageFallbackProps {
  extensionPath?: string;
}
export function ExtensionPageFallback({ extensionPath }: ExtensionPageFallbackProps) {
  const routes = useExtensionRoutes();
  const availableExtensions = routes.reduce((acc, route) => {
    if (!acc.find(ext => ext.extensionId === route.extensionId)) {
      acc.push({
        extensionId: route.extensionId,
        path: route.path,
        name: route.extensionId.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
      });
    }
    return acc;
  }, [] as Array<{ extensionId: string; path: string; name: string }>);
  return (
    <div className="max-w-4xl mx-auto space-y-6 sm:w-auto md:w-full">
      {/* Header */}
      <div className="text-center">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4 sm:w-auto md:w-full">
          <Puzzle className="w-8 h-8 text-gray-400 sm:w-auto md:w-full" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Extension Not Found</h1>
        <p className="text-gray-600">
          {extensionPath 
            ? `The extension page "${extensionPath}" could not be found.`
            : 'The requested extension page could not be found.'
          }
        </p>
      </div>
      {/* Available Extensions */}
      {availableExtensions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="w-5 h-5 sm:w-auto md:w-full" />
              Available Extensions
            </CardTitle>
            <CardDescription>
              Here are the extensions currently available in your system
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {availableExtensions.map((extension) => (
                <Link
                  key={extension.extensionId}
                  href={extension.path}
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors sm:p-4 md:p-6"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center sm:w-auto md:w-full">
                      <Puzzle className="w-4 h-4 text-blue-600 sm:w-auto md:w-full" />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">{extension.name}</h3>
                      <p className="text-sm text-gray-500 md:text-base lg:text-lg">{extension.path}</p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      {/* No Extensions Available */}
      {availableExtensions.length === 0 && (
        <Card>
          <CardContent className="text-center py-8">
            <Puzzle className="w-12 h-12 text-gray-300 mx-auto mb-4 sm:w-auto md:w-full" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Extensions Available</h3>
            <p className="text-gray-600 mb-4">
              There are currently no extensions installed or active in your system.
            </p>
            <button asChild aria-label="Button">
              <Link href="/extensions">
                View Extension Dashboard
              </Link>
            </Button>
          </CardContent>
        </Card>
      )}
      {/* Actions */}
      <div className="flex justify-center gap-4">
        <button variant="outline" asChild aria-label="Button">
          <Link href="/extensions" className="flex items-center gap-2">
            <ArrowLeft className="w-4 h-4 sm:w-auto md:w-full" />
            Back to Extensions
          </Link>
        </Button>
        <button asChild aria-label="Button">
          <Link href="/">
            Go to Dashboard
          </Link>
        </Button>
      </div>
      {/*  (only in development) */}
      {process.env.NODE_ENV === 'development' && (
        <Card className="bg-gray-50">
          <CardHeader>
            <CardTitle className="text-sm md:text-base lg:text-lg">rmation</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm space-y-2 md:text-base lg:text-lg">
              <div>
                <strong>Requested Path:</strong> {extensionPath || 'Unknown'}
              </div>
              <div>
                <strong>Available Routes:</strong> {routes.length}
              </div>
              <div>
                <strong>Extension IDs:</strong> {availableExtensions.map(e => e.extensionId).join(', ') || 'None'}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
export default ExtensionPageFallback;
