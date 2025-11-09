"use client";

import React from 'react';
import { AnimatePresence } from 'framer-motion';
import { PageTransition } from './page-transition';
import { RouteTransitionProps } from './types';

export function RouteTransition({
  children,
  routeKey,
  variant = 'fade',
  duration = 0.3,
  className
}: RouteTransitionProps) {
  return (
    <AnimatePresence mode="wait" initial={false}>
      <PageTransition
        key={routeKey}
        variant={variant}
        duration={duration}
        className={className}
      >
        {children}
      </PageTransition>
    </AnimatePresence>
  );
}