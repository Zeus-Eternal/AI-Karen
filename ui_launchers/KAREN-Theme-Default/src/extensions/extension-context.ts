import { createContext } from 'react';

import type { ExtensionAction, ExtensionState } from './types';

export const ExtensionContext = createContext<
  { state: ExtensionState; dispatch: React.Dispatch<ExtensionAction> } | undefined
>(undefined);

