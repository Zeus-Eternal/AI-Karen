'use client';

import * as React from 'react';
import { useState, useEffect, useCallback } from 'react';
import { KAREN_SUGGESTED_FACTS_LS_KEY } from '@/lib/constants';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { MessageSquarePlus } from 'lucide-react';
/**
 * @file NotificationsSection.tsx
 * @description Displays dynamically suggested facts from Karen AI in the Comms Center.
 */

declare global {
  interface WindowEventMap {
    'karen-suggested-facts-updated': CustomEvent<unknown>;
  }
}

const getSuggestedFactsFromStorage = (): string[] => {
  if (typeof window === 'undefined') {
    return [];
  }

  try {
    const storedFacts = window.localStorage.getItem(KAREN_SUGGESTED_FACTS_LS_KEY);
    if (!storedFacts) {
      return [];
    }

    const parsedFacts = JSON.parse(storedFacts);
    return Array.isArray(parsedFacts) ? parsedFacts : [];
  } catch (error) {
    console.warn('Failed to read suggested facts from localStorage.', error);
    return [];
  }
};

export default function NotificationsSection() {
  const [suggestedFacts, setSuggestedFacts] = useState<string[]>(() => getSuggestedFactsFromStorage());
  const alertStyling = {
    variant: 'default' as const,
    className: 'bg-primary/5 border-primary/20',
  };
  const loadSuggestedFacts = useCallback(() => {
    setSuggestedFacts(getSuggestedFactsFromStorage());
  }, []);

  useEffect(() => {
    const handleStorageChange = (event: StorageEvent) => {
      if (event.key === KAREN_SUGGESTED_FACTS_LS_KEY) {
        loadSuggestedFacts();
      }
    };
    const handleFactsUpdated = (_event: CustomEvent<unknown>) => {
      loadSuggestedFacts();
    };
    window.addEventListener('karen-suggested-facts-updated', handleFactsUpdated);
    window.addEventListener('storage', handleStorageChange);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('karen-suggested-facts-updated', handleFactsUpdated);
    };
  }, [loadSuggestedFacts]);
  return (
    <div className="p-4 border rounded-lg bg-card text-card-foreground shadow-sm space-y-3 sm:p-4 md:p-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Suggested Facts from Karen</h3>
      </div>
      {suggestedFacts.length === 0 ? (
        <p className="text-sm text-muted-foreground md:text-base lg:text-lg">No new facts suggested by Karen recently.</p>
      ) : (
        <>
          <Alert {...alertStyling}>
            <MessageSquarePlus className="h-4 w-4 !text-primary/80 " />
            <AlertTitle className="text-sm font-semibold text-primary md:text-base lg:text-lg">Review Karen&rsquo;s Suggestions</AlertTitle>
            <AlertDescription className="text-xs text-primary/90 sm:text-sm md:text-base">
              Karen has identified these new pieces of information from your conversations. You can review, confirm, or dismiss them in <strong>Settings &gt; Facts</strong> to help her remember them accurately.
            </AlertDescription>
          </Alert>
          <ul className="list-disc list-inside pl-2 space-y-1 text-sm text-muted-foreground max-h-60 overflow-y-auto border p-3 rounded-md bg-muted/20 md:text-base lg:text-lg">
            {suggestedFacts.map((fact, index) => (
              <li key={`${index}-${fact.slice(0,10)}`} className="truncate hover:whitespace-normal py-0.5">
                {fact}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
