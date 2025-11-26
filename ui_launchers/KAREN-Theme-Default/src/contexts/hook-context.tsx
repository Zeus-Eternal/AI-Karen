"use client";

import { createContext } from 'react';
import { HookContextType } from './hook-types';

export const HookContext = createContext<HookContextType | undefined>(undefined);