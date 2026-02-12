"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight, Bot, Database } from "lucide-react";

import {
  Alert,
  Button,
  PageHeader,
  SearchBar,
  Spinner,
  SummaryBanner,
} from "@/components";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
  AnalysisOptionSelector,
  AnalysisResultsPanel,
} from "@/components/features/automated-analysis";
import type { KommuneScore, ScoringSummary } from "@/components/features/kommune-occ-rankings/types";
import { selectionCardStyles } from "@/components/shared/themes";
import { useDashboardDataSource } from "@/hooks";
import { API_URL } from "@/lib/api";
import type { AgentAnalysisOption, AgentChatResponse } from "@/types";

const decimalFormatter = new Intl.NumberFormat("nb-NO", { maximumFractionDigits: 1 });
const SUGGESTION_LIMIT = 8;

const ui = {
  panel: "rounded-xl border border-slate-200 bg-white p-6",
  title: "text-lg font-semibold text-slate-800",
  textMuted: "text-slate-500",
};

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === "string") return payload.detail;
    return JSON.stringify(payload);
  } catch {
    return `Request failed with status ${response.status}`;
  }
}

interface KommuneSuggestionsProps {
  suggestions: KommuneScore[];
  selectedKommuneName: string | null;
  onSelect: (kommuneName: string) => void;
}

function KommuneSuggestions({ suggestions, selectedKommuneName, onSelect }: KommuneSuggestionsProps) {
  const styles = selectionCardStyles.primary;

  return (
    <div className={`mt-3 rounded-xl border ${styles.border} bg-white p-2`}>
      <ul className="space-y-1">
        {suggestions.map((item) => {
          const selected = selectedKommuneName?.toLowerCase() === item.kommune.toLowerCase();
          return (
            <li key={item.kommune}>
              <button
                type="button"
                onClick={() => onSelect(item.kommune)}
                className={`flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left text-sm transition-colors ${
                  selected
                    ? `${styles.borderSelected} ${styles.bgSelected} ${styles.titleSelected}`
                    : `${styles.border} ${styles.container} ${styles.title} ${styles.hoverBorder}`
                }`}
              >
                <span className="font-semibold">{item.kommune}</span>
                <span className={`text-xs ${"text-slate-600"}`}>
                  {decimalFormatter.format(item.total_bruksareal)} m2
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default function AutomatedAnalysisPage() {
  const { setDataSource } = useDashboardDataSource();
  const [loadingKommuner, setLoadingKommuner] = useState(true);
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [kommuneOptions, setKommuneOptions] = useState<KommuneScore[]>([]);
  const [analysisOptions, setAnalysisOptions] = useState<AgentAnalysisOption[]>([]);
  const [kommuneQuery, setKommuneQuery] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedKommuneName, setSelectedKommuneName] = useState<string | null>(null);
  const [selectedAnalyses, setSelectedAnalyses] = useState<string[]>([]);
  const [useLlmSummary, setUseLlmSummary] = useState(true);
  const [running, setRunning] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [optionsError, setOptionsError] = useState<string | null>(null);
  const [agentResponse, setAgentResponse] = useState<AgentChatResponse | null>(null);

  useEffect(() => {
    setDataSource("raw");
  }, [setDataSource]);

  useEffect(() => {
    let mounted = true;

    const loadKommuner = async () => {
      setLoadingKommuner(true);
      setLoadError(null);
      try {
        const url = new URL(`${API_URL}/kommune-occ-rankings/summary`);
        url.searchParams.set("data_source", "raw");
        const response = await fetch(url.toString());
        if (!response.ok) throw new Error(await readErrorMessage(response));
        const payload: ScoringSummary = await response.json();
        const next = [...(payload.kommuner || [])].sort((a, b) => a.kommune.localeCompare(b.kommune, "nb"));
        if (mounted) setKommuneOptions(next);
      } catch (error) {
        if (mounted) setLoadError(error instanceof Error ? error.message : "Failed to load kommune list.");
      } finally {
        if (mounted) setLoadingKommuner(false);
      }
    };

    const loadAnalysisOptions = async () => {
      setLoadingOptions(true);
      setOptionsError(null);
      try {
        const response = await fetch(`${API_URL}/agents/analysis-options`);
        if (!response.ok) throw new Error(await readErrorMessage(response));
        const payload = await response.json();
        const options = Array.isArray(payload?.options) ? (payload.options as AgentAnalysisOption[]) : [];
        if (mounted) setAnalysisOptions(options);
      } catch (error) {
        if (mounted) setOptionsError(error instanceof Error ? error.message : "Failed to load analysis options.");
      } finally {
        if (mounted) setLoadingOptions(false);
      }
    };

    loadKommuner();
    loadAnalysisOptions();
    return () => {
      mounted = false;
    };
  }, []);

  const normalizedQuery = kommuneQuery.trim().toLowerCase();
  const kommuneSuggestions = useMemo(() => {
    if (!normalizedQuery) return [];
    return kommuneOptions
      .filter((row) => row.kommune.toLowerCase().includes(normalizedQuery))
      .slice(0, SUGGESTION_LIMIT);
  }, [normalizedQuery, kommuneOptions]);

  useEffect(() => {
    if (!normalizedQuery) return;
    const exact = kommuneOptions.find((item) => item.kommune.toLowerCase() === normalizedQuery);
    if (exact) setSelectedKommuneName(exact.kommune);
  }, [normalizedQuery, kommuneOptions]);

  const selectedKommuneMeta = useMemo(
    () => kommuneOptions.find((item) => item.kommune.toLowerCase() === (selectedKommuneName || "").toLowerCase()) || null,
    [kommuneOptions, selectedKommuneName]
  );

  const selectedSections = useMemo(() => {
    const sections = agentResponse?.analysis_sections;
    if (!Array.isArray(sections)) return [];
    return sections.filter((section) => selectedAnalyses.includes(section.key));
  }, [agentResponse, selectedAnalyses]);

  const displayedSummary = useMemo(() => {
    const llmText =
      typeof agentResponse?.llm_summary?.text === "string" ? agentResponse.llm_summary.text.trim() : "";
    if (useLlmSummary && llmText) return llmText;
    return agentResponse?.summary || "";
  }, [agentResponse, useLlmSummary]);

  const handleSelectKommune = (kommuneName: string) => {
    setSelectedKommuneName(kommuneName);
    setKommuneQuery(kommuneName);
    setShowSuggestions(false);
    setAnalysisError(null);
    setAgentResponse(null);
  };

  const handleSearchKeyDown: React.KeyboardEventHandler<HTMLInputElement> = (event) => {
    if (event.key === "Escape") {
      setShowSuggestions(false);
      return;
    }
    if (event.key !== "Enter" || kommuneSuggestions.length === 0) return;
    event.preventDefault();
    handleSelectKommune(kommuneSuggestions[0].kommune);
  };

  const toggleAnalysisKey = (key: string) => {
    setSelectedAnalyses((prev) => {
      if (prev.includes(key)) return prev.filter((item) => item !== key);
      return [...prev, key];
    });
    setAgentResponse(null);
    setAnalysisError(null);
  };

  const clearSelectedAnalyses = () => {
    setSelectedAnalyses([]);
    setAgentResponse(null);
    setAnalysisError(null);
  };

  const handleRunWorkflow = async () => {
    if (!selectedKommuneMeta) {
      setAnalysisError("Select a valid kommune before running analysis.");
      return;
    }
    if (!selectedAnalyses.length) {
      setAnalysisError("Select at least one analysis option.");
      return;
    }

    setRunning(true);
    setAnalysisError(null);
    setAgentResponse(null);

    try {
      const response = await fetch(`${API_URL}/agents/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: "",
          workflow: "kommune_match_overview",
          kommune_name: selectedKommuneMeta.kommune,
          data_source: "raw",
          requested_analyses: selectedAnalyses,
          use_llm: useLlmSummary,
          include_mcp_resources: false,
        }),
      });
      if (!response.ok) throw new Error(await readErrorMessage(response));
      const payload: AgentChatResponse = await response.json();
      setAgentResponse(payload);
    } catch (error) {
      setAnalysisError(error instanceof Error ? error.message : "Failed to run automated analysis.");
    } finally {
      setRunning(false);
    }
  };

  const shouldShowSuggestions = showSuggestions && normalizedQuery.length > 0 && kommuneSuggestions.length > 0;
  const loadingAny = loadingKommuner || loadingOptions;

  return (
    <main className="mx-auto max-w-7xl px-6 py-16">
      <PageHeader
        title="Automated Analysis"
        subtitle="Choose a kommune and select exactly which analyses to run."
        backLink={{ href: "/", label: "Back to Home" }}
      />

      <div className="mt-6">
        <Alert
          type="info"
          title="Scope locked for now"
          message="This workflow uses raw Kartverket data and runs only selected analysis buttons."
          details="Output will include exactly the selected analyses."
        />
      </div>

      {selectedKommuneMeta && (
        <SummaryBanner
          className="mt-8"
          title={selectedKommuneMeta.kommune}
          description="Selected kommune for ownership workflow"
          meta={`Portfolio area: ${decimalFormatter.format(selectedKommuneMeta.total_bruksareal)} m2`}
          actions={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setSelectedKommuneName(null);
                setShowSuggestions(true);
                setAnalysisError(null);
              }}
            >
              Change selection
            </Button>
          }
        />
      )}

      <section className={`mt-8 ${ui.panel}`}>
        <div className="flex items-center gap-2">
          <Database className="h-4 w-4 text-primary-700" />
          <h2 className={ui.title}>Run Ownership Workflow</h2>
        </div>

        {loadingAny ? (
          <div className={`mt-6 flex items-center gap-3 ${ui.textMuted}`}>
            <Spinner size="md" color="primary" />
            <span className="text-sm">Loading kommune and analysis options...</span>
          </div>
        ) : (
          <>
            <div className="mt-5">
              <label className={`mb-2 block text-xs font-semibold uppercase tracking-wide ${ui.textMuted}`}>
                Search Kommune
              </label>
              <SearchBar
                value={kommuneQuery}
                onChange={(value) => {
                  setKommuneQuery(value);
                  setShowSuggestions(true);
                  if (selectedKommuneName && value.trim().toLowerCase() !== selectedKommuneName.toLowerCase()) {
                    setSelectedKommuneName(null);
                  }
                }}
                onFocus={() => setShowSuggestions(true)}
                onBlur={() => window.setTimeout(() => setShowSuggestions(false), 120)}
                onKeyDown={handleSearchKeyDown}
                placeholder="Type a kommune name and pick a suggestion"
                colorTheme="primary"
              />
              {shouldShowSuggestions && (
                <KommuneSuggestions
                  suggestions={kommuneSuggestions}
                  selectedKommuneName={selectedKommuneName}
                  onSelect={handleSelectKommune}
                />
              )}
              {showSuggestions && normalizedQuery.length > 0 && kommuneSuggestions.length === 0 && (
                <p className={`mt-2 text-xs ${ui.textMuted}`}>No kommune matched that search.</p>
              )}
            </div>

            <div className="mt-5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <label className={`block text-xs font-semibold uppercase tracking-wide ${ui.textMuted}`}>
                  Select Analyses
                </label>
                <div className="inline-flex items-center gap-2">
                  <span className={`text-xs ${ui.textMuted}`}>{selectedAnalyses.length} selected</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearSelectedAnalyses}
                    disabled={!selectedAnalyses.length || running}
                  >
                    Clear selected analyses
                  </Button>
                </div>
              </div>
              <AnalysisOptionSelector
                options={analysisOptions}
                selectedKeys={selectedAnalyses}
                onToggle={toggleAnalysisKey}
                disabled={running}
              />
            </div>

            <label className="mt-5 inline-flex items-center gap-2 text-sm text-slate-600">
              <Checkbox
                checked={useLlmSummary}
                onCheckedChange={(checked) => {
                  setUseLlmSummary(checked === true);
                  setAgentResponse(null);
                  setAnalysisError(null);
                }}
                disabled={running}
              />
              Use Claude summary for final response
            </label>

            <div className="mt-5 flex flex-wrap items-center gap-3">
              <Button
                onClick={handleRunWorkflow}
                disabled={!selectedKommuneMeta || !selectedAnalyses.length || running}
                loading={running}
                leftIcon={<Bot className="h-4 w-4" />}
              >
                Run Automated Analysis
              </Button>
              <Link
                href="/kommune-portfolios"
                className="inline-flex items-center gap-1 text-sm font-semibold text-primary-700 hover:text-primary-800"
              >
                Open Kommune Portfolios explorer
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </>
        )}

        {loadError && <Alert className="mt-5" type="error" title="Failed to load kommuner" message={loadError} />}
        {optionsError && <Alert className="mt-5" type="error" title="Failed to load analysis options" message={optionsError} />}
        {analysisError && <Alert className="mt-5" type="error" title="Workflow failed" message={analysisError} />}
      </section>

      {agentResponse && (
        <section className="mt-8 space-y-6">
          <Card>
            <CardContent>
              <h3 className={ui.title}>Automated Summary</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">{displayedSummary}</p>
              {useLlmSummary && agentResponse.llm_summary?.error && (
                <Alert
                  className="mt-4"
                  type="warning"
                  title="Claude summary unavailable"
                  message={agentResponse.llm_summary.error}
                />
              )}
            </CardContent>
          </Card>

          <AnalysisResultsPanel sections={selectedSections} />
        </section>
      )}
    </main>
  );
}
