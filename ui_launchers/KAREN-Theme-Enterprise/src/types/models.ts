export interface ModelProvider {
  id: string;
  name: string;
  description?: string;
  status: "active" | "inactive" | "degraded";
}