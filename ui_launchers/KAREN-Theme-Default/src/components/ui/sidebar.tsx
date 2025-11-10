'use client';

import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export type SidebarContextValue = {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
};

const SidebarContext = React.createContext<SidebarContextValue | undefined>(undefined);

function useSidebar() {
  const context = React.useContext(SidebarContext);
  if (!context) {
    throw new Error('useSidebar must be used within a SidebarProvider');
  }
  return context;
}

export interface SidebarProviderProps {
  defaultOpen?: boolean;
  children: React.ReactNode;
}

function SidebarProvider({ defaultOpen = true, children }: SidebarProviderProps) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen);

  const open = React.useCallback(() => setIsOpen(true), []);
  const close = React.useCallback(() => setIsOpen(false), []);
  const toggle = React.useCallback(() => setIsOpen(prev => !prev), []);

  const value = React.useMemo(
    () => ({
      isOpen,
      open,
      close,
      toggle,
    }),
    [isOpen, open, close, toggle],
  );

  return <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>;
}

export type SidebarProps = React.ComponentPropsWithoutRef<'aside'> & {
  variant?: 'sidebar' | 'floating';
  collapsible?: 'icon' | 'none' | 'offcanvas';
  side?: 'left' | 'right';
};

const Sidebar = React.forwardRef<HTMLDivElement, SidebarProps>(
  (
    {
      className,
      variant = 'sidebar',
      collapsible = 'offcanvas',
      side = 'left',
      children,
      ...props
    },
    ref,
  ) => {
    const { isOpen } = useSidebar();

    return (
      <aside
        ref={ref}
        data-variant={variant}
        data-collapsible={collapsible}
        data-side={side}
        data-state={isOpen ? 'expanded' : 'collapsed'}
        className={cn(
          'flex h-full w-64 flex-col border-r bg-sidebar text-sidebar-foreground transition-all duration-200',
          variant === 'floating' && 'rounded-lg shadow-lg',
          !isOpen && collapsible !== 'none' && 'w-12',
          className,
        )}
        {...props}
      >
        {children}
      </aside>
    );
  },
);
Sidebar.displayName = 'Sidebar';

export type SidebarTriggerProps = React.ComponentPropsWithoutRef<'button'> & {
  asChild?: boolean;
};

const SidebarTrigger = React.forwardRef<HTMLButtonElement, SidebarTriggerProps>(
  ({ className, asChild = false, onClick, ...props }, ref) => {
    const { toggle, isOpen } = useSidebar();
    const Comp = asChild ? Slot : 'button';

    return (
      <Comp
        ref={ref as any}
        type={asChild ? undefined : 'button'}
        aria-expanded={isOpen}
        onClick={event => {
          if (onClick) {
            onClick(event as any);
          }
          toggle();
        }}
        className={cn(
          'inline-flex h-9 w-9 items-center justify-center rounded-md border border-input bg-background text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
          className,
        )}
        {...props}
      />
    );
  },
);
SidebarTrigger.displayName = 'SidebarTrigger';

const SidebarRail = React.forwardRef<HTMLDivElement, React.ComponentPropsWithoutRef<'div'>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('hidden w-3 shrink-0 bg-sidebar-border md:block', className)}
      {...props}
    />
  ),
);
SidebarRail.displayName = 'SidebarRail';

const SidebarInset = React.forwardRef<HTMLElement, React.ComponentPropsWithoutRef<'main'>>(
  ({ className, ...props }, ref) => (
    <main
      ref={ref}
      className={cn('flex flex-1 flex-col bg-background', className)}
      {...props}
    />
  ),
);
SidebarInset.displayName = 'SidebarInset';

const SidebarHeader = React.forwardRef<HTMLDivElement, React.ComponentPropsWithoutRef<'div'>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('flex flex-col gap-2 p-4', className)} {...props} />
  ),
);
SidebarHeader.displayName = 'SidebarHeader';

const SidebarContent = React.forwardRef<HTMLDivElement, React.ComponentPropsWithoutRef<'div'>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('flex-1 overflow-y-auto p-2', className)} {...props} />
  ),
);
SidebarContent.displayName = 'SidebarContent';

const SidebarFooter = React.forwardRef<HTMLDivElement, React.ComponentPropsWithoutRef<'div'>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('mt-auto flex flex-col gap-2 p-4', className)} {...props} />
  ),
);
SidebarFooter.displayName = 'SidebarFooter';

const SidebarGroup = React.forwardRef<HTMLDivElement, React.ComponentPropsWithoutRef<'div'>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('flex w-full flex-col gap-2', className)} {...props} />
  ),
);
SidebarGroup.displayName = 'SidebarGroup';

const SidebarGroupLabel = React.forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<'div'> & { asChild?: boolean }
>(({ className, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : 'div';
  return (
    <Comp
      ref={ref as any}
      className={cn('px-2 text-xs font-semibold uppercase text-muted-foreground', className)}
      {...props}
    />
  );
});
SidebarGroupLabel.displayName = 'SidebarGroupLabel';

const SidebarGroupContent = React.forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<'div'>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('flex flex-col gap-1', className)} {...props} />
));
SidebarGroupContent.displayName = 'SidebarGroupContent';

const SidebarMenu = React.forwardRef<HTMLUListElement, React.ComponentPropsWithoutRef<'ul'>>(
  ({ className, ...props }, ref) => (
    <ul ref={ref} className={cn('flex flex-col gap-1', className)} {...props} />
  ),
);
SidebarMenu.displayName = 'SidebarMenu';

const SidebarMenuItem = React.forwardRef<HTMLLIElement, React.ComponentPropsWithoutRef<'li'>>(
  ({ className, ...props }, ref) => (
    <li ref={ref} className={cn('list-none', className)} {...props} />
  ),
);
SidebarMenuItem.displayName = 'SidebarMenuItem';

export type SidebarMenuButtonProps = React.ComponentPropsWithoutRef<'button'> & {
  asChild?: boolean;
  isActive?: boolean;
  variant?: 'default' | 'outline';
  size?: 'default' | 'sm';
};

const SidebarMenuButton = React.forwardRef<HTMLButtonElement, SidebarMenuButtonProps>(
  (
    { className, asChild = false, isActive = false, variant = 'default', size = 'default', ...props },
    ref,
  ) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp
        ref={ref as any}
        type={asChild ? undefined : 'button'}
        data-active={isActive ? 'true' : undefined}
        className={cn(
          'flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
          variant === 'outline' && 'border border-border bg-background hover:bg-accent',
          variant === 'default' && 'hover:bg-accent hover:text-accent-foreground',
          size === 'sm' && 'px-2 py-1 text-xs',
          isActive && 'bg-accent text-accent-foreground',
          className,
        )}
        {...props}
      />
    );
  },
);
SidebarMenuButton.displayName = 'SidebarMenuButton';

const SidebarMenuAction = React.forwardRef<
  HTMLButtonElement,
  React.ComponentPropsWithoutRef<'button'>
>(({ className, ...props }, ref) => (
  <Button
    ref={ref}
    type="button"
    className={cn(
      'absolute right-2 top-2 inline-flex h-6 w-6 items-center justify-center rounded-md text-xs font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground',
      className,
    )}
    {...props}
  />
));
SidebarMenuAction.displayName = 'SidebarMenuAction';

const SidebarSeparator = React.forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithoutRef<'div'>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('h-px w-full bg-border', className)} {...props} />
));
SidebarSeparator.displayName = 'SidebarSeparator';

export {
  SidebarProvider,
  useSidebar,
  Sidebar,
  SidebarTrigger,
  SidebarRail,
  SidebarInset,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenuAction,
  SidebarSeparator,
};
