import { type Variants, type Transition } from 'framer-motion';

export function createStaticVariants(variants: Variants): Variants {
  const staticVariants: Variants = {};
  Object.keys(variants).forEach(key => {
    staticVariants[key] = {
      ...variants[key],
      transition: { duration: 0 },
    };
  });
  return staticVariants;
}

export function createTransition(
  reducedMotion: boolean,
  animationsEnabled: boolean,
  transition?: Transition
): Transition {
  if (reducedMotion || !animationsEnabled) {
    return { duration: 0 };
  }
  return transition || {};
}