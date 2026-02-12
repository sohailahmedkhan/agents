/**
 * Shared theme configuration for components.
 * Provides consistent color theming across the application.
 *
 * Use "primary" and "secondary" for app-wide theming.
 * These map to CSS custom properties defined in globals.css.
 * To change the app theme, update globals.css (one place only).
 */

// =============================================================================
// Semantic Color Themes
// Only semantic themes are used - they map to CSS custom properties in globals.css
// =============================================================================

export const colorThemes = {
  primary: {
    bg: "bg-gradient-to-br from-primary-100 to-primary-200",
    border: "border-primary-300",
    hoverBorder: "hover:border-primary-400",
    hoverShadow: "hover:shadow-primary-200/50",
    text: "text-primary-900",
    textSecondary: "text-primary-700",
    textMuted: "text-primary-600",
    iconBg: "bg-primary-200",
    iconText: "text-primary-700",
    buttonBg: "bg-primary-600",
    buttonHover: "hover:bg-primary-700",
  },
  secondary: {
    bg: "bg-gradient-to-br from-secondary-100 to-secondary-200",
    border: "border-secondary-300",
    hoverBorder: "hover:border-secondary-400",
    hoverShadow: "hover:shadow-secondary-200/50",
    text: "text-secondary-900",
    textSecondary: "text-secondary-700",
    textMuted: "text-secondary-600",
    iconBg: "bg-secondary-200",
    iconText: "text-secondary-700",
    buttonBg: "bg-secondary-600",
    buttonHover: "hover:bg-secondary-700",
  },
  tertiary: {
    bg: "bg-gradient-to-br from-tertiary-50 to-tertiary-100",
    border: "border-tertiary-200",
    hoverBorder: "hover:border-tertiary-400",
    hoverShadow: "hover:shadow-tertiary-200/50",
    text: "text-tertiary-900",
    textSecondary: "text-tertiary-700",
    textMuted: "text-tertiary-600",
    iconBg: "bg-tertiary-100",
    iconText: "text-tertiary-700",
    buttonBg: "bg-tertiary-600",
    buttonHover: "hover:bg-tertiary-700",
  },
} as const;

export type ColorTheme = keyof typeof colorThemes;

// =============================================================================
// Chart Palettes
// =============================================================================

export const ESSOS_PALETTE = [
  "#7A2E3F",
  "#D8584E",
  "#EF8747",
  "#F7B44A",
  "#F3E04C",
  "#E6D6A6",
] as const;

// =============================================================================
// Component-specific style maps
// Using static class maps for Tailwind JIT compatibility
// =============================================================================

interface SearchBarStyles {
  icon: string;
  input: string;
  text: string;
  clear: string;
}

interface ToggleStyles {
  container: string;
  active: string;
  inactive: string;
  activeCount: string;
  inactiveCount: string;
}

interface StatCardStyles {
  bg: string;
  border: string;
  label: string;
  value: string;
}

interface TableStyles {
  badge: string;
  header: string;
  mismatchRow: string;
  mismatchLegendDot: string;
  highlightHeader: string;
  highlightCell: string;
}

interface FilterStyles {
  border: string;
  bg: string;
  icon: string;
  text: string;
  textLight: string;
  chipBorder: string;
  hoverBg: string;
  button: string;
}

interface MapStyles {
  border: string;
  bg: string;
  text: string;
}

interface SidebarStyles {
  container: string;
  sectionHeader: string;
  divider: string;
  navItemBase: string;
  navItemHover: string;
  navItemActive: string;
  navItemDisabled: string;
  activeIndicator: string;
  iconInactive: string;
  iconActive: string;
  badge: string;
  contextLabel: string;
  contextValue: string;
}

interface SummaryBannerStyles {
  container: string;
  title: string;
  subtitle: string;
  meta: string;
  statusIcon: string;
  statusText: string;
  divider: string;
  actionButton: string;
}

export const searchBarStyles: Record<ColorTheme, SearchBarStyles> = {
  primary: {
    icon: "text-primary-400",
    input: "border-primary-200 focus:border-primary-400 focus:ring-primary-200",
    text: "text-primary-900 placeholder-primary-400",
    clear: "text-primary-600 hover:text-primary-800",
  },
  secondary: {
    icon: "text-secondary-400",
    input: "border-secondary-200 focus:border-secondary-400 focus:ring-secondary-200",
    text: "text-secondary-900 placeholder-secondary-400",
    clear: "text-secondary-600 hover:text-secondary-800",
  },
  tertiary: {
    icon: "text-tertiary-400",
    input: "border-tertiary-200 focus:border-tertiary-400 focus:ring-tertiary-200",
    text: "text-tertiary-900 placeholder-tertiary-400",
    clear: "text-tertiary-600 hover:text-tertiary-800",
  },
};

export const toggleStyles: Record<ColorTheme, ToggleStyles> = {
  primary: {
    container: "border-primary-200 bg-primary-50",
    active: "bg-primary-600 text-white",
    inactive: "text-primary-700 hover:bg-primary-100",
    activeCount: "bg-white/20 text-white",
    inactiveCount: "bg-primary-200 text-primary-900",
  },
  secondary: {
    container: "border-secondary-200 bg-secondary-50",
    active: "bg-secondary-600 text-white",
    inactive: "text-secondary-700 hover:bg-secondary-100",
    activeCount: "bg-white/20 text-white",
    inactiveCount: "bg-secondary-200 text-secondary-900",
  },
  tertiary: {
    container: "border-tertiary-200 bg-tertiary-50",
    active: "bg-tertiary-600 text-white",
    inactive: "text-tertiary-700 hover:bg-tertiary-100",
    activeCount: "bg-white/20 text-white",
    inactiveCount: "bg-tertiary-200 text-tertiary-900",
  },
};

export const statCardStyles: Record<ColorTheme, StatCardStyles> = {
  primary: { bg: "bg-primary-50", border: "border-primary-200", label: "text-primary-600", value: "text-primary-900" },
  secondary: { bg: "bg-secondary-50", border: "border-secondary-200", label: "text-secondary-600", value: "text-secondary-900" },
  tertiary: { bg: "bg-tertiary-50", border: "border-tertiary-200", label: "text-tertiary-600", value: "text-tertiary-900" },
};

export const tableStyles: Record<ColorTheme, TableStyles> = {
  primary: {
    badge: "bg-primary-600",
    header: "text-primary-600",
    mismatchRow: "bg-amber-100/70 hover:bg-amber-200/60",
    mismatchLegendDot: "bg-amber-300",
    highlightHeader: "bg-[rgba(242,191,214,0.45)]",
    highlightCell: "bg-[rgba(242,191,214,0.22)] group-hover:bg-[rgba(242,191,214,0.32)]",
  },
  secondary: {
    badge: "bg-secondary-600",
    header: "text-secondary-600",
    mismatchRow: "bg-amber-100/70 hover:bg-amber-200/60",
    mismatchLegendDot: "bg-amber-300",
    highlightHeader: "bg-[rgba(242,191,214,0.45)]",
    highlightCell: "bg-[rgba(242,191,214,0.22)] group-hover:bg-[rgba(242,191,214,0.32)]",
  },
  tertiary: {
    badge: "bg-tertiary-600",
    header: "text-tertiary-600",
    mismatchRow: "bg-amber-100/70 hover:bg-amber-200/60",
    mismatchLegendDot: "bg-amber-300",
    highlightHeader: "bg-[rgba(242,191,214,0.45)]",
    highlightCell: "bg-[rgba(242,191,214,0.22)] group-hover:bg-[rgba(242,191,214,0.32)]",
  },
};

export const filterStyles: Record<ColorTheme, FilterStyles> = {
  primary: {
    border: "border-primary-200", bg: "bg-primary-50/50", icon: "text-primary-600",
    text: "text-primary-900", textLight: "text-primary-700", chipBorder: "border-primary-300",
    hoverBg: "hover:bg-primary-100", button: "bg-primary-600 hover:bg-primary-700",
  },
  secondary: {
    border: "border-secondary-200", bg: "bg-secondary-50/50", icon: "text-secondary-600",
    text: "text-secondary-900", textLight: "text-secondary-700", chipBorder: "border-secondary-300",
    hoverBg: "hover:bg-secondary-100", button: "bg-secondary-600 hover:bg-secondary-700",
  },
  tertiary: {
    border: "border-tertiary-200", bg: "bg-tertiary-50/50", icon: "text-tertiary-600",
    text: "text-tertiary-900", textLight: "text-tertiary-700", chipBorder: "border-tertiary-300",
    hoverBg: "hover:bg-tertiary-100", button: "bg-tertiary-600 hover:bg-tertiary-700",
  },
};

export const mapStyles: Record<ColorTheme, MapStyles> = {
  primary: { border: "border-slate-200", bg: "bg-white", text: "text-primary-900" },
  secondary: { border: "border-slate-200", bg: "bg-white", text: "text-secondary-900" },
  tertiary: { border: "border-slate-200", bg: "bg-white", text: "text-tertiary-900" },
};

export const sidebarStyles: Record<ColorTheme, SidebarStyles> = {
  primary: {
    container: "bg-white border-r border-primary-200",
    sectionHeader: "text-primary-600",
    divider: "border-primary-200",
    navItemBase:
      "group flex w-full items-center gap-3 rounded-lg border-l-2 border-transparent font-semibold text-primary-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-300 focus-visible:ring-offset-2",
    navItemHover: "hover:bg-primary-50 hover:text-primary-900",
    navItemActive: "text-primary-900",
    navItemDisabled: "cursor-not-allowed opacity-50",
    activeIndicator: "border-l-primary-600 bg-primary-100/60",
    iconInactive: "text-primary-500",
    iconActive: "text-primary-700",
    badge: "bg-primary-100 text-primary-800",
    contextLabel: "text-primary-600",
    contextValue: "text-primary-900",
  },
  secondary: {
    container: "bg-white border-r border-secondary-200",
    sectionHeader: "text-secondary-600",
    divider: "border-secondary-200",
    navItemBase:
      "group flex w-full items-center gap-3 rounded-lg border-l-2 border-transparent font-semibold text-secondary-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary-300 focus-visible:ring-offset-2",
    navItemHover: "hover:bg-secondary-50 hover:text-secondary-900",
    navItemActive: "text-secondary-900",
    navItemDisabled: "cursor-not-allowed opacity-50",
    activeIndicator: "border-l-secondary-600 bg-secondary-100/60",
    iconInactive: "text-secondary-500",
    iconActive: "text-secondary-700",
    badge: "bg-secondary-100 text-secondary-800",
    contextLabel: "text-secondary-600",
    contextValue: "text-secondary-900",
  },
  tertiary: {
    container: "bg-white border-r border-tertiary-200",
    sectionHeader: "text-tertiary-600",
    divider: "border-tertiary-200",
    navItemBase:
      "group flex w-full items-center gap-3 rounded-lg border-l-2 border-transparent font-semibold text-tertiary-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tertiary-300 focus-visible:ring-offset-2",
    navItemHover: "hover:bg-tertiary-50 hover:text-tertiary-900",
    navItemActive: "text-tertiary-900",
    navItemDisabled: "cursor-not-allowed opacity-50",
    activeIndicator: "border-l-tertiary-600 bg-tertiary-100/60",
    iconInactive: "text-tertiary-500",
    iconActive: "text-tertiary-700",
    badge: "bg-tertiary-100 text-tertiary-800",
    contextLabel: "text-tertiary-600",
    contextValue: "text-tertiary-900",
  },
};

export const summaryBannerStyles: Record<ColorTheme, SummaryBannerStyles> = {
  primary: {
    container: "rounded-xl border border-primary-200 bg-primary-50 p-6",
    title: "text-primary-900",
    subtitle: "text-primary-700",
    meta: "text-primary-700",
    statusIcon: "text-primary-600",
    statusText: "text-primary-700",
    divider: "border-primary-200",
    actionButton: "rounded-xl px-5 py-2.5 text-sm",
  },
  secondary: {
    container: "rounded-xl border border-secondary-200 bg-secondary-50 p-6",
    title: "text-secondary-900",
    subtitle: "text-secondary-700",
    meta: "text-secondary-700",
    statusIcon: "text-secondary-600",
    statusText: "text-secondary-700",
    divider: "border-secondary-200",
    actionButton: "rounded-xl px-5 py-2.5 text-sm",
  },
  tertiary: {
    container: "rounded-xl border border-tertiary-200 bg-tertiary-50 p-6",
    title: "text-tertiary-900",
    subtitle: "text-tertiary-700",
    meta: "text-tertiary-700",
    statusIcon: "text-tertiary-600",
    statusText: "text-tertiary-700",
    divider: "border-tertiary-200",
    actionButton: "rounded-xl px-5 py-2.5 text-sm",
  },
};

// =============================================================================
// Norwegian Fylke Color Schemes
// Neutral color schemes for displaying Norwegian administrative regions
// =============================================================================

interface FylkeColorScheme {
  bg: string;
  border: string;
  hoverBorder: string;
  hoverShadow: string;
  text: string;
  accent: string;
  iconBg: string;
  iconText: string;
  // Button styles for kommune selection within a fylke
  buttonBorder: string;
  buttonHoverBorder: string;
  buttonHoverShadow: string;
  gradient: string;
  badge: string;
}

export const fylkeColors: Record<string, FylkeColorScheme> = {
  Oslo: {
    bg: "bg-gradient-to-br from-slate-50 to-gray-50",
    border: "border-slate-200",
    hoverBorder: "hover:border-slate-400",
    hoverShadow: "hover:shadow-slate-200/50",
    text: "text-slate-900",
    accent: "text-slate-600",
    iconBg: "bg-slate-100",
    iconText: "text-slate-700",
    buttonBorder: "border-slate-200",
    buttonHoverBorder: "hover:border-slate-400",
    buttonHoverShadow: "hover:shadow-slate-200/50",
    gradient: "from-slate-600 to-zinc-600",
    badge: "bg-slate-100 text-slate-800",
  },
  Rogaland: {
    bg: "bg-gradient-to-br from-zinc-50 to-neutral-50",
    border: "border-zinc-200",
    hoverBorder: "hover:border-zinc-400",
    hoverShadow: "hover:shadow-zinc-200/50",
    text: "text-zinc-900",
    accent: "text-zinc-600",
    iconBg: "bg-zinc-100",
    iconText: "text-zinc-700",
    buttonBorder: "border-zinc-200",
    buttonHoverBorder: "hover:border-zinc-400",
    buttonHoverShadow: "hover:shadow-zinc-200/50",
    gradient: "from-zinc-600 to-neutral-600",
    badge: "bg-zinc-100 text-zinc-800",
  },
  "Møre og Romsdal": {
    bg: "bg-gradient-to-br from-gray-50 to-slate-50",
    border: "border-gray-200",
    hoverBorder: "hover:border-gray-400",
    hoverShadow: "hover:shadow-gray-200/50",
    text: "text-gray-900",
    accent: "text-gray-600",
    iconBg: "bg-gray-100",
    iconText: "text-gray-700",
    buttonBorder: "border-gray-200",
    buttonHoverBorder: "hover:border-gray-400",
    buttonHoverShadow: "hover:shadow-gray-200/50",
    gradient: "from-gray-600 to-slate-600",
    badge: "bg-gray-100 text-gray-800",
  },
  Nordland: {
    bg: "bg-gradient-to-br from-neutral-50 to-stone-50",
    border: "border-neutral-200",
    hoverBorder: "hover:border-neutral-400",
    hoverShadow: "hover:shadow-neutral-200/50",
    text: "text-neutral-900",
    accent: "text-neutral-600",
    iconBg: "bg-neutral-100",
    iconText: "text-neutral-700",
    buttonBorder: "border-neutral-200",
    buttonHoverBorder: "hover:border-neutral-400",
    buttonHoverShadow: "hover:shadow-neutral-200/50",
    gradient: "from-neutral-600 to-stone-600",
    badge: "bg-neutral-100 text-neutral-800",
  },
  Viken: {
    bg: "bg-gradient-to-br from-stone-50 to-slate-50",
    border: "border-stone-200",
    hoverBorder: "hover:border-stone-400",
    hoverShadow: "hover:shadow-stone-200/50",
    text: "text-stone-900",
    accent: "text-stone-600",
    iconBg: "bg-stone-100",
    iconText: "text-stone-700",
    buttonBorder: "border-stone-200",
    buttonHoverBorder: "hover:border-stone-400",
    buttonHoverShadow: "hover:shadow-stone-200/50",
    gradient: "from-stone-600 to-slate-600",
    badge: "bg-stone-100 text-stone-800",
  },
  Innlandet: {
    bg: "bg-gradient-to-br from-slate-50 to-zinc-50",
    border: "border-slate-200",
    hoverBorder: "hover:border-slate-400",
    hoverShadow: "hover:shadow-slate-200/50",
    text: "text-slate-900",
    accent: "text-slate-600",
    iconBg: "bg-slate-100",
    iconText: "text-slate-700",
    buttonBorder: "border-slate-200",
    buttonHoverBorder: "hover:border-slate-400",
    buttonHoverShadow: "hover:shadow-slate-200/50",
    gradient: "from-slate-600 to-zinc-600",
    badge: "bg-slate-100 text-slate-800",
  },
  "Vestfold og Telemark": {
    bg: "bg-gradient-to-br from-zinc-50 to-gray-50",
    border: "border-zinc-200",
    hoverBorder: "hover:border-zinc-400",
    hoverShadow: "hover:shadow-zinc-200/50",
    text: "text-zinc-900",
    accent: "text-zinc-600",
    iconBg: "bg-zinc-100",
    iconText: "text-zinc-700",
    buttonBorder: "border-zinc-200",
    buttonHoverBorder: "hover:border-zinc-400",
    buttonHoverShadow: "hover:shadow-zinc-200/50",
    gradient: "from-zinc-600 to-gray-600",
    badge: "bg-zinc-100 text-zinc-800",
  },
  Agder: {
    bg: "bg-gradient-to-br from-gray-50 to-neutral-50",
    border: "border-gray-200",
    hoverBorder: "hover:border-gray-400",
    hoverShadow: "hover:shadow-gray-200/50",
    text: "text-gray-900",
    accent: "text-gray-600",
    iconBg: "bg-gray-100",
    iconText: "text-gray-700",
    buttonBorder: "border-gray-200",
    buttonHoverBorder: "hover:border-gray-400",
    buttonHoverShadow: "hover:shadow-gray-200/50",
    gradient: "from-gray-600 to-neutral-600",
    badge: "bg-gray-100 text-gray-800",
  },
  Vestland: {
    bg: "bg-gradient-to-br from-neutral-50 to-zinc-50",
    border: "border-neutral-200",
    hoverBorder: "hover:border-neutral-400",
    hoverShadow: "hover:shadow-neutral-200/50",
    text: "text-neutral-900",
    accent: "text-neutral-600",
    iconBg: "bg-neutral-100",
    iconText: "text-neutral-700",
    buttonBorder: "border-neutral-200",
    buttonHoverBorder: "hover:border-neutral-400",
    buttonHoverShadow: "hover:shadow-neutral-200/50",
    gradient: "from-neutral-600 to-zinc-600",
    badge: "bg-neutral-100 text-neutral-800",
  },
  Trøndelag: {
    bg: "bg-gradient-to-br from-stone-50 to-gray-50",
    border: "border-stone-200",
    hoverBorder: "hover:border-stone-400",
    hoverShadow: "hover:shadow-stone-200/50",
    text: "text-stone-900",
    accent: "text-stone-600",
    iconBg: "bg-stone-100",
    iconText: "text-stone-700",
    buttonBorder: "border-stone-200",
    buttonHoverBorder: "hover:border-stone-400",
    buttonHoverShadow: "hover:shadow-stone-200/50",
    gradient: "from-stone-600 to-gray-600",
    badge: "bg-stone-100 text-stone-800",
  },
  "Troms og Finnmark": {
    bg: "bg-gradient-to-br from-slate-50 to-neutral-50",
    border: "border-slate-200",
    hoverBorder: "hover:border-slate-400",
    hoverShadow: "hover:shadow-slate-200/50",
    text: "text-slate-900",
    accent: "text-slate-600",
    iconBg: "bg-slate-100",
    iconText: "text-slate-700",
    buttonBorder: "border-slate-200",
    buttonHoverBorder: "hover:border-slate-400",
    buttonHoverShadow: "hover:shadow-slate-200/50",
    gradient: "from-slate-600 to-neutral-600",
    badge: "bg-slate-100 text-slate-800",
  },
};

export const defaultFylkeColors: FylkeColorScheme = fylkeColors.Oslo;

export function getFylkeColors(fylkeName: string): FylkeColorScheme {
  return fylkeColors[fylkeName] ?? defaultFylkeColors;
}

// =============================================================================
// Quick Access Section Styles
// =============================================================================

interface QuickAccessStyles {
  container: string;
  iconWrapper: string;
  icon: string;
  title: string;
  description: string;
}

export const quickAccessStyles: Record<ColorTheme, QuickAccessStyles> = {
  primary: {
    container: "border-primary-300 bg-primary-100",
    iconWrapper: "bg-primary-200",
    icon: "text-primary-600",
    title: "text-primary-900",
    description: "text-primary-700",
  },
  secondary: {
    container: "border-secondary-300 bg-secondary-100",
    iconWrapper: "bg-secondary-200",
    icon: "text-secondary-600",
    title: "text-secondary-900",
    description: "text-secondary-700",
  },
  tertiary: {
    container: "border-tertiary-300 bg-tertiary-100",
    iconWrapper: "bg-tertiary-200",
    icon: "text-tertiary-600",
    title: "text-tertiary-900",
    description: "text-tertiary-700",
  },
};

// =============================================================================
// Action Link Styles
// =============================================================================

interface ActionLinkStyles {
  base: string;
  hover: string;
}

export const actionLinkStyles: Record<ColorTheme, ActionLinkStyles> = {
  primary: { base: "bg-primary-600", hover: "hover:bg-primary-700" },
  secondary: { base: "bg-secondary-600", hover: "hover:bg-secondary-700" },
  tertiary: { base: "bg-tertiary-600", hover: "hover:bg-tertiary-700" },
};

// =============================================================================
// AI Section Styles
// =============================================================================

interface AISectionStyles {
  container: string;
  border: string;
  title: string;
  subtitle: string;
  cardBorder: string;
  badge: string;
}

export const aiSectionStyles: Record<ColorTheme, AISectionStyles> = {
  primary: {
    container: "bg-gradient-to-br from-primary-50 to-primary-50/50",
    border: "border-primary-200",
    title: "text-primary-900",
    subtitle: "text-primary-500",
    cardBorder: "border-primary-200",
    badge: "bg-primary-600",
  },
  secondary: {
    container: "bg-gradient-to-br from-secondary-50 to-secondary-50/50",
    border: "border-secondary-200",
    title: "text-secondary-900",
    subtitle: "text-secondary-500",
    cardBorder: "border-secondary-200",
    badge: "bg-secondary-600",
  },
  tertiary: {
    container: "bg-gradient-to-br from-tertiary-50 to-tertiary-50/50",
    border: "border-tertiary-200",
    title: "text-tertiary-900",
    subtitle: "text-tertiary-500",
    cardBorder: "border-tertiary-200",
    badge: "bg-tertiary-600",
  },
};

// =============================================================================
// Input Focus Styles
// =============================================================================

interface InputFocusStyles {
  focus: string;
}

export const inputFocusStyles: Record<ColorTheme, InputFocusStyles> = {
  primary: { focus: "focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-100" },
  secondary: { focus: "focus:border-secondary-400 focus:outline-none focus:ring-2 focus:ring-secondary-100" },
  tertiary: { focus: "focus:border-tertiary-400 focus:outline-none focus:ring-2 focus:ring-tertiary-100" },
};

// =============================================================================
// Feature Card Styles
// Neutral card styles for main navigation cards (home page, data source selection)
// Matches fylke card styling for consistency
// =============================================================================

interface FeatureCardStyles {
  bg: string;
  border: string;
  hoverBorder: string;
  hoverShadow: string;
  text: string;
  textSecondary: string;
  textMuted: string;
  iconBg: string;
  iconText: string;
  infoBg: string;
  infoBorder: string;
  infoText: string;
}

/**
 * Neutral card style for feature/navigation cards.
 * Use this for home page cards and data source selection cards.
 * To customize, modify this single object.
 */
export const featureCardStyles: FeatureCardStyles = {
  bg: "bg-gradient-to-br from-slate-50 to-gray-50",
  border: "border-slate-200",
  hoverBorder: "hover:border-slate-400",
  hoverShadow: "hover:shadow-slate-200/50",
  text: "text-slate-900",
  textSecondary: "text-slate-600",
  textMuted: "text-slate-500",
  iconBg: "bg-slate-100",
  iconText: "text-slate-700",
  infoBg: "bg-slate-100/50",
  infoBorder: "border-slate-200",
  infoText: "text-slate-700",
};

// =============================================================================
// Spinner Styles
// Loading spinner color variants
// =============================================================================

type SpinnerColor = "primary" | "secondary" | "slate";

interface SpinnerColorStyles {
  border: string;
  label: string;
}

export const spinnerStyles: Record<SpinnerColor, SpinnerColorStyles> = {
  primary: {
    border: "border-primary-200 border-t-primary-600",
    label: "text-primary-700",
  },
  secondary: {
    border: "border-secondary-200 border-t-secondary-600",
    label: "text-secondary-700",
  },
  slate: {
    border: "border-slate-200 border-t-slate-600",
    label: "text-slate-700",
  },
};

// =============================================================================
// Processing Modal Styles
// Styles for the full-screen processing overlay
// =============================================================================

interface ProcessingModalStylesDef {
  border: string;
  iconBg: string;
  iconSpinner: string;
  progressBar: string;
  stageBg: string;
  stageText: string;
  activeStep: string;
}

export const processingModalStyles: ProcessingModalStylesDef = {
  border: "border-primary-300",
  iconBg: "bg-primary-100",
  iconSpinner: "text-primary-600",
  progressBar: "bg-primary-600",
  stageBg: "bg-primary-100",
  stageText: "text-primary-900",
  activeStep: "text-primary-600",
};

// =============================================================================
// Table Info Bar Styles
// Styles for table header info bars with search and stats
// =============================================================================

interface TableInfoBarStylesDef {
  container: string;
  border: string;
  divider: string;
  text: string;
  textMuted: string;
  icon: string;
  iconHover: string;
  inputBorder: string;
  inputFocus: string;
}

export const tableInfoBarStyles: Record<ColorTheme, TableInfoBarStylesDef> = {
  primary: {
    container: "bg-primary-50/50",
    border: "border-primary-200",
    divider: "bg-primary-200",
    text: "text-primary-900",
    textMuted: "text-primary-500",
    icon: "text-primary-400",
    iconHover: "hover:text-primary-600",
    inputBorder: "border-primary-200",
    inputFocus: "focus:border-primary-400 focus:ring-primary-200 focus:outline-none focus:ring-2",
  },
  secondary: {
    container: "bg-secondary-50/50",
    border: "border-secondary-200",
    divider: "bg-secondary-200",
    text: "text-secondary-900",
    textMuted: "text-secondary-500",
    icon: "text-secondary-400",
    iconHover: "hover:text-secondary-600",
    inputBorder: "border-secondary-200",
    inputFocus: "focus:border-secondary-400 focus:ring-secondary-200 focus:outline-none focus:ring-2",
  },
  tertiary: {
    container: "bg-tertiary-50/50",
    border: "border-tertiary-200",
    divider: "bg-tertiary-200",
    text: "text-tertiary-900",
    textMuted: "text-tertiary-500",
    icon: "text-tertiary-400",
    iconHover: "hover:text-tertiary-600",
    inputBorder: "border-tertiary-200",
    inputFocus: "focus:border-tertiary-400 focus:ring-tertiary-200 focus:outline-none focus:ring-2",
  },
};

// =============================================================================
// Insights Display Styles
// Styles for AI insights cards and content
// =============================================================================

interface InsightsStylesDef {
  container: string;
  border: string;
  hoverBg: string;
  hoverBorder: string;
  title: string;
  subtitle: string;
  text: string;
  iconBg: string;
  icon: string;
  badge: string;
}

export const insightsStyles: Record<ColorTheme, InsightsStylesDef> = {
  primary: {
    container: "bg-primary-50",
    border: "border-primary-200",
    hoverBg: "hover:bg-primary-50",
    hoverBorder: "hover:border-primary-300",
    title: "text-primary-900",
    subtitle: "text-primary-600",
    text: "text-primary-700",
    iconBg: "bg-primary-100",
    icon: "text-primary-600",
    badge: "bg-primary-600",
  },
  secondary: {
    container: "bg-secondary-50",
    border: "border-secondary-200",
    hoverBg: "hover:bg-secondary-50",
    hoverBorder: "hover:border-secondary-300",
    title: "text-secondary-900",
    subtitle: "text-secondary-600",
    text: "text-secondary-700",
    iconBg: "bg-secondary-100",
    icon: "text-secondary-600",
    badge: "bg-secondary-600",
  },
  tertiary: {
    container: "bg-tertiary-50",
    border: "border-tertiary-200",
    hoverBg: "hover:bg-tertiary-50",
    hoverBorder: "hover:border-tertiary-300",
    title: "text-tertiary-900",
    subtitle: "text-tertiary-600",
    text: "text-tertiary-700",
    iconBg: "bg-tertiary-100",
    icon: "text-tertiary-600",
    badge: "bg-tertiary-600",
  },
};

// =============================================================================
// Selection Card Styles
// Styles for selectable cards with selected/unselected states (e.g., kommune selection)
// =============================================================================

interface SelectionCardStyles {
  container: string;
  border: string;
  borderSelected: string;
  bgSelected: string;
  hoverBorder: string;
  hoverShadow: string;
  iconBg: string;
  iconBgHover: string;
  iconBgSelected: string;
  iconText: string;
  title: string;
  titleHover: string;
  titleSelected: string;
  selectedBadge: string;
  decoration: string;
}

/**
 * Unified neutral card styles for selection cards.
 * Uses the same slate/gray palette as featureCardStyles for visual consistency
 * across all card types (home page, BigQuery selection, fylke pages).
 */
const neutralCardStyle: SelectionCardStyles = {
  container: "bg-white",
  border: "border-slate-200",
  borderSelected: "border-slate-400",
  bgSelected: "bg-slate-100",
  hoverBorder: "hover:border-slate-400",
  hoverShadow: "hover:shadow-lg hover:shadow-slate-200/50",
  iconBg: "bg-slate-100",
  iconBgHover: "group-hover:bg-slate-200",
  iconBgSelected: "bg-slate-200",
  iconText: "text-slate-700",
  title: "text-slate-800",
  titleHover: "group-hover:text-slate-900",
  titleSelected: "text-slate-900",
  selectedBadge: "bg-slate-600",
  decoration: "bg-slate-100/50",
};

export const selectionCardStyles: Record<ColorTheme, SelectionCardStyles> = {
  primary: neutralCardStyle,
  secondary: neutralCardStyle,
  tertiary: neutralCardStyle,
};

// =============================================================================
// Kommune Ranking Styles
// Centralized styles for risk bands and category mix colors
// =============================================================================

export const riskBandStyles = {
  Green: {
    label: "Green",
    pill: "bg-emerald-100 text-emerald-800 border-emerald-200",
    dot: "bg-emerald-500",
  },
  White: {
    label: "White",
    pill: "bg-white text-slate-700 border-slate-200",
    dot: "bg-slate-400",
  },
  Yellow: {
    label: "Yellow",
    pill: "bg-amber-100 text-amber-800 border-amber-200",
    dot: "bg-amber-500",
  },
  Red: {
    label: "Red",
    pill: "bg-red-100 text-red-800 border-red-200",
    dot: "bg-red-500",
  },
} as const;

export const matchResultStyles = {
  Matched: {
    label: "Matched",
    pill: "bg-emerald-100 text-emerald-800 border-emerald-200",
    dot: "bg-emerald-500",
  },
  Unmatched: {
    label: "Unmatched",
    pill: "bg-red-100 text-red-800 border-red-200",
    dot: "bg-red-500",
  },
  Unknown: {
    label: "Unknown",
    pill: "bg-slate-100 text-slate-700 border-slate-200",
    dot: "bg-slate-400",
  },
} as const;

export const categoryMixColors = [
  "bg-primary-600",
  "bg-secondary-600",
  "bg-emerald-500",
  "bg-amber-500",
  "bg-sky-500",
  "bg-cyan-500",
  "bg-teal-500",
  "bg-slate-500",
] as const;

// =============================================================================
// Chat Bar Theme
// Centralized style tokens for the shared chat bar + send button.
// =============================================================================

export interface ChatBarTheme {
  panelBackground: string;
  panelBorder: string;
  placeholderColor: string;
  buttonBorder: string;
  buttonBackground: string;
  buttonBackgroundHover: string;
  buttonShadow: string;
  buttonShadowHover: string;
  buttonRadius: string;
  sendInnerBackground: string;
  sendIconColor: string;
}

export const chatBarThemes = {
  default: {
    panelBackground: "rgba(255, 255, 255, 0.84)",
    panelBorder: "rgba(80, 98, 124, 0.24)",
    placeholderColor: "#5f6f86",
    buttonBorder: "rgba(0, 0, 0, 0.15)",
    buttonBackground: "#2a2b2e",
    buttonBackgroundHover: "#33353a",
    buttonShadow: "0 6px 14px rgba(18, 22, 28, 0.22)",
    buttonShadowHover: "0 8px 16px rgba(18, 22, 28, 0.28)",
    buttonRadius: "999px",
    sendInnerBackground: "transparent",
    sendIconColor: "#f5f5f5",
  },
} as const satisfies Record<string, ChatBarTheme>;

export function getChatBarCssVars(theme: ChatBarTheme): Record<string, string> {
  return {
    "--chat-panel-bg": theme.panelBackground,
    "--chat-panel-border": theme.panelBorder,
    "--chat-placeholder": theme.placeholderColor,
    "--chat-btn-border": theme.buttonBorder,
    "--chat-btn-bg": theme.buttonBackground,
    "--chat-btn-bg-hover": theme.buttonBackgroundHover,
    "--chat-btn-shadow": theme.buttonShadow,
    "--chat-btn-shadow-hover": theme.buttonShadowHover,
    "--chat-btn-radius": theme.buttonRadius,
    "--chat-send-inner-bg": theme.sendInnerBackground,
    "--chat-send-icon": theme.sendIconColor,
  };
}

// =============================================================================
// Chat Workspace Theme
// Centralized style tokens for kommune selector + chat page accents.
// =============================================================================

export interface ChatWorkspaceTheme {
  selectorBackground: string;
  selectorBorder: string;
  selectorLabel: string;
  selectorText: string;
  selectorMeta: string;
  selectorFocus: string;
  selectorInputBackground: string;
  selectorDropdownBackground: string;
  selectorOptionHover: string;
  selectorOptionSelected: string;
}

export const chatWorkspaceThemes = {
  default: {
    selectorBackground: "rgba(255, 255, 255, 0.86)",
    selectorBorder: "rgba(80, 98, 124, 0.24)",
    selectorLabel: "#2b3a50",
    selectorText: "#1a2739",
    selectorMeta: "#607089",
    selectorFocus: "rgba(42, 57, 79, 0.22)",
    selectorInputBackground: "rgba(255, 255, 255, 0.96)",
    selectorDropdownBackground: "rgba(255, 255, 255, 0.98)",
    selectorOptionHover: "rgba(240, 245, 255, 0.95)",
    selectorOptionSelected: "rgba(226, 236, 255, 0.98)",
  },
} as const satisfies Record<string, ChatWorkspaceTheme>;

export function getChatWorkspaceCssVars(theme: ChatWorkspaceTheme): Record<string, string> {
  return {
    "--kommune-panel-bg": theme.selectorBackground,
    "--kommune-panel-border": theme.selectorBorder,
    "--kommune-label": theme.selectorLabel,
    "--kommune-text": theme.selectorText,
    "--kommune-meta": theme.selectorMeta,
    "--kommune-focus": theme.selectorFocus,
    "--kommune-input-bg": theme.selectorInputBackground,
    "--kommune-dropdown-bg": theme.selectorDropdownBackground,
    "--kommune-option-hover": theme.selectorOptionHover,
    "--kommune-option-selected": theme.selectorOptionSelected,
  };
}
