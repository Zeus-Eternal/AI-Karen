import { useEffect, useRef } from 'react';
import { STICK_TO_BOTTOM_THRESHOLD } from './constants';

export function useScrollManagement(
  messages: any[],
  isLoading: boolean,
  viewportRef: React.RefObject<HTMLDivElement>,
  messagesContainerRef: React.RefObject<HTMLDivElement>
) {
  const shouldStickToBottomRef = useRef(true);

  // Scroll stickiness
  useEffect(() => {
    const viewport = viewportRef.current;
    const container = messagesContainerRef.current;
    if (!viewport) return;

    const updateStickiness = () => {
      const distanceFromBottom = viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight;
      shouldStickToBottomRef.current = distanceFromBottom < STICK_TO_BOTTOM_THRESHOLD;
    };

    updateStickiness();
    viewport.addEventListener('scroll', updateStickiness, { passive: true });

    return () => {
      viewport.removeEventListener('scroll', updateStickiness);
    };
  }, [viewportRef, messagesContainerRef]);

  useEffect(() => {
    if (shouldStickToBottomRef.current) {
      requestAnimationFrame(() => {
        scrollChatToBottom(messages.length <= 1 ? 'auto' : 'smooth');
      });
    }
  }, [messages, isLoading]);

  const scrollChatToBottom = (behavior: ScrollBehavior = 'smooth') => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    viewport.scrollTo({
      top: viewport.scrollHeight,
      behavior,
    });
  };

  return { scrollChatToBottom };
}