import { useCallback, useEffect, useRef } from 'react';
import type { ChatMessage } from '@/lib/types';
import { STICK_TO_BOTTOM_THRESHOLD } from './constants';

interface UseScrollManagementResult {
  scrollChatToBottom: (behavior?: ScrollBehavior) => void;
}

const getDistanceFromBottom = (viewport: HTMLDivElement): number => {
  return viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight;
};

const getScrollBehaviorForMessageCount = (
  messageCount: number,
): ScrollBehavior => {
  /*
   * The first render should jump into place instead of animating an empty view.
   * Later updates can scroll smoothly so streaming/new messages feel natural.
   */
  return messageCount <= 1 ? 'auto' : 'smooth';
};

export function useScrollManagement(
  messages: ChatMessage[],
  isLoading: boolean,
  viewportRef: React.RefObject<HTMLDivElement>,
  messagesContainerRef: React.RefObject<HTMLDivElement>,
): UseScrollManagementResult {
  const shouldStickToBottomRef = useRef(true);
  const animationFrameRef = useRef<number | null>(null);

  const cancelPendingScroll = useCallback(() => {
    if (animationFrameRef.current === null || typeof window === 'undefined') {
      return;
    }

    window.cancelAnimationFrame(animationFrameRef.current);
    animationFrameRef.current = null;
  }, []);

  const scrollChatToBottom = useCallback(
    (behavior: ScrollBehavior = 'smooth') => {
      const viewport = viewportRef.current;

      if (!viewport) {
        return;
      }

      viewport.scrollTo({
        top: viewport.scrollHeight,
        behavior,
      });
    },
    [viewportRef],
  );

  useEffect(() => {
    const viewport = viewportRef.current;

    if (!viewport) {
      return undefined;
    }

    const updateStickiness = () => {
      /*
       * Stickiness protects the reader. If they scroll up to inspect earlier
       * messages, streaming tokens should not keep yanking them back down.
       */
      const distanceFromBottom = getDistanceFromBottom(viewport);
      shouldStickToBottomRef.current =
        distanceFromBottom < STICK_TO_BOTTOM_THRESHOLD;
    };

    updateStickiness();

    viewport.addEventListener('scroll', updateStickiness, { passive: true });

    return () => {
      viewport.removeEventListener('scroll', updateStickiness);
    };
  }, [viewportRef]);

  useEffect(() => {
    if (!shouldStickToBottomRef.current || typeof window === 'undefined') {
      return undefined;
    }

    cancelPendingScroll();

    /*
     * Wait one animation frame so React has committed the new message DOM.
     * This matters during streaming where content height changes frequently.
     */
    animationFrameRef.current = window.requestAnimationFrame(() => {
      scrollChatToBottom(getScrollBehaviorForMessageCount(messages.length));
      animationFrameRef.current = null;
    });

    return () => {
      cancelPendingScroll();
    };
  }, [
    cancelPendingScroll,
    isLoading,
    messages.length,
    scrollChatToBottom,
  ]);

  useEffect(() => {
    const container = messagesContainerRef.current;

    if (!container || typeof ResizeObserver === 'undefined') {
      return undefined;
    }

    /*
     * Message cards can grow after the message array changes, for example:
     * markdown renders, code blocks hydrate, images load, or streamed content
     * wraps onto new lines. ResizeObserver keeps the bottom pinned only when
     * the user has not intentionally scrolled away.
     */
    const observer = new ResizeObserver(() => {
      if (!shouldStickToBottomRef.current) {
        return;
      }

      cancelPendingScroll();

      if (typeof window !== 'undefined') {
        animationFrameRef.current = window.requestAnimationFrame(() => {
          scrollChatToBottom('auto');
          animationFrameRef.current = null;
        });
      }
    });

    observer.observe(container);

    return () => {
      observer.disconnect();
      cancelPendingScroll();
    };
  }, [cancelPendingScroll, messagesContainerRef, scrollChatToBottom]);

  return { scrollChatToBottom };
}
