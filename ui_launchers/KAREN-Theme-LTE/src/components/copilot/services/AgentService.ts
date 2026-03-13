import { Agent, AgentFilter, AgentStatus, AgentType, AgentCapability, AgentCapabilityDetail, AgentPersona } from '../components/agent/types';

class AgentService {
  private static instance: AgentService;
  private agents: Agent[] = [];

  private constructor() {
    // Initialize with mock data
    this.initializeMockAgents();
  }

  public static getInstance(): AgentService {
    if (!AgentService.instance) {
      AgentService.instance = new AgentService();
    }
    return AgentService.instance;
  }

  private initializeMockAgents(): void {
    const mockAgents: Agent[] = [
      {
        id: 'agent-1',
        name: 'General Assistant',
        type: AgentType.GENERAL,
        status: AgentStatus.AVAILABLE,
        persona: {
          name: 'General Assistant',
          description: 'A versatile AI assistant capable of handling a wide range of tasks',
          personality: 'Helpful, friendly, and adaptable',
          communicationStyle: 'Clear and concise',
          expertise: ['General knowledge', 'Task management', 'Basic problem solving'],
          tone: 'friendly',
          background: 'Trained on diverse datasets to provide comprehensive assistance'
        },
        capabilities: [
          {
            capability: AgentCapability.TEXT_GENERATION,
            name: 'Text Generation',
            description: 'Generate coherent and contextually relevant text',
            proficiency: 4,
            enabled: true
          },
          {
            capability: AgentCapability.CONVERSATION,
            name: 'Conversation',
            description: 'Engage in natural language conversations',
            proficiency: 5,
            enabled: true
          },
          {
            capability: AgentCapability.SUMMARIZATION,
            name: 'Summarization',
            description: 'Create concise summaries of longer texts',
            proficiency: 4,
            enabled: true
          },
          {
            capability: AgentCapability.PLANNING,
            name: 'Planning',
            description: 'Help create structured plans for tasks and projects',
            proficiency: 3,
            enabled: true
          }
        ],
        createdAt: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
        lastActive: new Date(Date.now() - 1 * 60 * 60 * 1000), // 1 hour ago
        performance: {
          tasksCompleted: 156,
          averageResponseTime: 2.5,
          successRate: 0.92,
          userRating: 4.2
        }
      },
      {
        id: 'agent-2',
        name: 'Code Specialist',
        type: AgentType.SPECIALIST,
        status: AgentStatus.AVAILABLE,
        persona: {
          name: 'Code Specialist',
          description: 'Specialized AI assistant for programming and software development tasks',
          personality: 'Precise, logical, and detail-oriented',
          communicationStyle: 'Technical and structured',
          expertise: ['Programming', 'Software development', 'Code optimization', 'Debugging'],
          tone: 'professional',
          background: 'Trained on extensive code repositories and programming documentation'
        },
        capabilities: [
          {
            capability: AgentCapability.CODE_GENERATION,
            name: 'Code Generation',
            description: 'Generate code in various programming languages',
            proficiency: 5,
            enabled: true
          },
          {
            capability: AgentCapability.PROBLEM_SOLVING,
            name: 'Problem Solving',
            description: 'Analyze and solve complex technical problems',
            proficiency: 4,
            enabled: true
          },
          {
            capability: AgentCapability.TEXT_GENERATION,
            name: 'Documentation',
            description: 'Generate technical documentation and comments',
            proficiency: 4,
            enabled: true
          },
          {
            capability: AgentCapability.DATA_ANALYSIS,
            name: 'Data Analysis',
            description: 'Analyze and interpret data patterns',
            proficiency: 3,
            enabled: true
          }
        ],
        createdAt: new Date(Date.now() - 25 * 24 * 60 * 60 * 1000), // 25 days ago
        lastActive: new Date(Date.now() - 30 * 60 * 1000), // 30 minutes ago
        performance: {
          tasksCompleted: 89,
          averageResponseTime: 3.2,
          successRate: 0.95,
          userRating: 4.5
        }
      },
      {
        id: 'agent-3',
        name: 'Creative Writer',
        type: AgentType.CREATIVE,
        status: AgentStatus.BUSY,
        persona: {
          name: 'Creative Writer',
          description: 'AI assistant specialized in creative writing and content generation',
          personality: 'Imaginative, expressive, and inspiring',
          communicationStyle: 'Descriptive and engaging',
          expertise: ['Creative writing', 'Storytelling', 'Content creation', 'Poetry'],
          tone: 'casual',
          background: 'Trained on literature, poetry, and creative writing samples'
        },
        capabilities: [
          {
            capability: AgentCapability.CREATIVE_WRITING,
            name: 'Creative Writing',
            description: 'Generate original creative content',
            proficiency: 5,
            enabled: true
          },
          {
            capability: AgentCapability.TEXT_GENERATION,
            name: 'Content Creation',
            description: 'Create engaging and original content',
            proficiency: 5,
            enabled: true
          },
          {
            capability: AgentCapability.SUMMARIZATION,
            name: 'Creative Summarization',
            description: 'Create engaging summaries with a creative flair',
            proficiency: 4,
            enabled: true
          },
          {
            capability: AgentCapability.CONVERSATION,
            name: 'Creative Dialogue',
            description: 'Engage in imaginative conversations',
            proficiency: 4,
            enabled: true
          }
        ],
        createdAt: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000), // 20 days ago
        lastActive: new Date(Date.now() - 15 * 60 * 1000), // 15 minutes ago
        performance: {
          tasksCompleted: 67,
          averageResponseTime: 4.1,
          successRate: 0.89,
          userRating: 4.3
        }
      },
      {
        id: 'agent-4',
        name: 'Research Analyst',
        type: AgentType.RESEARCH,
        status: AgentStatus.AVAILABLE,
        persona: {
          name: 'Research Analyst',
          description: 'AI assistant specialized in research, data analysis, and information synthesis',
          personality: 'Analytical, thorough, and methodical',
          communicationStyle: 'Detailed and evidence-based',
          expertise: ['Research', 'Data analysis', 'Information synthesis', 'Fact checking'],
          tone: 'formal',
          background: 'Trained on academic papers, research databases, and analytical methodologies'
        },
        capabilities: [
          {
            capability: AgentCapability.RESEARCH,
            name: 'Research',
            description: 'Conduct in-depth research on various topics',
            proficiency: 5,
            enabled: true
          },
          {
            capability: AgentCapability.DATA_ANALYSIS,
            name: 'Data Analysis',
            description: 'Analyze and interpret complex data',
            proficiency: 4,
            enabled: true
          },
          {
            capability: AgentCapability.SUMMARIZATION,
            name: 'Research Summarization',
            description: 'Create comprehensive research summaries',
            proficiency: 5,
            enabled: true
          },
          {
            capability: AgentCapability.PROBLEM_SOLVING,
            name: 'Analytical Problem Solving',
            description: 'Solve complex problems through analysis',
            proficiency: 4,
            enabled: true
          }
        ],
        createdAt: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000), // 15 days ago
        lastActive: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
        performance: {
          tasksCompleted: 42,
          averageResponseTime: 5.8,
          successRate: 0.96,
          userRating: 4.7
        }
      },
      {
        id: 'agent-5',
        name: 'Data Analyst',
        type: AgentType.ANALYTICAL,
        status: AgentStatus.OFFLINE,
        persona: {
          name: 'Data Analyst',
          description: 'AI assistant specialized in data analysis, visualization, and insights',
          personality: 'Precise, analytical, and detail-oriented',
          communicationStyle: 'Data-driven and structured',
          expertise: ['Data analysis', 'Statistics', 'Data visualization', 'Pattern recognition'],
          tone: 'professional',
          background: 'Trained on statistical methods, data analysis techniques, and visualization tools'
        },
        capabilities: [
          {
            capability: AgentCapability.DATA_ANALYSIS,
            name: 'Advanced Data Analysis',
            description: 'Perform complex data analysis and modeling',
            proficiency: 5,
            enabled: true
          },
          {
            capability: AgentCapability.PROBLEM_SOLVING,
            name: 'Data-Driven Problem Solving',
            description: 'Solve problems using data analysis',
            proficiency: 4,
            enabled: true
          },
          {
            capability: AgentCapability.RESEARCH,
            name: 'Data Research',
            description: 'Research and find relevant data sources',
            proficiency: 3,
            enabled: true
          },
          {
            capability: AgentCapability.SUMMARIZATION,
            name: 'Insight Summarization',
            description: 'Summarize key insights from data',
            proficiency: 4,
            enabled: true
          }
        ],
        createdAt: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000), // 10 days ago
        lastActive: new Date(Date.now() - 24 * 60 * 60 * 1000), // 24 hours ago
        performance: {
          tasksCompleted: 28,
          averageResponseTime: 6.2,
          successRate: 0.94,
          userRating: 4.6
        }
      }
    ];

    this.agents = mockAgents;
  }

  public async getAgents(filter?: AgentFilter): Promise<Agent[]> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 300));

    let filteredAgents = [...this.agents];

    if (filter) {
      if (filter.status && filter.status.length > 0) {
        filteredAgents = filteredAgents.filter(agent => 
          filter.status!.includes(agent.status)
        );
      }

      if (filter.type && filter.type.length > 0) {
        filteredAgents = filteredAgents.filter(agent => 
          filter.type!.includes(agent.type)
        );
      }

      if (filter.capabilities && filter.capabilities.length > 0) {
        filteredAgents = filteredAgents.filter(agent => 
          filter.capabilities!.some(capability => 
            agent.capabilities.some(agentCap => 
              agentCap.capability === capability && agentCap.enabled
            )
          )
        );
      }

      if (filter.searchQuery) {
        const query = filter.searchQuery.toLowerCase();
        filteredAgents = filteredAgents.filter(agent => 
          agent.name.toLowerCase().includes(query) ||
          agent.persona.description.toLowerCase().includes(query) ||
          agent.persona.expertise.some(expertise => 
            expertise.toLowerCase().includes(query)
          )
        );
      }
    }

    return filteredAgents;
  }

  public async getAgentById(id: string): Promise<Agent | null> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 200));

    const agent = this.agents.find(agent => agent.id === id);
    return agent || null;
  }

  public async updateAgent(id: string, updates: Partial<Agent>): Promise<Agent | null> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));

    const agentIndex = this.agents.findIndex(agent => agent.id === id);
    if (agentIndex === -1) {
      return null;
    }

    const existingAgent = this.agents[agentIndex];
    if (!existingAgent) {
      return null;
    }

    // Build updated agent without spreading updates (to avoid undefined id)
    const updatedAgent: Agent = {
      id: existingAgent.id,
      name: updates.name ?? existingAgent.name,
      type: updates.type ?? existingAgent.type,
      status: updates.status ?? existingAgent.status,
      persona: updates.persona ?? existingAgent.persona,
      capabilities: updates.capabilities ?? existingAgent.capabilities,
      createdAt: updates.createdAt ?? existingAgent.createdAt,
      lastActive: updates.lastActive ?? existingAgent.lastActive,
      performance: updates.performance ?? existingAgent.performance
    } as Agent;

    this.agents[agentIndex] = updatedAgent;
    return updatedAgent;
  }

  public async updateAgentPersona(id: string, persona: Partial<AgentPersona>): Promise<Agent | null> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 400));

    const agentIndex = this.agents.findIndex(agent => agent.id === id);
    if (agentIndex === -1) {
      return null;
    }

    const existingAgent = this.agents[agentIndex];
    if (!existingAgent) {
      return null;
    }

    this.agents[agentIndex] = {
      ...existingAgent,
      persona: {
        ...existingAgent.persona,
        ...persona
      }
    } as Agent;

    const updatedAgent = this.agents[agentIndex];
    return updatedAgent || null;
  }

  public async updateAgentCapabilities(id: string, capabilities: Partial<AgentCapabilityDetail>[]): Promise<Agent | null> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 400));

    const agentIndex = this.agents.findIndex(agent => agent.id === id);
    if (agentIndex === -1) {
      return null;
    }

    const existingAgent = this.agents[agentIndex];
    if (!existingAgent) {
      return null;
    }

    const updatedCapabilities = existingAgent.capabilities.map(cap => {
      const update = capabilities.find(u => u.capability === cap.capability);
      return update ? { ...cap, ...update } : cap;
    });

    this.agents[agentIndex] = {
      ...existingAgent,
      capabilities: updatedCapabilities
    } as Agent;

    const updatedAgent = this.agents[agentIndex];
    return updatedAgent || null;
  }

  public async createAgent(agentData: Omit<Agent, 'id' | 'createdAt'>): Promise<Agent> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 600));

    const newAgent: Agent = {
      ...agentData,
      id: `agent-${Date.now()}`,
      createdAt: new Date()
    };

    this.agents.push(newAgent);
    return newAgent;
  }

  public async deleteAgent(id: string): Promise<boolean> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 300));

    const agentIndex = this.agents.findIndex(agent => agent.id === id);
    if (agentIndex === -1) {
      return false;
    }

    this.agents.splice(agentIndex, 1);
    return true;
  }
}

export default AgentService;