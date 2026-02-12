/**
 * Sectioned output cards for selected automated analyses.
 */

"use client";

import { AlertCircle, CheckCircle2, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import type { AgentAnalysisSection } from "@/types";

function toCellValue(value: unknown): string {
  if (value === null || value === undefined) return "-";
  if (typeof value === "number") return Number.isFinite(value) ? value.toLocaleString("nb-NO") : "-";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

function scalarEntries(data: Record<string, unknown>): Array<[string, string]> {
  return Object.entries(data)
    .filter(([, value]) => ["string", "number", "boolean"].includes(typeof value) || value === null)
    .slice(0, 6)
    .map(([key, value]) => [key, toCellValue(value)]);
}

interface AnalysisResultsPanelProps {
  sections: AgentAnalysisSection[];
}

function extractRows(data: Record<string, unknown> | null): Array<Record<string, unknown>> {
  if (!data) return [];
  if (Array.isArray(data.rows)) return data.rows as Array<Record<string, unknown>>;

  const rowLikeKeys = [
    "top_occupancy_categories",
    "largest_properties",
    "top_ownership_groups",
    "top_building_types",
    "critical_columns",
    "top_contributors",
  ];
  for (const key of rowLikeKeys) {
    const value = data[key];
    if (Array.isArray(value)) return value as Array<Record<string, unknown>>;
  }
  return [];
}

export function AnalysisResultsPanel({ sections }: AnalysisResultsPanelProps) {
  if (!sections.length) return null;

  return (
    <section className="space-y-5">
      {sections.map((section) => {
        const data = section.data && typeof section.data === "object" ? section.data : null;
        const rows = extractRows(data as Record<string, unknown> | null);
        const rowColumns = rows.length > 0 ? Object.keys(rows[0] || {}).slice(0, 5) : [];
        const metrics = data ? scalarEntries(data as Record<string, unknown>) : [];
        const isOk = section.status === "ok";

        return (
          <Card key={section.key} className="transition-shadow duration-200 hover:shadow-md">
            <CardContent>
              <div className="flex items-start gap-3">
                <div className="mt-0.5 inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary-100">
                  {isOk ? <Sparkles className="h-4 w-4 text-primary-700" /> : <AlertCircle className="h-4 w-4 text-amber-700" />}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-semibold text-slate-800">{section.title}</h3>
                    {isOk ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    ) : (
                      <Badge variant="outline" className="border-amber-200 bg-amber-50 text-amber-700">
                        {section.status}
                      </Badge>
                    )}
                  </div>
                  <p className="mt-2 text-sm text-slate-600">{section.summary}</p>
                </div>
              </div>

              {metrics.length > 0 && (
                <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {metrics.map(([key, value]) => (
                    <div key={key} className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 transition-colors hover:bg-slate-100/70">
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{key}</p>
                      <p className="mt-1.5 text-sm font-semibold text-slate-800">{value}</p>
                    </div>
                  ))}
                </div>
              )}

              {rows.length > 0 && rowColumns.length > 0 && (
                <div className="mt-4">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {rowColumns.map((column) => (
                          <TableHead key={column} className="text-[11px] uppercase tracking-wide">
                            {column}
                          </TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {rows.slice(0, 6).map((row, index) => (
                        <TableRow key={`${section.key}-row-${index}`}>
                          {rowColumns.map((column) => (
                            <TableCell key={column} className={cn("text-slate-600")}>
                              {toCellValue(row[column])}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </section>
  );
}
