import { useEffect } from 'react';
import type { ChatMessage } from '@/lib/types';
import type { AuthUser } from '@/lib/auth';

export type ChatGreetingUser = Partial<AuthUser> & {
  id?: string | number | null;
  user_id?: string | number | null;
  username?: string | null;
  email?: string | null;
  full_name?: string | null;
  name?: string | null;
  preferences?: {
    preferred_address_name?: string | null;
  } | null;
};

interface GreetingIdentity {
  preferredAddressName: string;
  fullName: string;
  username: string;
  emailLocalPart: string;
  displayName: string | null;
  firstNameOption: string | null;
  shouldPromptForPreferredName: boolean;
}

const DEFAULT_GUEST_GREETING =
  "Hello! I'm Karen, your intelligent assistant. How can I help you today?";

const INITIAL_GREETING_ID_PREFIX = 'karen-initial-';

const cleanString = (value: unknown): string => {
  return typeof value === 'string' ? value.trim() : '';
};

const getEmailLocalPart = (email: unknown): string => {
  const cleanedEmail = cleanString(email);

  if (!cleanedEmail || !cleanedEmail.includes('@')) {
    return '';
  }

  return cleanString(cleanedEmail.split('@')[0]);
};

const getUserStableId = (user: ChatGreetingUser | null | undefined): string => {
  const rawId = user?.id ?? user?.user_id ?? user?.username ?? user?.email ?? 'guest';

  if (typeof rawId === 'string' || typeof rawId === 'number') {
    return String(rawId).trim() || 'guest';
  }

  return 'guest';
};

const buildGreetingMessageId = (
  user: ChatGreetingUser | null | undefined,
): string => {
  const userId = getUserStableId(user);
  const timestamp = typeof window !== 'undefined' ? Date.now() : 0;

  return `${INITIAL_GREETING_ID_PREFIX}${userId}-${timestamp}`;
};

const hasInitialGreeting = (messages: ChatMessage[]): boolean => {
  return messages.some((message) => {
    return (
      typeof message?.id === 'string' &&
      message.id.startsWith(INITIAL_GREETING_ID_PREFIX)
    );
  });
};

const resolveGreetingIdentity = (
  isAuthenticated: boolean,
  user: ChatGreetingUser | null | undefined,
): GreetingIdentity => {
  if (!isAuthenticated || !user) {
    return {
      preferredAddressName: '',
      fullName: '',
      username: '',
      emailLocalPart: '',
      displayName: null,
      firstNameOption: null,
      shouldPromptForPreferredName: false,
    };
  }

  const preferredAddressName = cleanString(
    user.preferences?.preferred_address_name,
  );
  const fullName = cleanString(user.full_name) || cleanString(user.name);
  const username = cleanString(user.username);
  const emailLocalPart = getEmailLocalPart(user.email);

  const displayName =
    preferredAddressName || fullName || username || emailLocalPart || null;

  const firstNameOption =
    fullName.split(/\s+/).filter(Boolean)[0] || displayName || null;

  const shouldPromptForPreferredName = Boolean(
    !preferredAddressName &&
      fullName &&
      firstNameOption &&
      fullName.includes(' ') &&
      firstNameOption.toLowerCase() !== fullName.toLowerCase(),
  );

  return {
    preferredAddressName,
    fullName,
    username,
    emailLocalPart,
    displayName,
    firstNameOption,
    shouldPromptForPreferredName,
  };
};

const generateGreeting = (
  isAuthenticated: boolean,
  user: ChatGreetingUser | null | undefined,
): {
  content: string;
  metadata?: Record<string, unknown>;
} => {
  const identity = resolveGreetingIdentity(isAuthenticated, user);

  if (!identity.displayName) {
    return {
      content: DEFAULT_GUEST_GREETING,
    };
  }

  if (
    identity.shouldPromptForPreferredName &&
    identity.fullName &&
    identity.firstNameOption
  ) {
    return {
      content: `Hello there! I'm Karen. ${identity.fullName}, how may I assist you today? Would you rather I address you as ${identity.firstNameOption} or ${identity.fullName}?`,
      metadata: {
        addressPreferencePrompt: true,
        addressOptions: [identity.firstNameOption, identity.fullName],
      },
    };
  }

  return {
    content: `Hello there! I'm Karen. ${identity.displayName}, how may I assist you today?`,
  };
};

export function useGreetingSystem(
  isAuthLoading: boolean,
  isAuthenticated: boolean,
  user: ChatGreetingUser | null | undefined,
  messages: ChatMessage[],
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>,
) {
  useEffect(() => {
    if (isAuthLoading) {
      return;
    }

    if (messages.length > 0 || hasInitialGreeting(messages)) {
      return;
    }

    setMessages((currentMessages) => {
      if (currentMessages.length > 0 || hasInitialGreeting(currentMessages)) {
        return currentMessages;
      }

      const greeting = generateGreeting(isAuthenticated, user);

      return [
        {
          id: buildGreetingMessageId(user),
          role: 'assistant',
          content: greeting.content,
          timestamp: new Date(),
          status: 'completed',
          metadata: greeting.metadata,
        },
      ];
    });
  }, [isAuthenticated, isAuthLoading, messages, user, setMessages]);
}
