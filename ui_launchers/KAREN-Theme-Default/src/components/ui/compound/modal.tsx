"use client"

import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import type { BaseModalProps, ModalTriggerProps, ModalContentProps, ModalActionsProps } from "./types";

// Modal Root Component
const ModalRoot = DialogPrimitive.Root
ModalRoot.displayName = "ModalRoot"

// Modal Trigger Component
const ModalTrigger = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Trigger>,
  ModalTriggerProps
>(({ asChild = false, ...props }, ref) => (
  <DialogPrimitive.Trigger ref={ref} asChild={asChild} {...props} />
))
ModalTrigger.displayName = "ModalTrigger"

// Modal Portal Component
const ModalPortal = DialogPrimitive.Portal
ModalPortal.displayName = "ModalPortal"

// Modal Overlay Component
const ModalOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
      "fixed inset-0 z-50 bg-black/80 backdrop-blur-sm",
      "data-[state=open]:animate-in data-[state=closed]:animate-out",
      "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className
    )}
    {...props}
  />
))
ModalOverlay.displayName = "ModalOverlay"

// Modal Content Component
const ModalContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  ModalContentProps
>(({ className, children, size = "md", showCloseButton = true, ...props }, ref) => (
  <ModalPortal>
    <ModalOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-[50%] top-[50%] z-50 grid translate-x-[-50%] translate-y-[-50%]",
        "gap-4 border bg-background p-6 shadow-lg duration-200",
        "data-[state=open]:animate-in data-[state=closed]:animate-out",
        "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
        "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95",
        "data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%]",
        "data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%]",
        "sm:rounded-lg",
        {
          "w-full max-w-sm": size === "sm",
          "w-full max-w-lg": size === "md",
          "w-full max-w-2xl": size === "lg",
          "w-full max-w-4xl": size === "xl",
          "w-screen h-screen max-w-none rounded-none": size === "full",
        },
        className
      )}
      {...props}
    >
      {children}
      {showCloseButton && (
        <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground">
          <X className="h-4 w-4 " />
          <span className="sr-only">Close</span>
        </DialogPrimitive.Close>
      )}
    </DialogPrimitive.Content>
  </ModalPortal>
))
ModalContent.displayName = "ModalContent"

// Modal Header Component
const ModalHeader = React.forwardRef<HTMLDivElement, BaseModalProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex flex-col space-y-1.5 text-center sm:text-left",
        className
      )}
      {...props}
    />
  )
)
ModalHeader.displayName = "ModalHeader"

// Modal Title Component
const ModalTitle = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn(
      "text-lg font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
))
ModalTitle.displayName = "ModalTitle"

// Modal Description Component
const ModalDescription = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Description
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
))
ModalDescription.displayName = "ModalDescription"

// Modal Body Component
const ModalBody = React.forwardRef<HTMLDivElement, BaseModalProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex-1 overflow-y-auto", className)}
      {...props}
    />
  )
)
ModalBody.displayName = "ModalBody"

// Modal Actions Component
const ModalActions = React.forwardRef<HTMLDivElement, ModalActionsProps>(
  ({ className, justify = "end", ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex flex-col-reverse sm:flex-row sm:space-x-2",
        {
          "sm:justify-start": justify === "start",
          "sm:justify-center": justify === "center",
          "sm:justify-end": justify === "end",
          "sm:justify-between": justify === "between",
        },
        className
      )}
      {...props}
    />
  )
)
ModalActions.displayName = "ModalActions"

// Modal Close Component
const ModalClose = DialogPrimitive.Close
ModalClose.displayName = "ModalClose"

// Compound Modal Component
const Modal = {
  Root: ModalRoot,
  Trigger: ModalTrigger,
  Portal: ModalPortal,
  Overlay: ModalOverlay,
  Content: ModalContent,
  Header: ModalHeader,
  Title: ModalTitle,
  Description: ModalDescription,
  Body: ModalBody,
  Actions: ModalActions,
  Close: ModalClose,
}

const ModalDefault = Modal;

export {
  Modal,
  ModalRoot,
  ModalTrigger,
  ModalPortal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalBody,
  ModalActions,
  ModalClose,
}

export default ModalDefault;
