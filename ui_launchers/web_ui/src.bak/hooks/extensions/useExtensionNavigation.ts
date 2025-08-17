"use client";
import { useCallback } from "react";
import { useExtensionContext, type BreadcrumbItem, type ExtensionCategory } from "@/extensions";
import { useNavigationActions } from "@/lib/extensions/navigationUtils";

export interface UseExtensionNavigation {
  navigation: ReturnType<typeof useExtensionContext>["state"]["navigation"];
  setCategory: (category: ExtensionCategory) => void;
  pushBreadcrumb: (item: BreadcrumbItem) => void;
  goBack: () => void;
  reset: () => void;
  navigate: ReturnType<typeof useNavigationActions>["navigate"];
}

export function useExtensionNavigation(): UseExtensionNavigation {
  const { state, dispatch } = useExtensionContext();
  const { dispatchMultiple, navigate } = useNavigationActions(dispatch);

  const setCategory = useCallback(
    (category: ExtensionCategory) => dispatch({ type: "SET_CATEGORY", category }),
    [dispatch],
  );

  const pushBreadcrumb = useCallback(
    (item: BreadcrumbItem) => dispatch({ type: "PUSH_BREADCRUMB", item }),
    [dispatch],
  );

  const goBack = useCallback(() => dispatch({ type: "GO_BACK" }), [dispatch]);
  const reset = useCallback(() => dispatch({ type: "RESET_BREADCRUMBS" }), [dispatch]);

  return {
    navigation: state.navigation,
    setCategory,
    pushBreadcrumb,
    goBack,
    reset,
    navigate,
  };
}
