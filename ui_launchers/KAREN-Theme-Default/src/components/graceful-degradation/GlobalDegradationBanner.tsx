
"use client";

import React from "react";
import { useFeatureFlag } from "../../lib/graceful-degradation/feature-flags";
import { ExtensionFeatureFlags } from "../../lib/graceful-degradation/feature-flags";

const flagNames = [
  "extensionSystem",
  "backgroundTasks",
  "modelProviderIntegration",
  "extensionHealth",
  "extensionAuth",
];

const serviceDisplayNames: Record<string, string> = {
  extensionSystem: "Extension System",
  backgroundTasks: "Background Tasks",
  modelProviderIntegration: "Model Provider Integration",
  extensionHealth: "Extension Health Monitoring",
  extensionAuth: "Extension Authentication",
};

const DegradedService: React.FC<{ flagName: keyof ExtensionFeatureFlags }> = ({ flagName }) => {
  const { isEnabled } = useFeatureFlag(flagName);

  if (isEnabled) {
    return null;
  }

  return (
    <li className="text-sm">
      - {serviceDisplayNames[flagName] || flagName}: Operations may be limited or data may be stale.
    </li>
  );
};

export const GlobalDegradationBanner: React.FC = () => {
  const flags = flagNames.map(flagName => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const { isEnabled } = useFeatureFlag(flagName);
    return { flagName, isEnabled };
  });

  const unhealthyServices = flags.filter(f => !f.isEnabled);

  if (unhealthyServices.length === 0) {
    return null;
  }

  return (
    <div
      className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4"
      role="alert"
    >
      <p className="font-bold">System Degradation</p>
      <p>
        Some services are currently experiencing issues. You may encounter errors or see stale data.
      </p>
      <ul className="mt-2 list-disc list-inside">
        {unhealthyServices.map(({ flagName }) => (
          <DegradedService key={flagName} flagName={flagName as keyof ExtensionFeatureFlags} />
        ))}
      </ul>
    </div>
  );
};
