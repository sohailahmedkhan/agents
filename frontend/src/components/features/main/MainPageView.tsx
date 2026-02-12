"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { KommuneSelector } from "@/components/features/chat/KommuneSelector";
import type { KommuneOption } from "@/components/features/chat/contracts";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8101";

interface KommuneListResponse {
  kommuner?: KommuneOption[];
  detail?: string;
}

export function MainPageView() {
  const router = useRouter();
  const [kommuner, setKommuner] = useState<KommuneOption[]>([]);
  const [selectedKommuneKey, setSelectedKommuneKey] = useState("");
  const [isLoadingKommuner, setIsLoadingKommuner] = useState(true);
  const [errorText, setErrorText] = useState("");

  const canAnalyze = useMemo(
    () => !isLoadingKommuner && selectedKommuneKey.trim().length > 0,
    [isLoadingKommuner, selectedKommuneKey]
  );

  useEffect(() => {
    const controller = new AbortController();

    const loadKommuner = async () => {
      setIsLoadingKommuner(true);
      setErrorText("");

      try {
        const response = await fetch(`${API_URL}/agents/kommuner`, { signal: controller.signal });
        const payload = (await response.json()) as KommuneListResponse;

        if (!response.ok) {
          throw new Error(payload.detail || "Failed to load kommune options.");
        }

        const options = Array.isArray(payload.kommuner) ? payload.kommuner : [];
        setKommuner(options);
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          const message = error instanceof Error ? error.message : "Unexpected kommune loading error.";
          setErrorText(message);
        }
      } finally {
        setIsLoadingKommuner(false);
      }
    };

    void loadKommuner();

    return () => {
      controller.abort();
    };
  }, []);

  const handleAnalyze = () => {
    if (!canAnalyze) {
      setErrorText("Select a kommune before running analysis.");
      return;
    }
    router.push(`/main/insights?kommune=${encodeURIComponent(selectedKommuneKey)}`);
  };

  return (
    <main className="flex min-h-dvh items-center justify-center bg-slate-50 px-4 py-8 sm:px-6 lg:px-10">
      <section className="w-full max-w-lg">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-slate-800">Select Kommune</h1>
          <p className="mt-1 text-sm text-slate-500">Choose a kommune to begin your analysis</p>
        </div>

        <KommuneSelector
          options={kommuner}
          selectedKey={selectedKommuneKey}
          onChange={setSelectedKommuneKey}
          isLoading={isLoadingKommuner}
          disabled={isLoadingKommuner}
          label="Kommune"
          helperText="Search and choose a kommune, then run Analyze."
          onSubmit={handleAnalyze}
          submitLabel="Analyze"
          submitDisabled={!canAnalyze}
        />

        {errorText ? (
          <p className="mt-3 text-center text-sm text-red-600">{errorText}</p>
        ) : null}
      </section>
    </main>
  );
}
