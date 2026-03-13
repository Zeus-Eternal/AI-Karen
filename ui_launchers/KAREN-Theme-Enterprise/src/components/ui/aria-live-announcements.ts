"use client";

import { useCallback, useEffect, useRef, useState } from 'react';

type PolitenessSetting = 'polite' | 'assertive';

export interface UseAriaAnnouncementsOptions {
  defaultPoliteness?: PolitenessSetting;
  clearDelay?: number;
}

export interface AriaAnnouncements {
  announce: (message: string, politeness?: PolitenessSetting) => void;
  clearAnnouncements: () => void;
  politeMessage: string;
  assertiveMessage: string;
}

export const useAriaAnnouncements = (
  options: UseAriaAnnouncementsOptions = {}
): AriaAnnouncements => {
  const { defaultPoliteness = 'polite', clearDelay = 1000 } = options;
  const [politeMessage, setPoliteMessage] = useState('');
  const [assertiveMessage, setAssertiveMessage] = useState('');
  const politeTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const assertiveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearAnnouncements = useCallback(() => {
    setPoliteMessage('');
    setAssertiveMessage('');
    if (politeTimeoutRef.current) clearTimeout(politeTimeoutRef.current);
    if (assertiveTimeoutRef.current) clearTimeout(assertiveTimeoutRef.current);
  }, []);

  const announce = useCallback(
    (message: string, politeness: PolitenessSetting = defaultPoliteness) => {
      if (politeness === 'assertive') {
        if (assertiveTimeoutRef.current) {
          clearTimeout(assertiveTimeoutRef.current);
        }

        setAssertiveMessage(message);

        assertiveTimeoutRef.current = setTimeout(() => {
          setAssertiveMessage('');
        }, clearDelay);
        return;
      }

      if (politeTimeoutRef.current) {
        clearTimeout(politeTimeoutRef.current);
      }

      setPoliteMessage(message);

      politeTimeoutRef.current = setTimeout(() => {
        setPoliteMessage('');
      }, clearDelay);
    },
    [clearDelay, defaultPoliteness]
  );

  useEffect(() => () => {
    if (politeTimeoutRef.current) clearTimeout(politeTimeoutRef.current);
    if (assertiveTimeoutRef.current) clearTimeout(assertiveTimeoutRef.current);
  }, []);

  return {
    announce,
    clearAnnouncements,
    politeMessage,
    assertiveMessage,
  };
};
