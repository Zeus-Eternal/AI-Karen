"use client"

import { useEffect, useState } from "react"
import { createPortal } from "react-dom"
import { useToast } from "@/hooks/use-toast"
import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
} from "@/components/ui/toast"

export function Toaster() {
  const { toasts } = useToast()
  const [sidebarFooterElement, setSidebarFooterElement] = useState<HTMLElement | null>(null)

  useEffect(() => {
    if (typeof document === 'undefined') return;
    
    const resolveSidebarFooter = () => {
      const next = document.querySelector<HTMLElement>('[data-sidebar="footer"]')
      setSidebarFooterElement((current) => (current === next ? current : next))
    }

    resolveSidebarFooter()

    const observer = new MutationObserver(resolveSidebarFooter)
    observer.observe(document.body, {
      childList: true,
      subtree: true,
    })

    return () => observer.disconnect()
  }, [])

  const viewport = (
    <ToastViewport
      className={
        sidebarFooterElement
          ? "!absolute !bottom-full !left-2 !right-2 !top-auto !w-auto !max-h-[50vh] !p-0 !z-[120] !flex-col"
          : undefined
      }
    />
  )

  return (
    <ToastProvider>
      {toasts.map(function ({ id, title, description, action, ...props }) {
        return (
          <Toast key={id} {...props}>
            <div className="grid gap-1">
              {title && <ToastTitle>{title}</ToastTitle>}
              {description && (
                <ToastDescription>{description}</ToastDescription>
              )}
            </div>
            {action}
            <ToastClose />
          </Toast>
        )
      })}
      {sidebarFooterElement ? createPortal(viewport, sidebarFooterElement) : viewport}
    </ToastProvider>
  )
}
