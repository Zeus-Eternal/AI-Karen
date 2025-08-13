'use client';

import React from 'react';

interface MetaBarProps {
  title?: string;
  children?: React.ReactNode;
}

export const MetaBar: React.FC<MetaBarProps> = ({ title = 'Chat', children }) => {
  return (
    <div className="flex items-center justify-between border-b border-border px-4 py-2">
      <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
      {children}
    </div>
  );
};

export default MetaBar;
