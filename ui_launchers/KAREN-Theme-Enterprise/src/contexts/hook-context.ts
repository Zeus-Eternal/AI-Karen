import { createContext } from 'react';
import type { HookContextType } from './hook-types';

export const HookContext = createContext<HookContextType | undefined>(undefined);

