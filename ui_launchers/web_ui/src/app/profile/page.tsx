"use client";
import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getMemoryService } from '@/services/memoryService'
import { authService } from '@/services/authService'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'

export default function ProfilePage() {
  const [isClient, setIsClient] = useState(false)
  const { user, logout } = useAuth()
  const router = useRouter()
  const [memoryCount, setMemoryCount] = useState<number | null>(null)
  const [message, setMessage] = useState('')

  useEffect(() => {
    setIsClient(true)
  }, [])

  useEffect(() => {
    if (!isClient || !user?.user_id) return
    
    getMemoryService()
      .getMemoryStats(user.user_id)
      .then(stats => setMemoryCount(stats.totalMemories))
      .catch(() => setMemoryCount(null))
  }, [isClient, user?.user_id])

  if (!isClient) {
    return <div>Loading...</div>
  }

  if (!user) {
    router.push('/login')
    return null
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setMessage('Profile updates are currently not available.')
  }

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    setMessage('Avatar upload is currently not available.')
  }

  return (
    <div className="p-6 max-w-xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>Logged in as <span className="font-semibold">{user?.user_id}</span></div>
          <div>Email: <span className="font-semibold">{user?.email}</span></div>
          <div>Roles: <span className="font-semibold">{user?.roles.join(', ')}</span></div>
          {memoryCount !== null && <div>Total memories: {memoryCount}</div>}
          
          {message && (
            <div className="p-3 bg-yellow-100 border border-yellow-300 rounded text-sm">
              {message}
            </div>
          )}
          
          <div className="flex gap-2">
            <Button type="button" variant="secondary" onClick={logout}>Log Out</Button>
          </div>
          
          <div className="text-sm text-gray-600">
            Profile editing and two-factor authentication setup are currently not available.
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
