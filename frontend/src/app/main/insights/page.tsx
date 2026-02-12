"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

import { KommuneInsightsView } from "@/components/features/insights/KommuneInsightsView";

function KommuneInsightsContent() {
  const searchParams = useSearchParams();
  const kommune = searchParams.get("kommune") || "";

  return <KommuneInsightsView kommune={kommune} />;
}

export default function KommuneInsightsPage() {
  return (
    <Suspense fallback={<p className="p-6 text-sm text-slate-500">Loading...</p>}>
      <KommuneInsightsContent />
    </Suspense>
  );
}
