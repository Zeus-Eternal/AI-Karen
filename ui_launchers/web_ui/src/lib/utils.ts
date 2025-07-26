import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function sanitizeInput(str: string): string {
  return str.replace(/[&<>"'`]/g, (ch) => {
    switch (ch) {
      case '&':
        return '&amp;'
      case '<':
        return '&lt;'
      case '>':
        return '&gt;'
      case '"':
        return '&quot;'
      case "'":
        return '&#39;'
      case '`':
        return '&#x60;'
      default:
        return ch
    }
  })
}

export function widgetRefId(tag: string): string {
  const match = tag.match(/\uE200forecast\uE202(.*?)\uE201/);
  return match ? match[1] : '';
}
