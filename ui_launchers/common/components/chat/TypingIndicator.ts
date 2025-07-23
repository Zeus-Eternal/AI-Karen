// Shared Typing Indicator Component
// Framework-agnostic typing indicator for chat interfaces

import { Theme } from '../../abstractions/types';

export interface TypingIndicatorOptions {
  showAvatar?: boolean;
  showText?: boolean;
  customText?: string;
  animationSpeed?: 'slow' | 'normal' | 'fast';
  dotCount?: number;
  size?: 'small' | 'medium' | 'large';
}

export interface TypingIndicatorState {
  isVisible: boolean;
  currentDot: number;
  animationFrame: number;
}

export class SharedTypingIndicator {
  private state: TypingIndicatorState;
  private options: TypingIndicatorOptions;
  private theme: Theme;
  private animationTimer: NodeJS.Timeout | null = null;

  constructor(
    theme: Theme,
    options: TypingIndicatorOptions = {}
  ) {
    this.theme = theme;
    this.options = {
      showAvatar: true,
      showText: true,
      customText: 'Karen is typing',
      animationSpeed: 'normal',
      dotCount: 3,
      size: 'medium',
      ...options
    };

    this.state = {
      isVisible: false,
      currentDot: 0,
      animationFrame: 0
    };
  }

  // Get current state
  getState(): TypingIndicatorState {
    return { ...this.state };
  }

  // Update state
  updateState(newState: Partial<TypingIndicatorState>): void {
    this.state = { ...this.state, ...newState };
  }

  // Show the typing indicator
  show(): void {
    if (this.state.isVisible) return;

    this.updateState({ 
      isVisible: true,
      currentDot: 0,
      animationFrame: 0
    });

    this.startAnimation();
  }

  // Hide the typing indicator
  hide(): void {
    if (!this.state.isVisible) return;

    this.updateState({ isVisible: false });
    this.stopAnimation();
  }

  // Toggle visibility
  toggle(): void {
    if (this.state.isVisible) {
      this.hide();
    } else {
      this.show();
    }
  }

  // Start the dot animation
  private startAnimation(): void {
    if (this.animationTimer) return;

    const speed = this.getAnimationSpeed();
    
    this.animationTimer = setInterval(() => {
      const nextDot = (this.state.currentDot + 1) % (this.options.dotCount! + 1);
      const nextFrame = this.state.animationFrame + 1;
      
      this.updateState({
        currentDot: nextDot,
        animationFrame: nextFrame
      });
    }, speed);
  }

  // Stop the animation
  private stopAnimation(): void {
    if (this.animationTimer) {
      clearInterval(this.animationTimer);
      this.animationTimer = null;
    }
  }

  // Get animation speed in milliseconds
  private getAnimationSpeed(): number {
    const speeds = {
      slow: 800,
      normal: 600,
      fast: 400
    };

    return speeds[this.options.animationSpeed!] || speeds.normal;
  }

  // Get dot size based on options
  private getDotSize(): string {
    const sizes = {
      small: '6px',
      medium: '8px',
      large: '10px'
    };

    return sizes[this.options.size!] || sizes.medium;
  }

  // Get container size based on options
  private getContainerSize(): { width: string; height: string } {
    const sizes = {
      small: { width: '40px', height: '20px' },
      medium: { width: '50px', height: '24px' },
      large: { width: '60px', height: '28px' }
    };

    return sizes[this.options.size!] || sizes.medium;
  }

  // Generate dots for display
  getDots(): Array<{ active: boolean; delay: number }> {
    const dots = [];
    
    for (let i = 0; i < this.options.dotCount!; i++) {
      dots.push({
        active: i <= this.state.currentDot,
        delay: i * 200 // Stagger the animation
      });
    }
    
    return dots;
  }

  // Get CSS classes
  getCssClasses(): string[] {
    const classes = ['karen-typing-indicator'];
    
    if (this.state.isVisible) {
      classes.push('karen-typing-indicator-visible');
    }
    
    classes.push(`karen-typing-indicator-${this.options.size}`);
    classes.push(`karen-typing-indicator-${this.options.animationSpeed}`);
    
    return classes;
  }

  // Get inline styles for container
  getContainerStyles(): Record<string, string> {
    const containerSize = this.getContainerSize();
    
    return {
      display: this.state.isVisible ? 'flex' : 'none',
      alignItems: 'center',
      gap: this.theme.spacing.sm,
      padding: this.theme.spacing.sm,
      backgroundColor: this.theme.colors.surface,
      borderRadius: this.theme.borderRadius,
      border: `1px solid ${this.theme.colors.border}`,
      ...containerSize
    };
  }

  // Get inline styles for dots container
  getDotsContainerStyles(): Record<string, string> {
    return {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '4px',
      minWidth: '30px'
    };
  }

  // Get inline styles for individual dots
  getDotStyles(isActive: boolean): Record<string, string> {
    const dotSize = this.getDotSize();
    
    return {
      width: dotSize,
      height: dotSize,
      borderRadius: '50%',
      backgroundColor: isActive ? this.theme.colors.primary : this.theme.colors.border,
      transition: 'all 0.3s ease',
      opacity: isActive ? '1' : '0.3',
      transform: isActive ? 'scale(1.2)' : 'scale(1)'
    };
  }

  // Get text styles
  getTextStyles(): Record<string, string> {
    return {
      fontSize: this.theme.typography.fontSize.sm,
      color: this.theme.colors.textSecondary,
      fontStyle: 'italic',
      marginLeft: this.theme.spacing.xs
    };
  }

  // Get avatar styles
  getAvatarStyles(): Record<string, string> {
    const avatarSize = this.options.size === 'small' ? '20px' : 
                     this.options.size === 'large' ? '28px' : '24px';
    
    return {
      width: avatarSize,
      height: avatarSize,
      borderRadius: '50%',
      backgroundColor: this.theme.colors.primary,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'white',
      fontSize: this.theme.typography.fontSize.xs,
      flexShrink: '0'
    };
  }

  // Generate CSS keyframes for animation
  generateCssKeyframes(): string {
    return `
      @keyframes karen-typing-dot {
        0%, 60%, 100% {
          transform: scale(1);
          opacity: 0.3;
        }
        30% {
          transform: scale(1.2);
          opacity: 1;
        }
      }
      
      @keyframes karen-typing-pulse {
        0%, 100% {
          opacity: 1;
        }
        50% {
          opacity: 0.5;
        }
      }
      
      .karen-typing-indicator-dot {
        animation: karen-typing-dot 1.4s infinite ease-in-out;
      }
      
      .karen-typing-indicator-dot:nth-child(1) {
        animation-delay: -0.32s;
      }
      
      .karen-typing-indicator-dot:nth-child(2) {
        animation-delay: -0.16s;
      }
      
      .karen-typing-indicator-text {
        animation: karen-typing-pulse 2s infinite ease-in-out;
      }
    `;
  }

  // Get render data
  getRenderData(): TypingIndicatorRenderData {
    return {
      state: this.getState(),
      options: this.options,
      dots: this.getDots(),
      cssClasses: this.getCssClasses(),
      styles: {
        container: this.getContainerStyles(),
        dotsContainer: this.getDotsContainerStyles(),
        text: this.getTextStyles(),
        avatar: this.getAvatarStyles()
      },
      theme: this.theme,
      cssKeyframes: this.generateCssKeyframes(),
      handlers: {
        show: () => this.show(),
        hide: () => this.hide(),
        toggle: () => this.toggle()
      }
    };
  }

  // Update theme
  updateTheme(theme: Theme): void {
    this.theme = theme;
  }

  // Update options
  updateOptions(newOptions: Partial<TypingIndicatorOptions>): void {
    this.options = { ...this.options, ...newOptions };
    
    // Restart animation if visible to apply new settings
    if (this.state.isVisible) {
      this.stopAnimation();
      this.startAnimation();
    }
  }

  // Destroy the indicator
  destroy(): void {
    this.stopAnimation();
  }
}

// Supporting interfaces
export interface TypingIndicatorRenderData {
  state: TypingIndicatorState;
  options: TypingIndicatorOptions;
  dots: Array<{ active: boolean; delay: number }>;
  cssClasses: string[];
  styles: {
    container: Record<string, string>;
    dotsContainer: Record<string, string>;
    text: Record<string, string>;
    avatar: Record<string, string>;
  };
  theme: Theme;
  cssKeyframes: string;
  handlers: {
    show: () => void;
    hide: () => void;
    toggle: () => void;
  };
}

// Utility functions
export function createTypingIndicator(
  theme: Theme,
  options: TypingIndicatorOptions = {}
): SharedTypingIndicator {
  return new SharedTypingIndicator(theme, options);
}

export function getTypingIndicatorHtml(renderData: TypingIndicatorRenderData): string {
  const { state, options, dots, styles } = renderData;
  
  if (!state.isVisible) return '';

  let html = `<div class="${renderData.cssClasses.join(' ')}" style="${Object.entries(styles.container).map(([k, v]) => `${k}: ${v}`).join('; ')}">`;
  
  // Avatar
  if (options.showAvatar) {
    html += `<div style="${Object.entries(styles.avatar).map(([k, v]) => `${k}: ${v}`).join('; ')}">K</div>`;
  }
  
  // Dots
  html += `<div style="${Object.entries(styles.dotsContainer).map(([k, v]) => `${k}: ${v}`).join('; ')}">`;
  dots.forEach((dot, index) => {
    const dotStyles = Object.entries({
      width: '8px',
      height: '8px',
      borderRadius: '50%',
      backgroundColor: dot.active ? renderData.theme.colors.primary : renderData.theme.colors.border,
      transition: 'all 0.3s ease',
      opacity: dot.active ? '1' : '0.3'
    }).map(([k, v]) => `${k}: ${v}`).join('; ');
    
    html += `<div class="karen-typing-indicator-dot" style="${dotStyles}"></div>`;
  });
  html += '</div>';
  
  // Text
  if (options.showText) {
    html += `<span class="karen-typing-indicator-text" style="${Object.entries(styles.text).map(([k, v]) => `${k}: ${v}`).join('; ')}">${options.customText}</span>`;
  }
  
  html += '</div>';
  
  return html;
}

export function getTypingIndicatorDuration(options: TypingIndicatorOptions): number {
  const speeds = {
    slow: 800,
    normal: 600,
    fast: 400
  };
  
  const speed = speeds[options.animationSpeed || 'normal'];
  const dotCount = options.dotCount || 3;
  
  return speed * (dotCount + 1); // Full cycle duration
}