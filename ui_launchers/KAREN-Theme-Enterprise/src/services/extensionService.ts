import { getKarenBackend } from '@/lib/karen-backend'

export interface ExtensionInfo {
  name: string
  version: string
  status: string
  loaded_at?: number
  error_message?: string
}
export interface ExtensionEvent {
  id: string
  capsule: string
  event_type: string
  payload: Record<string, unknown>
  risk: number
}
export class ExtensionService {
  private backend = getKarenBackend()
  private polling = false
  async getInstalledExtensions(): Promise<ExtensionInfo[]> {
    try {
      const list = await this.backend['makeRequest']<ExtensionInfo[]>('/extensions')
      return list
    } catch {
      // Return empty array if request fails
      return []
    }
  }
  async loadExtension(name: string): Promise<boolean> {
    try {
      await this.backend['makeRequest'](`/extensions/${encodeURIComponent(name)}/load`, { method: 'POST' })
      return true
    } catch {
      // Return false if load fails
      return false
    }
  }
  async unloadExtension(name: string): Promise<boolean> {
    try {
      await this.backend['makeRequest'](`/extensions/${encodeURIComponent(name)}/unload`, { method: 'POST' })
      return true
    } catch {
      // Return false if unload fails
      return false
    }
  }
  subscribeToEvents(callback: (events: ExtensionEvent[]) => void, interval = 5000) {
    if (this.polling) return
    this.polling = true
    const poll = async () => {
      if (!this.polling) return
      try {
        const events = await this.backend['makeRequest']<ExtensionEvent[]>('/api/events/', {}, false)
        if (events.length) callback(events)
      } catch {
        // Ignore polling errors and continue
      }
      setTimeout(poll, interval)
    }
    poll()
  }
  stopEventSubscription() {
    this.polling = false
  }
}
let extensionService: ExtensionService | null = null
export function getExtensionService(): ExtensionService {
  if (!extensionService) {
    extensionService = new ExtensionService()
  }
  return extensionService
}
export function initializeExtensionService(): ExtensionService {
  extensionService = new ExtensionService()
  return extensionService
}
