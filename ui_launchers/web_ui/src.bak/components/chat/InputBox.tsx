'use client';

import React from 'react';
import { ChatInput } from './ChatInput';

interface InputBoxProps {
  onSend: (message: string) => Promise<void>;
  isLoading?: boolean;
  placeholder?: string;
}

export const InputBox: React.FC<InputBoxProps> = ({ onSend, isLoading, placeholder }) => {
  return (
    <ChatInput onSubmit={onSend} isLoading={isLoading} placeholder={placeholder} />
  );
};

export default InputBox;
