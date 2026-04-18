import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageBubble } from '../MessageBubble';
import type { ChatMessage } from '@/lib/types';

interface MessagesAreaProps {
  messages: ChatMessage[];
  onActionClick: (action: any) => void;
  viewportRef: React.RefObject<HTMLDivElement>;
  messagesContainerRef: React.RefObject<HTMLDivElement>;
}

export function MessagesArea({
  messages,
  onActionClick,
  viewportRef,
  messagesContainerRef
}: MessagesAreaProps) {
  return (
    <ScrollArea className="flex-1 p-4 md:p-6" viewportRef={viewportRef}>
      <div ref={messagesContainerRef} className="w-full space-y-1 pb-4">
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            onActionClick={onActionClick}
          />
        ))}
      </div>
    </ScrollArea>
  );
}