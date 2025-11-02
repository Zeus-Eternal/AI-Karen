// UI Logic Hooks Export
export {
  useMediaQuery,
  useMediaQueries,
  useBreakpoint,
  useCurrentBreakpoint,
  useDeviceCapabilities,
} from "../use-media-query"

export {
  useLocalStorage,
  useSessionStorage,
  usePersistentUIState,
  usePersistentForm,
} from "../use-local-storage"

export {
  useKeyboardShortcuts,
  useKeyboardShortcut,
  useCommonShortcuts,
  useNavigationShortcuts,
  useShortcutDisplay,
  useShortcutHelp,
} from "../use-keyboard-shortcuts"

export {
  useReducedMotion,
  useAnimationDuration,
  useAnimationVariants,
} from "../use-reduced-motion"

// Types export
export type {
  KeyboardShortcut,
  KeyboardShortcutHandler,
  KeyboardShortcutConfig,
} from "../use-keyboard-shortcuts"