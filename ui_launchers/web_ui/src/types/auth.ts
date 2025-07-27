export interface User {
  user_id: string;
  email: string;
  roles: string[];
  tenant_id: string;
  preferences: {
    personalityTone: string;
    personalityVerbosity: string;
    memoryDepth: string;
    customPersonaInstructions: string;
    preferredLLMProvider: string;
    preferredModel: string;
    temperature: number;
    maxTokens: number;
    notifications: {
      email: boolean;
      push: boolean;
    };
    ui: {
      theme: string;
      language: string;
    };
  };
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user_id: string;
  email: string;
  roles: string[];
  tenant_id: string;
  preferences: any;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  updateUserPreferences: (preferences: Partial<User['preferences']>) => Promise<void>;
}