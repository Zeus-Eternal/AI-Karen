import { useMemo } from 'react';
import type { ChatMessage, UserPreferences } from './types';

interface User {
  preferences?: {
    preferred_address_name?: string;
  };
  full_name?: string;
  email?: string;
}

export function useUserPreferences(
  user: User | null,
  isAuthenticated: boolean,
  messages: ChatMessage[],
  maxRecentMessages: number = 6
): UserPreferences {
  const preferredAddressName = useMemo(() =>
    typeof user?.preferences?.preferred_address_name === 'string'
      ? user.preferences.preferred_address_name.trim()
      : '', [user?.preferences?.preferred_address_name]);

  const fullName = user?.full_name?.trim() || '';
  const emailName = user?.email?.split('@')[0]?.trim() || '';

  const displayName = useMemo(() => {
    const candidate = preferredAddressName || fullName || emailName || '';
    return candidate || null;
  }, [preferredAddressName, fullName, emailName]);

  const firstNameOption = fullName.split(/\s+/).filter(Boolean)[0] || displayName || null;

  const shouldPromptForPreferredName = Boolean(
    isAuthenticated &&
    !preferredAddressName &&
    fullName &&
    firstNameOption &&
    fullName.includes(' ') &&
    firstNameOption.toLowerCase() !== fullName.toLowerCase()
  );

  const recentMessages = useMemo(() =>
    messages
      .filter((message) => message.role === 'user' || message.role === 'assistant')
      .slice(-maxRecentMessages)
      .map((message) => ({
        role: message.role,
        content: message.content,
      })), [messages, maxRecentMessages]);

  return {
    preferredAddressName,
    fullName,
    displayName,
    firstNameOption,
    shouldPromptForPreferredName,
    recentMessages,
  };
}