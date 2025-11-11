import { AnimationVariants } from './types';

export const animationVariants: AnimationVariants = {
  button: {
    default: {
      idle: { 
        scale: 1, 
        boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
        transition: { duration: 0.15, ease: "easeOut" }
      },
      hover: { 
        scale: 1.02, 
        boxShadow: "0 4px 8px rgba(0,0,0,0.15)",
        transition: { duration: 0.15, ease: "easeOut" }
      },
      tap: { 
        scale: 0.98,
        boxShadow: "0 1px 2px rgba(0,0,0,0.1)",
        transition: { duration: 0.1, ease: "easeInOut" }
      },
      loading: {
        scale: 1,
        opacity: 0.8,
        transition: { duration: 0.2, ease: "easeInOut" }
      }
    },
    bounce: {
      idle: { 
        scale: 1, 
        y: 0,
        transition: { type: "spring", stiffness: 300, damping: 20 }
      },
      hover: { 
        scale: 1.05, 
        y: -2,
        transition: { type: "spring", stiffness: 400, damping: 15 }
      },
      tap: { 
        scale: 0.95,
        y: 0,
        transition: { type: "spring", stiffness: 600, damping: 25 }
      }
    },
    scale: {
      idle: { 
        scale: 1,
        transition: { type: "spring", stiffness: 300, damping: 20 }
      },
      hover: { 
        scale: 1.08,
        transition: { type: "spring", stiffness: 400, damping: 15 }
      },
      tap: { 
        scale: 0.92,
        transition: { type: "spring", stiffness: 600, damping: 25 }
      }
    },
    slide: {
      idle: { 
        x: 0,
        transition: { type: "spring", stiffness: 300, damping: 20 }
      },
      hover: { 
        x: 4,
        transition: { type: "spring", stiffness: 400, damping: 15 }
      },
      tap: { 
        x: 0,
        transition: { type: "spring", stiffness: 600, damping: 25 }
      }
    }
  },
  input: {
    default: {
      idle: { 
        scale: 1,
        borderColor: "hsl(var(--border))",
        boxShadow: "0 0 0 0px hsl(var(--ring) / 0)",
        transition: { duration: 0.15, ease: "easeOut" }
      },
      focus: { 
        scale: 1.01,
        borderColor: "hsl(var(--ring))",
        boxShadow: "0 0 0 2px hsl(var(--ring) / 0.2)",
        transition: { duration: 0.15, ease: "easeOut" }
      },
      error: {
        borderColor: "hsl(var(--destructive))",
        boxShadow: "0 0 0 2px hsl(var(--destructive) / 0.2)",
        transition: { duration: 0.15, ease: "easeOut" }
      },
      success: {
        borderColor: "hsl(var(--success))",
        boxShadow: "0 0 0 2px hsl(var(--success) / 0.2)",
        transition: { duration: 0.15, ease: "easeOut" }
      }
    },
    glow: {
      idle: { 
        boxShadow: "0 0 0 0px hsl(var(--ring) / 0)",
        transition: { duration: 0.2, ease: "easeOut" }
      },
      focus: { 
        boxShadow: "0 0 0 3px hsl(var(--ring) / 0.3), 0 0 20px hsl(var(--ring) / 0.1)",
        transition: { duration: 0.2, ease: "easeOut" }
      }
    },
    shake: {
      idle: { x: 0 },
      error: {
        x: [-10, 10, -10, 10, -5, 5, 0],
        transition: { duration: 0.5, ease: "easeInOut" }
      }
    }
  },
  card: {
    lift: {
      idle: { 
        y: 0, 
        boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
        transition: { duration: 0.2, ease: "easeOut" }
      },
      hover: { 
        y: -4, 
        boxShadow: "0 8px 16px rgba(0,0,0,0.15)",
        transition: { duration: 0.2, ease: "easeOut" }
      },
      tap: { 
        y: -2,
        boxShadow: "0 4px 8px rgba(0,0,0,0.12)",
        transition: { duration: 0.1, ease: "easeInOut" }
      }
    },
    glow: {
      idle: { 
        boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
        transition: { duration: 0.2, ease: "easeOut" }
      },
      hover: { 
        boxShadow: "0 4px 8px rgba(0,0,0,0.15), 0 0 0 1px hsl(var(--ring) / 0.1)",
        transition: { duration: 0.2, ease: "easeOut" }
      }
    },
    scale: {
      idle: { 
        scale: 1,
        transition: { type: "spring", stiffness: 300, damping: 20 }
      },
      hover: { 
        scale: 1.02,
        transition: { type: "spring", stiffness: 400, damping: 15 }
      },
      tap: { 
        scale: 0.98,
        transition: { type: "spring", stiffness: 600, damping: 25 }
      }
    }
  }
};

// Reduced motion variants
export const reducedMotionVariants: AnimationVariants = {
  button: {
    default: {
      idle: { opacity: 1 },
      hover: { opacity: 0.9 },
      tap: { opacity: 0.8 },
      loading: { opacity: 0.7 }
    },
    bounce: {
      idle: { opacity: 1 },
      hover: { opacity: 0.9 },
      tap: { opacity: 0.8 }
    },
    scale: {
      idle: { opacity: 1 },
      hover: { opacity: 0.9 },
      tap: { opacity: 0.8 }
    },
    slide: {
      idle: { opacity: 1 },
      hover: { opacity: 0.9 },
      tap: { opacity: 0.8 }
    }
  },
  input: {
    default: {
      idle: { opacity: 1 },
      focus: { opacity: 1 },
      error: { opacity: 1 },
      success: { opacity: 1 }
    },
    glow: {
      idle: { opacity: 1 },
      focus: { opacity: 1 }
    },
    shake: {
      idle: { opacity: 1 },
      error: { opacity: 1 }
    }
  },
  card: {
    lift: {
      idle: { opacity: 1 },
      hover: { opacity: 0.95 },
      tap: { opacity: 0.9 }
    },
    glow: {
      idle: { opacity: 1 },
      hover: { opacity: 0.95 }
    },
    scale: {
      idle: { opacity: 1 },
      hover: { opacity: 0.95 },
      tap: { opacity: 0.9 }
    }
  }
};