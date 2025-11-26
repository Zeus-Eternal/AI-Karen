import { Puzzle, Play, Settings } from 'lucide-react'

const mockPlugins = [
  {
    id: '1',
    name: 'Weather Plugin',
    description: 'Get real-time weather information for any location',
    enabled: true,
    category: 'Utility',
  },
  {
    id: '2',
    name: 'Calculator',
    description: 'Perform complex mathematical calculations',
    enabled: true,
    category: 'Utility',
  },
  {
    id: '3',
    name: 'Web Search',
    description: 'Search the web for information',
    enabled: false,
    category: 'Information',
  },
]

export default function PluginsPage() {
  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center gap-3 mb-8">
          <Puzzle className="w-8 h-8 text-karen-primary" />
          <h1 className="text-3xl font-bold">Plugins</h1>
        </div>

        <div className="grid gap-4">
          {mockPlugins.map((plugin) => (
            <div
              key={plugin.id}
              className="p-6 bg-card border border-border rounded-lg hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold">{plugin.name}</h3>
                    <span className="px-2 py-1 text-xs font-medium bg-karen-primary/10 text-karen-primary rounded">
                      {plugin.category}
                    </span>
                  </div>
                  <p className="text-muted-foreground mb-4">{plugin.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  <button className="p-2 hover:bg-accent rounded-lg transition-colors">
                    <Settings className="w-5 h-5 text-muted-foreground" />
                  </button>
                  <button className="p-2 hover:bg-accent rounded-lg transition-colors">
                    <Play className="w-5 h-5 text-muted-foreground" />
                  </button>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={plugin.enabled}
                      className="sr-only peer"
                      readOnly
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-karen-primary/20 dark:peer-focus:ring-karen-primary/40 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-karen-primary"></div>
                  </label>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
