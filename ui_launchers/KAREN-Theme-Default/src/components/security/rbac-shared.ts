export type UserRole = "admin" | "user" | "guest" | "moderator" | "developer";

export type Permission =
  | "chat.send"
  | "chat.code_assistance"
  | "chat.explanations"
  | "chat.documentation"
  | "chat.analysis"
  | "voice.input"
  | "voice.output"
  | "attachments.upload"
  | "attachments.download"
  | "admin.settings"
  | "admin.users"
  | "developer.debug"
  | "moderator.content";

export const ROLE_HIERARCHY: Record<UserRole, number> = {
  guest: 0,
  user: 1,
  moderator: 2,
  developer: 3,
  admin: 4,
} as const;

export const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  guest: ["chat.send"],
  user: [
    "chat.send",
    "chat.code_assistance",
    "chat.explanations",
    "chat.documentation",
    "chat.analysis",
    "voice.input",
    "voice.output",
    "attachments.upload",
    "attachments.download",
  ],
  moderator: [
    "chat.send",
    "chat.code_assistance",
    "chat.explanations",
    "chat.documentation",
    "chat.analysis",
    "voice.input",
    "voice.output",
    "attachments.upload",
    "attachments.download",
    "moderator.content",
  ],
  developer: [
    "chat.send",
    "chat.code_assistance",
    "chat.explanations",
    "chat.documentation",
    "chat.analysis",
    "voice.input",
    "voice.output",
    "attachments.upload",
    "attachments.download",
    "developer.debug",
  ],
  admin: [
    "chat.send",
    "chat.code_assistance",
    "chat.explanations",
    "chat.documentation",
    "chat.analysis",
    "voice.input",
    "voice.output",
    "attachments.upload",
    "attachments.download",
    "moderator.content",
    "developer.debug",
    "admin.settings",
    "admin.users",
  ],
} as const;

export function getHighestRole(roles: readonly string[] | undefined | null): UserRole {
  if (!roles || roles.length === 0) return "guest";
  let best: UserRole = "guest";
  let bestLevel = ROLE_HIERARCHY[best];
  for (const r of roles) {
    const role = (r as UserRole) || "guest";
    const lvl = ROLE_HIERARCHY[role] ?? 0;
    if (lvl > bestLevel) {
      best = role;
      bestLevel = lvl;
    }
  }
  return best;
}
