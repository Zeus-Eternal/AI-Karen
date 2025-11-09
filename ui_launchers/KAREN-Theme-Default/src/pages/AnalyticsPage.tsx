import { BarChart3, TrendingUp, Users, MessageSquare } from 'lucide-react'

const stats = [
  { name: 'Total Conversations', value: '1,234', change: '+12.5%', icon: MessageSquare },
  { name: 'Active Users', value: '456', change: '+8.2%', icon: Users },
  { name: 'Avg Response Time', value: '1.2s', change: '-15.3%', icon: TrendingUp },
  { name: 'Success Rate', value: '98.5%', change: '+2.1%', icon: BarChart3 },
]

export default function AnalyticsPage() {
  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center gap-3 mb-8">
          <BarChart3 className="w-8 h-8 text-karen-primary" />
          <h1 className="text-3xl font-bold">Analytics</h1>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat) => {
            const Icon = stat.icon
            return (
              <div key={stat.name} className="p-6 bg-card border border-border rounded-lg">
                <div className="flex items-center justify-between mb-4">
                  <Icon className="w-5 h-5 text-muted-foreground" />
                  <span className={`text-sm font-medium ${
                    stat.change.startsWith('+') ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {stat.change}
                  </span>
                </div>
                <p className="text-2xl font-bold mb-1">{stat.value}</p>
                <p className="text-sm text-muted-foreground">{stat.name}</p>
              </div>
            )
          })}
        </div>

        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Usage Trends</h2>
          <div className="h-64 flex items-center justify-center text-muted-foreground">
            Chart visualization will be rendered here
          </div>
        </div>
      </div>
    </div>
  )
}
