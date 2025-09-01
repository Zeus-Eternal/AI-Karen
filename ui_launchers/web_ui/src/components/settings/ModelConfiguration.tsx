'use client';

import React from 'react';

interface ModelConfigurationProps {
  modelId?: string;
  onModelChange?: (modelId: string) => void;
}

const ModelConfiguration: React.FC<ModelConfigurationProps> = ({
  modelId,
  onModelChange
}) => {
  return (
    <div className="p-4">
      <h3 className="text-lg font-semibold mb-4">Model Configuration</h3>
      <p className="text-gray-600">
        Model configuration interface is under development.
      </p>
      {modelId && (
        <p className="text-sm text-gray-500 mt-2">
          Selected Model: {modelId}
        </p>
      )}
    </div>
  );
};

export default ModelConfiguration;