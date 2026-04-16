import { useEffect, useRef } from 'react';

export function useGreetingSystem(
  isAuthLoading: boolean,
  isAuthenticated: boolean,
  user: any,
  messages: any[],
  setMessages: React.Dispatch<React.SetStateAction<any[]>>
) {
  // Dynamic greeting system
  useEffect(() => {
    if (isAuthLoading) return;

    const generateGreeting = () => {
      if (isAuthenticated && user) {
        const preferredAddressName =
          typeof user?.preferences?.preferred_address_name === 'string'
            ? user.preferences.preferred_address_name.trim()
            : '';
        const fullName = user?.full_name?.trim() || '';
        const displayName = (() => {
          const candidate = preferredAddressName || fullName || user?.email?.split('@')[0]?.trim() || '';
          return candidate || null;
        })();

        const firstNameOption = fullName.split(/\s+/).filter(Boolean)[0] || displayName || null;
        const shouldPromptForPreferredName = Boolean(
          isAuthenticated &&
          !preferredAddressName &&
          fullName &&
          firstNameOption &&
          fullName.includes(' ') &&
          firstNameOption.toLowerCase() !== fullName.toLowerCase()
        );

        if (displayName) {
          if (shouldPromptForPreferredName && firstNameOption) {
            return `Hello there! I'm Karen. ${fullName}, how may I assist you today? Would you rather I address you as ${firstNameOption} or ${fullName}?`;
          } else {
            return `Hello there! I'm Karen. ${displayName}, how may I assist you today?`;
          }
        }
      }

      return "Hello! I'm Karen, your intelligent assistant. How can I help you today?";
    };

    const greeting = generateGreeting();

    setMessages((currentMessages) => {
      // Don't add greeting if we already have messages (e.g. from history load)
      if (currentMessages.length > 0) {
        return currentMessages;
      }

      const shouldPromptForPreferredName = isAuthenticated && user &&
        typeof user?.preferences?.preferred_address_name === 'string' &&
        user.preferences.preferred_address_name.trim() === '' &&
        user?.full_name?.trim() &&
        user.full_name.includes(' ');

      return [
        {
          id: 'karen-initial-' + Date.now(),
          role: 'assistant',
          content: greeting,
          timestamp: new Date(),
          status: 'completed',
          metadata: shouldPromptForPreferredName ? {
            addressPreferencePrompt: true,
            addressOptions: [
              user.full_name.split(/\s+/).filter(Boolean)[0],
              user.full_name
            ],
          } : undefined,
        },
      ];
    });
  }, [isAuthenticated, isAuthLoading, user, setMessages]);
}