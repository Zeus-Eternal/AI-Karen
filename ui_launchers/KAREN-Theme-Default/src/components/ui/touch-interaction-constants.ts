import type {
  FloatingActionButtonProps,
  TouchButtonProps,
} from "./types";

export const BUTTON_VARIANTS: Record<
  NonNullable<TouchButtonProps["variant"]>,
  string
> = {
  primary: "bg-blue-500 hover:bg-blue-600 text-white shadow-lg",
  secondary:
    "bg-gray-100 hover:bg-gray-200 text-gray-900 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-100",
  ghost:
    "hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300",
  destructive: "bg-red-500 hover:bg-red-600 text-white shadow-lg",
};

export const BUTTON_SIZES: Record<
  NonNullable<TouchButtonProps["size"]>,
  string
> = {
  sm: "min-h-[40px] px-3 py-2 text-sm",
  md: "min-h-[44px] px-4 py-2.5 text-base",
  lg: "min-h-[48px] px-6 py-3 text-lg",
};

export const FAB_POSITIONS: Record<
  NonNullable<FloatingActionButtonProps["position"]>,
  string
> = {
  "bottom-right": "bottom-6 right-6",
  "bottom-left": "bottom-6 left-6",
  "bottom-center": "bottom-6 left-1/2 -translate-x-1/2",
};

export const FAB_SIZES: Record<
  NonNullable<FloatingActionButtonProps["size"]>,
  string
> = {
  sm: "w-12 h-12",
  md: "w-14 h-14",
  lg: "w-16 h-16",
};

export const SLIDER_TRACK_COLOR = "bg-gray-200";
export const SLIDER_THUMB_COLOR = "bg-blue-500";
