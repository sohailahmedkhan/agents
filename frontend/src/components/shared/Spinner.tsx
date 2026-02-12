"use client";

import { spinnerStyles } from "@/components/shared/themes";
import { cn } from "@/lib/utils";

type SpinnerSize = "sm" | "md" | "lg";
type SpinnerColor = "primary" | "secondary" | "slate";

interface SpinnerProps {
  size?: SpinnerSize;
  color?: SpinnerColor;
  label?: string;
  className?: string;
}

const sizeClasses: Record<SpinnerSize, string> = {
  sm: "h-4 w-4 border-2",
  md: "h-6 w-6 border-2",
  lg: "h-8 w-8 border-[3px]",
};

export function Spinner({ size = "md", color = "primary", label, className }: SpinnerProps) {
  const styles = spinnerStyles[color];

  return (
    <div className={cn("inline-flex items-center gap-2", className)}>
      <div className={cn("animate-spin rounded-full", sizeClasses[size], styles.border)} />
      {label && <span className={cn("text-sm", styles.label)}>{label}</span>}
    </div>
  );
}
