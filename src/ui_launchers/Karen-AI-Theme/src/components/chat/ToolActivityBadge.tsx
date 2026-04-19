"use client";

import React from 'react';

interface ToolActivityBadgeProps {
  toolName: string;
  status?: 'idle' | 'in_progress' | 'completed' | 'failed';
  executionTime?: number;
}

export function ToolActivityBadge({
  toolName,
  status = 'idle',
  executionTime
}: ToolActivityBadgeProps) {
  if (status === 'idle') {
    return null;
  }

  const statusColors = {
    in_progress: '#2196F3',
    completed: '#4CAF50',
    failed: '#F44336'
  };

  return (
    <div className="tool-activity-badge" style={{ borderColor: statusColors[status] }}>
      <div className="tool-name">{toolName}</div>
      {status === 'in_progress' && (
        <div className="status-indicator in-progress">
          <span className="spinner">⏳</span>
        </div>
      )}
      {status === 'completed' && executionTime && (
        <div className="execution-time">
          {executionTime}ms
        </div>
      )}
      {status === 'failed' && (
        <div className="status-indicator failed">
          ❌
        </div>
      )}
    </div>
  );
}
