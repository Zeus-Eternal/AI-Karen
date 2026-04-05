
import { KAREN_SETTINGS_LS_KEY } from './constants';

export type FactVisibility = 'private' | 'personal' | 'global';
export type FactDomain = 'lifestyle' | 'professional' | 'business';

export interface Fact {
  id: string;
  text: string;
  visibility: FactVisibility;
  domain: FactDomain;
  category: string;
  importance: number;
  confidence: number;
  source?: string;
  sourceType?: 'gmail' | 'calendar' | 'chat' | 'manual' | 'manual_sync';
  created_at: string;
  updated_at?: string;
  last_used?: string;
  usage_count: number;
  metadata?: Record<string, any>;
}

export interface FactSuggestion {
  id: string;
  text: string;
  reasoning: string;
  source: string;
  confidence: number;
  domain: FactDomain;
  status: 'pending' | 'accepted' | 'ignored';
}

const FACTS_LS_KEY = 'karen_robust_facts_v2';
const SUGGESTIONS_LS_KEY = 'karen_fact_suggestions';

export const mockFactApi = {
  getFacts: async (): Promise<Fact[]> => {
    await new Promise(resolve => setTimeout(resolve, 500));
    const stored = localStorage.getItem(FACTS_LS_KEY);
    if (!stored) {
      const legacyFacts = JSON.parse(localStorage.getItem(KAREN_SETTINGS_LS_KEY) || '{}').personalFacts || [];
      const seeded: Fact[] = legacyFacts.map((text: string, i: number) => ({
        id: `fact-${Date.now()}-${i}`,
        text,
        visibility: 'personal',
        domain: 'lifestyle',
        category: 'Personal Profile',
        importance: 8,
        confidence: 0.95,
        source: 'Legacy Import',
        sourceType: 'manual',
        usage_count: Math.floor(Math.random() * 10),
        created_at: new Date(Date.now() - (i * 86400000)).toISOString()
      }));
      // Add some sample business facts
      seeded.push({
        id: 'fact-biz-1',
        text: 'Client QBR sessions are prioritized every third Wednesday.',
        visibility: 'personal',
        domain: 'business',
        category: 'Scheduling',
        importance: 9,
        confidence: 0.88,
        source: 'Gmail Thread "Q3 Planning"',
        sourceType: 'gmail',
        usage_count: 12,
        created_at: new Date().toISOString(),
        last_used: new Date().toISOString()
      });
      localStorage.setItem(FACTS_LS_KEY, JSON.stringify(seeded));
      return seeded;
    }
    return JSON.parse(stored);
  },

  getSuggestions: async (): Promise<FactSuggestion[]> => {
    await new Promise(resolve => setTimeout(resolve, 300));
    const stored = localStorage.getItem(SUGGESTIONS_LS_KEY);
    if (!stored) {
      const initial: FactSuggestion[] = [
        {
          id: 'sug-1',
          text: 'You typically prefer deep work blocks from 9am-11am on Tuesdays.',
          reasoning: 'Observed from Google Calendar blocking and consistent rejection of meeting invites during this window.',
          source: 'Google Calendar Integration',
          confidence: 0.92,
          domain: 'professional',
          status: 'pending'
        },
        {
          id: 'sug-2',
          text: 'The project "Zeus" deadline has moved to May 15th.',
          reasoning: 'Detected in Slack conversation with @ProjectManager yesterday.',
          source: 'Slack Connect',
          confidence: 0.85,
          domain: 'business',
          status: 'pending'
        }
      ];
      localStorage.setItem(SUGGESTIONS_LS_KEY, JSON.stringify(initial));
      return initial;
    }
    return JSON.parse(stored);
  },

  addFact: async (fact: Omit<Fact, 'id' | 'created_at' | 'usage_count'>): Promise<Fact> => {
    await new Promise(resolve => setTimeout(resolve, 300));
    const facts = await mockFactApi.getFacts();
    const newFact: Fact = {
      ...fact,
      id: `fact-${Date.now()}`,
      usage_count: 0,
      created_at: new Date().toISOString()
    };
    const updated = [newFact, ...facts];
    localStorage.setItem(FACTS_LS_KEY, JSON.stringify(updated));
    return newFact;
  },

  updateFact: async (id: string, updates: Partial<Fact>): Promise<Fact> => {
    await new Promise(resolve => setTimeout(resolve, 300));
    const facts = await mockFactApi.getFacts();
    const index = facts.findIndex(f => f.id === id);
    if (index === -1) throw new Error('Fact not found');
    
    const updatedFact = { ...facts[index], ...updates, updated_at: new Date().toISOString() };
    facts[index] = updatedFact;
    localStorage.setItem(FACTS_LS_KEY, JSON.stringify(facts));
    return updatedFact;
  },

  deleteFact: async (id: string): Promise<void> => {
    await new Promise(resolve => setTimeout(resolve, 200));
    const facts = await mockFactApi.getFacts();
    const updated = facts.filter(f => f.id !== id);
    localStorage.setItem(FACTS_LS_KEY, JSON.stringify(updated));
  },

  processSuggestion: async (id: string, status: 'accepted' | 'ignored'): Promise<void> => {
    const suggestions = await mockFactApi.getSuggestions();
    const index = suggestions.findIndex(s => s.id === id);
    if (index !== -1) {
      if (status === 'accepted') {
        const sug = suggestions[index];
        await mockFactApi.addFact({
          text: sug.text,
          visibility: 'personal',
          domain: sug.domain,
          category: 'AI Insight',
          importance: Math.floor(sug.confidence * 10),
          confidence: sug.confidence,
          source: sug.source,
          sourceType: 'chat' // Default mapping for mock
        });
      }
      suggestions.splice(index, 1); // Remove from list once processed
      localStorage.setItem(SUGGESTIONS_LS_KEY, JSON.stringify(suggestions));
    }
  }
};
