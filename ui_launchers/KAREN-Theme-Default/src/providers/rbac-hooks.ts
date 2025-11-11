import { useContext } from "react";
import { RBACContext } from "./rbac-context";
import type { RBACContextValue } from "./rbac-context";

export function useRBAC(): RBACContextValue {
  const context = useContext(RBACContext);
  if (!context) {
    throw new Error("useRBAC must be used within an RBACProvider");
  }
  return context;
}
