import { useMemo } from 'react';
import type { AuthUser } from '@/lib/auth';
import type { ChatMessage } from '@/lib/types';
import type { UserPreferences } from './types';

type User = Partial<AuthUser> & {
  id?: string | number | null;
  user_id?: string | number | null;
  username?: string | null;
  name?: string | null;
  preferences?: {
    preferred_address_name?: string | null;
  } | null;
  full_name?: string | null;
  email?: string | null;
};

const DEFAULT_MAX_RECENT_MESSAGES = 6;
const MIN_RECENT_MESSAGES = 0;
const MAX_RECENT_MESSAGES_LIMIT = 50;

const cleanString = (value: unknown): string => {
  return typeof value === 'string' ? value.trim() : '';
};

const clampRecentMessageLimit = (value: number): number => {
  if (!Number.isFinite(value)) {
    return DEFAULT_MAX_RECENT_MESSAGES;
  }

  return Math.min(
    MAX_RECENT_MESSAGES_LIMIT,
    Math.max(MIN_RECENT_MESSAGES, Math.floor(value)),
  );
};

const getEmailLocalPart = (email: unknown): string => {
  const cleanedEmail = cleanString(email);

  if (!cleanedEmail || !cleanedEmail.includes('@')) {
    return '';
  }

  return cleanString(cleanedEmail.split('@')[0]);
};

const getFirstNameOption = (
  fullName: string,
  displayName: string | null,
): string | null => {
  return fullName.split(/\s+/).filter(Boolean)[0] || displayName || null;
};

const shouldAskForPreferredName = ({
  isAuthenticated,
  preferredAddressName,
  fullName,
  firstNameOption,
}: {
  isAuthenticated: boolean;
  preferredAddressName: string;
  fullName: string;
  firstNameOption: string | null;
}): boolean => {
  return Boolean(
    isAuthenticated &&
      !preferredAddressName &&
      fullName &&
      firstNameOption &&
      fullName.includes(' ') &&
      firstNameOption.toLowerCase() !== fullName.toLowerCase(),
  );
};

const normalizeRecentMessages = (
  messages: ChatMessage[],
  maxRecentMessages: number,
): UserPreferences['recentMessages'] => {
  const limit = clampRecentMessageLimit(maxRecentMessages);

  if (limit <= 0) {
    return [];
  }

  return messages
    .filter((message) => {
      return (
        (message.role === 'user' || message.role === 'assistant') &&
        typeof message.content === 'string' &&
        message.content.trim().length > 0
      );
    })
    .slice(-limit)
    .map((message) => ({
      role: message.role,
      content: message.content.trim(),
    }));
};

export function useUserPreferences(
  user: User | null,
  isAuthenticated: boolean,
  messages: ChatMessage[],
  maxRecentMessages: number = DEFAULT_MAX_RECENT_MESSAGES,
): UserPreferences {
  const preferredAddressName = useMemo(() => {
    return cleanString(user?.preferences?.preferred_address_name);
  }, [user?.preferences?.preferred_address_name]);

  const fullName = useMemo(() => {
    return cleanString(user?.full_name) || cleanString(user?.name);
  }, [user?.full_name, user?.name]);

  const username = useMemo(() => {
    return cleanString(user?.username);
  }, [user?.username]);

  const emailName = useMemo(() => {
    return getEmailLocalPart(user?.email);
  }, [user?.email]);

  const displayName = useMemo(() => {
    const candidate = preferredAddressName || fullName || username || emailName;

    return candidate || null;
  }, [preferredAddressName, fullName, username, emailName]);

  const firstNameOption = useMemo(() => {
    return getFirstNameOption(fullName, displayName);
  }, [fullName, displayName]);

  const shouldPromptForPreferredName = useMemo(() => {
    return shouldAskForPreferredName({
      isAuthenticated,
      preferredAddressName,
      fullName,
      firstNameOption,
    });
  }, [isAuthenticated, preferredAddressName, fullName, firstNameOption]);

  const recentMessages = useMemo(() => {
    return normalizeRecentMessages(messages, maxRecentMessages);
  }, [messages, maxRecentMessages]);

  return {
    preferredAddressName,
    fullName,
    displayName,
    firstNameOption,
    shouldPromptForPreferredName,
    recentMessages,
  };
}
