"use client";

import { Search, X } from "lucide-react";

import { Input } from "@/components/ui/input";
import type { ColorTheme } from "@/components/shared/themes";
import { searchBarStyles } from "@/components/shared/themes";
import { cn } from "@/lib/utils";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onFocus?: () => void;
  onBlur?: () => void;
  onKeyDown?: React.KeyboardEventHandler<HTMLInputElement>;
  placeholder?: string;
  colorTheme?: ColorTheme;
}

export function SearchBar({
  value,
  onChange,
  onFocus,
  onBlur,
  onKeyDown,
  placeholder = "Search...",
  colorTheme = "primary",
}: SearchBarProps) {
  const styles = searchBarStyles[colorTheme];

  return (
    <div className="relative">
      <Search className={cn("absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2", styles.icon)} />
      <Input
        type="text"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onFocus={onFocus}
        onBlur={onBlur}
        onKeyDown={onKeyDown}
        placeholder={placeholder}
        className={cn("w-full rounded-xl py-2.5 pl-10 pr-9", styles.input, styles.text)}
        autoComplete="off"
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange("")}
          className={cn("absolute right-3 top-1/2 -translate-y-1/2", styles.clear)}
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
