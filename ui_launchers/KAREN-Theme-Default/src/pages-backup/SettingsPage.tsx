import { Settings as SettingsIcon, User, Bell, Palette, Shield } from 'lucide-react'

const settingsSections = [
  {
    title: 'Profile',
    icon: User,
    description: 'Manage your account and preferences',
  },
  {
    title: 'Notifications',
    icon: Bell,
    description: 'Configure notification settings',
  },
  {
    title: 'Appearance',
    icon: Palette,
    description: 'Customize theme and display options',
  },
  {
    title: 'Privacy & Security',
    icon: Shield,
    description: 'Control your data and security settings',
  },
]

export default function SettingsPage() {
  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-center gap-3 mb-8">
          <SettingsIcon className="w-8 h-8 text-karen-primary" />
          <h1 className="text-3xl font-bold">Settings</h1>
        </div>

        <div className="grid gap-6">
          {settingsSections.map((section) => {
            const Icon = section.icon
            return (
              <div
                key={section.title}
                className="p-6 bg-card border border-border rounded-lg hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-karen-primary/10 rounded-lg">
                    <Icon className="w-6 h-6 text-karen-primary" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold mb-1">{section.title}</h3>
                    <p className="text-muted-foreground">{section.description}</p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
