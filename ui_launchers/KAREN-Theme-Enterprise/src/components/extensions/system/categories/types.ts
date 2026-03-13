export interface SystemCategory {
  id: string;
  name: string;
  description: string;
  icon: string;
  extensionCount: number;
  isActive: boolean;
  lastUpdated: Date;
}

export interface SystemCategoryFilter {
  search?: string;
  isActive?: boolean;
  sortBy?: 'name' | 'extensionCount' | 'lastUpdated';
  sortOrder?: 'asc' | 'desc';
}