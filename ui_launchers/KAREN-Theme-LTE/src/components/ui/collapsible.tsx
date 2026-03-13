"use client"

import * as React from "react"
import * as CollapsiblePrimitive from "@radix-ui/react-collapsible"

const Collapsible = CollapsiblePrimitive.Root
const CollapsibleTrigger = CollapsiblePrimitive.CollapsibleTrigger
const CollapsibleContent = CollapsiblePrimitive.CollapsibleContent

export { Collapsible, CollapsibleTrigger, CollapsibleContent }

export interface CollapsibleProps {
  children: React.ReactNode | ((isOpen: boolean) => React.ReactNode)
  open?: boolean
  defaultOpen?: boolean
  onOpenChange?: (open: boolean) => void
  className?: string
}

export function CollapsibleComponent({
  children,
  open,
  defaultOpen,
  onOpenChange,
  className,
}: CollapsibleProps) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen || false)

  React.useEffect(() => {
    if (open !== undefined) {
      setIsOpen(open)
    }
  }, [open])

  const handleOpenChange = (newOpen: boolean) => {
    setIsOpen(newOpen)
    onOpenChange?.(newOpen)
  }

  return (
    <Collapsible open={isOpen} onOpenChange={handleOpenChange}>
      <CollapsibleTrigger className={className}>
        {typeof children === 'function' ? children(isOpen) : children}
      </CollapsibleTrigger>
      <CollapsibleContent>
        {/* Content rendered by CollapsiblePrimitive */}
      </CollapsibleContent>
    </Collapsible>
  )
}
