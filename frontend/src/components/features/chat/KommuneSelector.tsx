"use client";

import { Check, ChevronsUpDown, Loader2, MapPin } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import type { KommuneOption } from "@/components/features/chat/contracts";

interface KommuneSelectorProps {
  options: KommuneOption[];
  selectedKey: string;
  onChange: (selectedKey: string) => void;
  label?: string;
  helperText?: string;
  isLoading?: boolean;
  disabled?: boolean;
  onSubmit?: () => void;
  submitLabel?: string;
  submitDisabled?: boolean;
}

export function KommuneSelector({
  options,
  selectedKey,
  onChange,
  label = "Select Kommune",
  helperText = "Type to search and select a kommune.",
  isLoading = false,
  disabled = false,
  onSubmit,
  submitLabel = "Analyze",
  submitDisabled = false,
}: KommuneSelectorProps) {
  const [open, setOpen] = useState(false);
  const hasOptions = options.length > 0;

  const selectedOption = useMemo(
    () => options.find((option) => option.key === selectedKey) || null,
    [options, selectedKey],
  );

  return (
    <section
      className="overflow-visible rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
      aria-label="Kommune selector"
    >
      <div className="mb-3 flex items-center justify-between">
        <label className="text-xs font-bold uppercase tracking-wider text-slate-500">
          {label}
        </label>
        {isLoading && (
          <span className="inline-flex items-center gap-1.5 text-xs text-slate-400">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Loading...
          </span>
        )}
      </div>

      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between rounded-xl border-slate-200 bg-white text-sm font-normal text-slate-800 hover:bg-white hover:border-slate-300"
            disabled={disabled || !hasOptions}
          >
            {selectedOption
              ? selectedOption.label
              : hasOptions
                ? "Search kommune..."
                : "No kommune files found"}
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-(--radix-popover-trigger-width) p-0" align="start">
          <Command>
            <CommandInput placeholder="Search kommune..." />
            <CommandList>
              <CommandEmpty>No kommune matches your search.</CommandEmpty>
              {options.map((option) => (
                <CommandItem
                  key={option.key}
                  value={option.label}
                  onSelect={() => {
                    onChange(option.key);
                    setOpen(false);
                  }}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      selectedKey === option.key ? "opacity-100" : "opacity-0",
                    )}
                  />
                  {option.label}
                </CommandItem>
              ))}
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>

      {selectedOption && !open && (
        <div className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700">
          <MapPin className="h-3 w-3" />
          {selectedOption.label}
        </div>
      )}

      {!isLoading && helperText && !selectedOption && (
        <p className="mt-2.5 text-xs text-slate-400">{helperText}</p>
      )}

      {onSubmit && (
        <div className="mt-4 border-t border-slate-100 pt-4">
          <Button
            onClick={onSubmit}
            disabled={submitDisabled}
            className="w-full rounded-xl bg-slate-800 px-5 py-3 text-sm font-semibold text-white shadow-sm hover:bg-slate-900 active:translate-y-px disabled:hover:bg-slate-800"
          >
            {submitLabel}
          </Button>
        </div>
      )}
    </section>
  );
}
