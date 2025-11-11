import { create } from "zustand";
import { persist } from "zustand/middleware";

type Theme = "light" | "dark" | "system";

interface ThemeStore {
  theme: Theme;
  effectiveTheme: "light" | "dark";
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const getEffectiveTheme = (theme: Theme): "light" | "dark" => {
  if (theme === "system") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }
  return theme;
};

export const useThemeStore = create<ThemeStore>()(
  persist(
    (set, get) => ({
      theme: "system",
      effectiveTheme: getEffectiveTheme("system"),
      setTheme: (theme) => {
        set({ theme, effectiveTheme: getEffectiveTheme(theme) });
        document.documentElement.classList.toggle(
          "dark",
          getEffectiveTheme(theme) === "dark"
        );
      },
      toggleTheme: () => {
        const current = get().effectiveTheme;
        const newTheme = current === "dark" ? "light" : "dark";
        set({ theme: newTheme, effectiveTheme: newTheme });
        document.documentElement.classList.toggle("dark", newTheme === "dark");
      },
    }),
    {
      name: "karen-theme-storage",
    }
  )
);

// Listen to system theme changes
if (typeof window !== "undefined") {
  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", (_e) => {
      const store = useThemeStore.getState();
      if (store.theme === "system") {
        store.setTheme("system");
      }
    });
}
