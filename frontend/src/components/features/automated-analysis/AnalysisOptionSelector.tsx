/**
 * Multi-select analysis options for the automated analysis workflow.
 */

"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import type { AgentAnalysisOption } from "@/types";

interface AnalysisOptionSelectorProps {
  options: AgentAnalysisOption[];
  selectedKeys: string[];
  onToggle: (key: string) => void;
  disabled?: boolean;
}

export function AnalysisOptionSelector({
  options,
  selectedKeys,
  onToggle,
  disabled = false,
}: AnalysisOptionSelectorProps) {
  return (
    <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3">
      {options.map((option) => {
        const selected = selectedKeys.includes(option.key);
        return (
          <Card
            key={option.key}
            className={cn(
              "group relative cursor-pointer border-2 py-0 transition-all duration-200",
              selected
                ? "border-primary-500 bg-primary-50 shadow-sm ring-2 ring-primary-100"
                : "border-slate-200 bg-white hover:border-slate-300 hover:shadow-md",
              disabled && "cursor-not-allowed opacity-60",
            )}
            onClick={() => !disabled && onToggle(option.key)}
          >
            <CardContent className="flex items-start justify-between gap-3 px-5 py-4">
              <div className="min-w-0 flex-1">
                <p className={cn("text-sm font-semibold leading-snug", selected ? "text-primary-900" : "text-slate-800")}>
                  {option.label}
                </p>
                <p className={cn("mt-1.5 text-xs leading-relaxed", selected ? "text-primary-700" : "text-slate-600")}>
                  {option.description}
                </p>
              </div>
              <div className="shrink-0 pt-0.5">
                <Checkbox checked={selected} className="pointer-events-none" />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
