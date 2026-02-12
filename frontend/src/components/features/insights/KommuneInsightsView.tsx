"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import { EChart } from "@/components/shared";
import { InsightsChatPanel } from "@/components/features/insights/InsightsChatPanel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8101";

interface OccupancyDistributionRow {
  occupancy_category?: string;
  building_count?: number;
  total_bruksareal?: number;
  share_percent?: number;
  count_share_percent?: number;
  area_share_percent?: number;
}

interface LargestOccupancyRow {
  occupancy_category?: string;
  building_count?: number;
  total_bruksareal?: number;
}

interface ExposureKommuneRow {
  kommune?: string;
  property_count?: number;
  total_bruksareal?: number;
  property_share_percent?: number;
  area_share_percent?: number;
  is_selected?: boolean;
}

interface ExposureTopPropertyRow {
  rank?: number;
  kommune?: string;
  address_label?: string;
  occupancy_category?: string;
  bygningsstatus?: string;
  tek_standard?: string;
  total_bruksareal?: number;
  area_share_percent?: number;
}

interface ExposureDashboard {
  portfolio_total_properties?: number;
  portfolio_total_bruksareal?: number;
  selected_kommune_properties?: number;
  selected_kommune_bruksareal?: number;
  selected_property_share_percent?: number;
  selected_area_share_percent?: number;
  by_kommune?: ExposureKommuneRow[];
  concentration?: {
    top5_area?: number;
    top5_share_percent?: number;
    top10_area?: number;
    top10_share_percent?: number;
  };
  top_properties_by_area?: ExposureTopPropertyRow[];
}

interface AgeBandRow {
  age_band?: string;
  property_count?: number;
  total_bruksareal?: number;
  area_share_percent?: number;
}

interface TekDistributionRow {
  tek_standard?: string;
  property_count?: number;
  total_bruksareal?: number;
  property_share_percent?: number;
  area_share_percent?: number;
}

interface StatusDistributionRow {
  bygningsstatus?: string;
  property_count?: number;
  total_bruksareal?: number;
  property_share_percent?: number;
  area_share_percent?: number;
}

interface PropertyRiskRow {
  rank?: number;
  kommune?: string;
  address_label?: string;
  occupancy_category?: string;
  bygningsstatus?: string;
  tek_standard?: string;
  total_bruksareal?: number;
}

interface HeritageRow {
  kommune?: string;
  address_label?: string;
  occupancy_category?: string;
  total_bruksareal?: number;
  har_sefrakminne?: number;
  har_kulturminne?: number;
  skjermingsverdig?: number;
}

interface TenantTopRow {
  kommune?: string;
  address_label?: string;
  occupancy_category?: string;
  antall_underenheter?: number;
  total_bruksareal?: number;
  antall_eiere?: number;
  underenheter?: string;
}

interface QualityFieldRow {
  field?: string;
  label?: string;
  present_count?: number;
  missing_count?: number;
  completeness_percent?: number;
}

interface UnderwritingPayload {
  exposure_dashboard?: ExposureDashboard;
  occupancy_risk_mix?: {
    by_category?: OccupancyDistributionRow[];
    top_categories_by_area?: OccupancyDistributionRow[];
    top_categories_by_count?: OccupancyDistributionRow[];
  };
  age_standard_proxy?: {
    tek_distribution?: TekDistributionRow[];
    age_band_distribution?: AgeBandRow[];
  };
  status_underwriting?: {
    distribution?: StatusDistributionRow[];
    problematic_statuses?: string[];
    problematic_properties?: PropertyRiskRow[];
  };
  large_risk_schedule?: {
    rows?: PropertyRiskRow[];
  };
  heritage_flags?: {
    summary?: {
      sefrak_count?: number;
      kulturminne_count?: number;
      skjermingsverdig_count?: number;
      any_flag_count?: number;
    };
    rows?: HeritageRow[];
  };
  tenant_activity_proxy?: {
    summary?: {
      total_properties?: number;
      with_tenants_count?: number;
      with_tenants_share_percent?: number;
      with_tenants_area?: number;
      max_underenheter?: number;
      multi_owner_count?: number;
    };
    top_rows?: TenantTopRow[];
  };
  data_quality?: {
    score_percent?: number;
    total_properties?: number;
    fields?: QualityFieldRow[];
    gaps?: QualityFieldRow[];
  };
}

interface KommuneInsightsResponse {
  kommune?: string;
  occupancy_distribution?: {
    rows?: OccupancyDistributionRow[];
  };
  largest_occupancy?: {
    row?: LargestOccupancyRow | null;
  };
  underwriting?: UnderwritingPayload;
  detail?: string;
}

interface KommuneInsightsViewProps {
  kommune: string;
}

interface TooltipItem {
  name?: string;
  marker?: string;
  dataIndex?: number;
}

const nf0 = new Intl.NumberFormat("nb-NO", { maximumFractionDigits: 0 });
const nf1 = new Intl.NumberFormat("nb-NO", { maximumFractionDigits: 1 });
const nf2 = new Intl.NumberFormat("nb-NO", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function asNumber(value: unknown): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatCount(value: unknown): string {
  return nf0.format(asNumber(value));
}

function formatArea(value: unknown): string {
  return nf1.format(asNumber(value));
}

function formatPercent(value: unknown): string {
  return `${nf2.format(asNumber(value))}%`;
}

function textValue(value: unknown, fallback = "N/A"): string {
  if (typeof value === "string" && value.trim()) return value;
  return fallback;
}

export function KommuneInsightsView({ kommune }: KommuneInsightsViewProps) {
  const [data, setData] = useState<KommuneInsightsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorText, setErrorText] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    const loadInsights = async () => {
      setIsLoading(true);
      setErrorText("");

      try {
        const response = await fetch(
          `${API_URL}/agents/kommune-insights?kommune=${encodeURIComponent(kommune)}`,
          { signal: controller.signal }
        );
        const payload = (await response.json()) as KommuneInsightsResponse;

        if (!response.ok) {
          throw new Error(payload.detail || "Failed to load kommune insights.");
        }
        setData(payload);
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          const message = error instanceof Error ? error.message : "Unexpected insights loading error.";
          setErrorText(message);
        }
      } finally {
        setIsLoading(false);
      }
    };

    if (kommune.trim()) {
      void loadInsights();
    } else {
      setIsLoading(false);
      setErrorText("Missing kommune selection.");
    }

    return () => {
      controller.abort();
    };
  }, [kommune]);

  const underwriting = data?.underwriting;
  const exposure = underwriting?.exposure_dashboard;
  const occupancyRows = useMemo(() => {
    if (Array.isArray(underwriting?.occupancy_risk_mix?.by_category)) {
      return underwriting.occupancy_risk_mix.by_category;
    }
    if (Array.isArray(data?.occupancy_distribution?.rows)) {
      return data.occupancy_distribution.rows;
    }
    return [];
  }, [data, underwriting]);
  const largestOccupancy = data?.largest_occupancy?.row || null;
  const occupancyTopByArea = Array.isArray(underwriting?.occupancy_risk_mix?.top_categories_by_area)
    ? underwriting.occupancy_risk_mix.top_categories_by_area
    : occupancyRows.slice(0, 10);
  const occupancyTopByCount = Array.isArray(underwriting?.occupancy_risk_mix?.top_categories_by_count)
    ? underwriting.occupancy_risk_mix.top_categories_by_count
    : [...occupancyRows]
        .sort((a, b) => asNumber(b.building_count) - asNumber(a.building_count))
        .slice(0, 10);
  const ageBands = useMemo(
    () =>
      Array.isArray(underwriting?.age_standard_proxy?.age_band_distribution)
        ? underwriting.age_standard_proxy.age_band_distribution
        : [],
    [underwriting?.age_standard_proxy?.age_band_distribution]
  );
  const tekDistribution = useMemo(
    () =>
      Array.isArray(underwriting?.age_standard_proxy?.tek_distribution)
        ? underwriting.age_standard_proxy.tek_distribution
        : [],
    [underwriting?.age_standard_proxy?.tek_distribution]
  );
  const statusDistribution = useMemo(
    () =>
      Array.isArray(underwriting?.status_underwriting?.distribution)
        ? underwriting.status_underwriting.distribution
        : [],
    [underwriting?.status_underwriting?.distribution]
  );
  const problematicStatuses = Array.isArray(underwriting?.status_underwriting?.problematic_statuses)
    ? underwriting.status_underwriting.problematic_statuses
    : [];
  const problematicProperties = Array.isArray(underwriting?.status_underwriting?.problematic_properties)
    ? underwriting.status_underwriting.problematic_properties
    : [];
  const largeRiskRows = Array.isArray(underwriting?.large_risk_schedule?.rows) ? underwriting.large_risk_schedule.rows : [];
  const heritageRows = Array.isArray(underwriting?.heritage_flags?.rows) ? underwriting.heritage_flags.rows : [];
  const tenantSummary = underwriting?.tenant_activity_proxy?.summary;
  const tenantTopRows = Array.isArray(underwriting?.tenant_activity_proxy?.top_rows)
    ? underwriting.tenant_activity_proxy.top_rows
    : [];
  const qualityFields = useMemo(
    () => (Array.isArray(underwriting?.data_quality?.fields) ? underwriting.data_quality.fields : []),
    [underwriting?.data_quality?.fields]
  );
  const withTenantsSharePercent = useMemo(() => {
    const direct = asNumber(tenantSummary?.with_tenants_share_percent);
    if (direct > 0) return direct;
    const total = asNumber(tenantSummary?.total_properties);
    const withTenants = asNumber(tenantSummary?.with_tenants_count);
    if (total <= 0) return 0;
    return (100 * withTenants) / total;
  }, [tenantSummary?.total_properties, tenantSummary?.with_tenants_count, tenantSummary?.with_tenants_share_percent]);

  const occupancyAreaShareOption = useMemo(() => {
    const categories = occupancyRows.map((row) => textValue(row.occupancy_category));
    const values = occupancyRows.map((row) => asNumber(row.area_share_percent ?? row.share_percent));
    return {
      tooltip: {
        trigger: "axis" as const,
        formatter: (raw: unknown) => {
          const item = (Array.isArray(raw) ? raw[0] : raw) as TooltipItem;
          const row =
            typeof item?.dataIndex === "number" && item.dataIndex >= 0
              ? occupancyRows[item.dataIndex]
              : occupancyRows.find((entry) => entry.occupancy_category === item?.name);
          if (!row) return "";
          const marker = typeof item?.marker === "string" ? item.marker : "";
          return [
            `<div style="font-weight:600;margin-bottom:4px;">${textValue(row.occupancy_category)}</div>`,
            `<div>${marker} Area Share: ${formatPercent(row.area_share_percent ?? row.share_percent)}</div>`,
            `<div>Buildings: ${formatCount(row.building_count)}</div>`,
            `<div>BruksArealTotalt: ${formatArea(row.total_bruksareal)}</div>`,
          ].join("");
        },
      },
      grid: { left: 40, right: 12, top: 26, bottom: 54 },
      xAxis: {
        type: "category" as const,
        data: categories,
        axisLabel: { interval: 0, rotate: 26 },
      },
      yAxis: {
        type: "value" as const,
        name: "Area Share (%)",
      },
      series: [
        {
          type: "bar" as const,
          data: values,
          itemStyle: { color: "#3a62e3", borderRadius: [6, 6, 0, 0] },
          barMaxWidth: 44,
        },
      ],
    };
  }, [occupancyRows]);

  const occupancyCountShareOption = useMemo(() => {
    const categories = occupancyRows.map((row) => textValue(row.occupancy_category));
    const values = occupancyRows.map((row) => asNumber(row.count_share_percent));
    return {
      tooltip: { trigger: "axis" as const, valueFormatter: (value: unknown) => formatPercent(value) },
      grid: { left: 40, right: 12, top: 20, bottom: 54 },
      xAxis: { type: "category" as const, data: categories, axisLabel: { interval: 0, rotate: 26 } },
      yAxis: { type: "value" as const, name: "Count Share (%)" },
      series: [{ type: "bar" as const, data: values, itemStyle: { color: "#5f78c3", borderRadius: [6, 6, 0, 0] } }],
    };
  }, [occupancyRows]);

  const exposureConcentrationOption = useMemo(() => {
    const rows = Array.isArray(exposure?.top_properties_by_area) ? exposure.top_properties_by_area.slice(0, 10) : [];
    const categories = rows.map((row) => `#${formatCount(row.rank)} ${textValue(row.address_label, "Unknown")}`);
    const areaValues = rows.map((row) => asNumber(row.total_bruksareal));
    const cumulativeShares: number[] = [];
    let runningShare = 0;
    rows.forEach((row) => {
      runningShare += asNumber(row.area_share_percent);
      cumulativeShares.push(Math.min(100, Number(runningShare.toFixed(2))));
    });

    return {
      tooltip: {
        trigger: "axis" as const,
        formatter: (raw: unknown) => {
          const params = Array.isArray(raw) ? raw : [raw];
          const first = params[0] as TooltipItem;
          const row = typeof first?.dataIndex === "number" ? rows[first.dataIndex] : undefined;
          if (!row) return "";
          return [
            `<div style="font-weight:600;margin-bottom:4px;">#${formatCount(row.rank)} ${textValue(row.address_label)}</div>`,
            `<div>Category: ${textValue(row.occupancy_category)}</div>`,
            `<div>Area: ${formatArea(row.total_bruksareal)}</div>`,
            `<div>Area Share: ${formatPercent(row.area_share_percent)}</div>`,
            `<div>Cumulative Share: ${formatPercent(cumulativeShares[first.dataIndex || 0])}</div>`,
          ].join("");
        },
      },
      legend: { data: ["Area", "Cumulative Share"], top: 0 },
      grid: { left: 44, right: 46, top: 34, bottom: 72 },
      xAxis: { type: "category" as const, data: categories, axisLabel: { interval: 0, rotate: 28 } },
      yAxis: [
        { type: "value" as const, name: "Area" },
        { type: "value" as const, name: "Cumulative (%)", min: 0, max: 100 },
      ],
      series: [
        { name: "Area", type: "bar" as const, data: areaValues, itemStyle: { color: "#2f80b9", borderRadius: [6, 6, 0, 0] }, barMaxWidth: 40 },
        { name: "Cumulative Share", type: "line" as const, yAxisIndex: 1, data: cumulativeShares, smooth: true, symbolSize: 7, lineStyle: { color: "#d27a2d", width: 2 } },
      ],
    };
  }, [exposure]);

  const ageBandOption = useMemo(() => {
    const categories = ageBands.map((row) => textValue(row.age_band));
    const areaShares = ageBands.map((row) => asNumber(row.area_share_percent));
    return {
      tooltip: { trigger: "axis" as const, valueFormatter: (value: unknown) => formatPercent(value) },
      grid: { left: 40, right: 12, top: 18, bottom: 32 },
      xAxis: { type: "category" as const, data: categories },
      yAxis: { type: "value" as const, name: "Area Share (%)" },
      series: [{ type: "bar" as const, data: areaShares, itemStyle: { color: "#4d8f7a", borderRadius: [6, 6, 0, 0] } }],
    };
  }, [ageBands]);

  const tekOption = useMemo(() => {
    const categories = tekDistribution.map((row) => textValue(row.tek_standard));
    const areaShares = tekDistribution.map((row) => asNumber(row.area_share_percent));
    return {
      tooltip: { trigger: "axis" as const, valueFormatter: (value: unknown) => formatPercent(value) },
      grid: { left: 40, right: 12, top: 18, bottom: 48 },
      xAxis: { type: "category" as const, data: categories, axisLabel: { interval: 0, rotate: 24 } },
      yAxis: { type: "value" as const, name: "Area Share (%)" },
      series: [{ type: "bar" as const, data: areaShares, itemStyle: { color: "#5a9f93", borderRadius: [6, 6, 0, 0] } }],
    };
  }, [tekDistribution]);

  const statusOption = useMemo(() => {
    const rows = statusDistribution.slice(0, 12);
    return {
      tooltip: { trigger: "axis" as const },
      grid: { left: 46, right: 12, top: 20, bottom: 64 },
      xAxis: { type: "category" as const, data: rows.map((row) => textValue(row.bygningsstatus)), axisLabel: { interval: 0, rotate: 28 } },
      yAxis: { type: "value" as const, name: "Buildings" },
      series: [{ type: "bar" as const, data: rows.map((row) => asNumber(row.property_count)), itemStyle: { color: "#3f6ba1", borderRadius: [6, 6, 0, 0] } }],
    };
  }, [statusDistribution]);

  const dataQualityOption = useMemo(() => {
    const labels = qualityFields.map((field) => textValue(field.label));
    const completeness = qualityFields.map((field) => asNumber(field.completeness_percent));
    return {
      tooltip: { trigger: "axis" as const, valueFormatter: (value: unknown) => formatPercent(value) },
      grid: { left: 46, right: 12, top: 16, bottom: 54 },
      xAxis: { type: "category" as const, data: labels, axisLabel: { interval: 0, rotate: 24 } },
      yAxis: { type: "value" as const, min: 0, max: 100, name: "Completeness (%)" },
      series: [{ type: "bar" as const, data: completeness, itemStyle: { color: "#2f946f", borderRadius: [6, 6, 0, 0] } }],
    };
  }, [qualityFields]);

  return (
    <main className="min-h-dvh px-4 py-4 sm:px-6 sm:py-6 lg:px-10">
      <div className="mx-auto w-full max-w-360">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Kommune Insights</h1>
            <p className="text-sm text-slate-600">{data?.kommune || kommune}</p>
          </div>
          <Button variant="outline" asChild className="rounded-xl">
            <Link href="/main">Back to Select Kommune</Link>
          </Button>
        </div>

        <div className="flex gap-6">
          <section className="min-w-0 flex-1 space-y-5">
            {isLoading ? <p className="text-sm text-slate-600">Loading kommune insights...</p> : null}
            {errorText ? <p className="text-sm text-red-700">{errorText}</p> : null}

            {!isLoading && !errorText ? (
              <>
                <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                  <Card className="rounded-2xl">
                    <CardContent>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Largest Occupancy</p>
                      <p className="mt-1 text-xl font-bold text-slate-900">{textValue(largestOccupancy?.occupancy_category)}</p>
                      <p className="mt-2 text-sm text-slate-700">Area: {formatArea(largestOccupancy?.total_bruksareal)}</p>
                      <p className="text-sm text-slate-700">Buildings: {formatCount(largestOccupancy?.building_count)}</p>
                    </CardContent>
                  </Card>
                  <Card className="rounded-2xl">
                    <CardContent>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Kommune Properties</p>
                      <p className="mt-1 text-xl font-bold text-slate-900">{formatCount(exposure?.selected_kommune_properties)}</p>
                      <p className="mt-2 text-sm text-slate-700">Share: {formatPercent(exposure?.selected_property_share_percent)}</p>
                    </CardContent>
                  </Card>
                  <Card className="rounded-2xl">
                    <CardContent>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Kommune Area</p>
                      <p className="mt-1 text-xl font-bold text-slate-900">{formatArea(exposure?.selected_kommune_bruksareal)}</p>
                      <p className="mt-2 text-sm text-slate-700">Share: {formatPercent(exposure?.selected_area_share_percent)}</p>
                    </CardContent>
                  </Card>
                  <Card className="rounded-2xl">
                    <CardContent>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Data Quality Score</p>
                      <p className="mt-1 text-xl font-bold text-slate-900">{formatPercent(underwriting?.data_quality?.score_percent)}</p>
                      <p className="mt-2 text-sm text-slate-700">Fields checked: {formatCount(qualityFields.length)}</p>
                    </CardContent>
                  </Card>
                </section>

                <Card className="rounded-2xl">
                  <CardContent>
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <h2 className="text-base font-semibold text-slate-900">Exposure Concentration</h2>
                      <div className="flex flex-wrap gap-2 text-xs">
                        <Badge variant="outline">Top 5: {formatPercent(exposure?.concentration?.top5_share_percent)}</Badge>
                        <Badge variant="outline">Top 10: {formatPercent(exposure?.concentration?.top10_share_percent)}</Badge>
                      </div>
                    </div>
                    <EChart option={exposureConcentrationOption} className="mt-3" height={340} />
                    <div className="mt-3 overflow-hidden rounded-xl border border-slate-200">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Top Area Rank</TableHead>
                            <TableHead>Kommune</TableHead>
                            <TableHead>Address</TableHead>
                            <TableHead>Category</TableHead>
                            <TableHead className="text-right">Area</TableHead>
                            <TableHead className="text-right">Kommune Area Share</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {(exposure?.top_properties_by_area || []).map((row) => (
                            <TableRow key={`${row.rank}-${row.address_label}-${row.kommune}`}>
                              <TableCell>{formatCount(row.rank)}</TableCell>
                              <TableCell>{textValue(row.kommune)}</TableCell>
                              <TableCell>{textValue(row.address_label)}</TableCell>
                              <TableCell>{textValue(row.occupancy_category)}</TableCell>
                              <TableCell className="text-right">{formatArea(row.total_bruksareal)}</TableCell>
                              <TableCell className="text-right">{formatPercent(row.area_share_percent)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </CardContent>
                </Card>

                <Card className="rounded-2xl">
                  <CardContent>
                    <h2 className="text-base font-semibold text-slate-900">Occupancy Risk Mix</h2>
                    <div className="mt-3 grid gap-4 xl:grid-cols-2">
                      <EChart option={occupancyAreaShareOption} height={340} />
                      <EChart option={occupancyCountShareOption} height={340} />
                    </div>
                    <div className="mt-3 grid gap-4 lg:grid-cols-2">
                      <div className="overflow-hidden rounded-xl border border-slate-200">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Top by Area</TableHead>
                              <TableHead className="text-right">Area Share</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {occupancyTopByArea.slice(0, 5).map((row) => (
                              <TableRow key={`area-${row.occupancy_category}`}>
                                <TableCell>{textValue(row.occupancy_category)}</TableCell>
                                <TableCell className="text-right">
                                  {formatPercent(row.area_share_percent ?? row.share_percent)}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                      <div className="overflow-hidden rounded-xl border border-slate-200">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Top by Count</TableHead>
                              <TableHead className="text-right">Buildings</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {occupancyTopByCount.slice(0, 5).map((row) => (
                              <TableRow key={`count-${row.occupancy_category}`}>
                                <TableCell>{textValue(row.occupancy_category)}</TableCell>
                                <TableCell className="text-right">{formatCount(row.building_count)}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="rounded-2xl">
                  <CardContent>
                    <h2 className="text-base font-semibold text-slate-900">Age / Standard Proxy</h2>
                    <div className="mt-3 grid gap-4 xl:grid-cols-2">
                      <EChart option={ageBandOption} height={280} />
                      <EChart option={tekOption} height={280} />
                    </div>
                  </CardContent>
                </Card>

                <Card className="rounded-2xl">
                  <CardContent>
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <h2 className="text-base font-semibold text-slate-900">Status-Based Underwriting Filters</h2>
                      <div className="flex flex-wrap gap-2">
                        {problematicStatuses.length ? (
                          problematicStatuses.map((status) => (
                            <Badge key={status} variant="outline">
                              {status}
                            </Badge>
                          ))
                        ) : (
                          <Badge variant="outline">No flagged statuses</Badge>
                        )}
                      </div>
                    </div>
                    <EChart option={statusOption} className="mt-3" height={300} />
                    {problematicProperties.length ? (
                      <div className="mt-3 overflow-hidden rounded-xl border border-slate-200">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Kommune</TableHead>
                              <TableHead>Address</TableHead>
                              <TableHead>Status</TableHead>
                              <TableHead>Category</TableHead>
                              <TableHead className="text-right">Area</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {problematicProperties.map((row) => (
                              <TableRow key={`${row.kommune}-${row.address_label}-${row.bygningsstatus}`}>
                                <TableCell>{textValue(row.kommune)}</TableCell>
                                <TableCell>{textValue(row.address_label)}</TableCell>
                                <TableCell>{textValue(row.bygningsstatus)}</TableCell>
                                <TableCell>{textValue(row.occupancy_category)}</TableCell>
                                <TableCell className="text-right">{formatArea(row.total_bruksareal)}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    ) : null}
                  </CardContent>
                </Card>

                <Card className="rounded-2xl">
                  <CardContent>
                    <h2 className="text-base font-semibold text-slate-900">Large-Risk Schedule</h2>
                    <div className="mt-3 overflow-hidden rounded-xl border border-slate-200">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Rank</TableHead>
                            <TableHead>Address</TableHead>
                            <TableHead>Category</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>TEK</TableHead>
                            <TableHead className="text-right">Area</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {largeRiskRows.map((row) => (
                            <TableRow key={`${row.rank}-${row.address_label}`}>
                              <TableCell>{formatCount(row.rank)}</TableCell>
                              <TableCell>{textValue(row.address_label)}</TableCell>
                              <TableCell>{textValue(row.occupancy_category)}</TableCell>
                              <TableCell>{textValue(row.bygningsstatus)}</TableCell>
                              <TableCell>{textValue(row.tek_standard)}</TableCell>
                              <TableCell className="text-right">{formatArea(row.total_bruksareal)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </CardContent>
                </Card>

                <Card className="rounded-2xl">
                  <CardContent>
                    <h2 className="text-base font-semibold text-slate-900">Heritage / Special-Handling Flags</h2>
                    <div className="mt-3 grid gap-3 sm:grid-cols-4">
                      <Badge variant="outline" className="justify-center py-1">SEFRAK: {formatCount(underwriting?.heritage_flags?.summary?.sefrak_count)}</Badge>
                      <Badge variant="outline" className="justify-center py-1">Kulturminne: {formatCount(underwriting?.heritage_flags?.summary?.kulturminne_count)}</Badge>
                      <Badge variant="outline" className="justify-center py-1">Skjermingsverdig: {formatCount(underwriting?.heritage_flags?.summary?.skjermingsverdig_count)}</Badge>
                      <Badge variant="outline" className="justify-center py-1">Any Flag: {formatCount(underwriting?.heritage_flags?.summary?.any_flag_count)}</Badge>
                    </div>
                    {heritageRows.length ? (
                      <div className="mt-3 overflow-hidden rounded-xl border border-slate-200">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Address</TableHead>
                              <TableHead>Category</TableHead>
                              <TableHead className="text-right">Area</TableHead>
                              <TableHead className="text-right">SEFRAK</TableHead>
                              <TableHead className="text-right">Kulturminne</TableHead>
                              <TableHead className="text-right">Skjermingsverdig</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {heritageRows.map((row) => (
                              <TableRow key={`${row.kommune}-${row.address_label}`}>
                                <TableCell>{textValue(row.address_label)}</TableCell>
                                <TableCell>{textValue(row.occupancy_category)}</TableCell>
                                <TableCell className="text-right">{formatArea(row.total_bruksareal)}</TableCell>
                                <TableCell className="text-right">{formatCount(row.har_sefrakminne)}</TableCell>
                                <TableCell className="text-right">{formatCount(row.har_kulturminne)}</TableCell>
                                <TableCell className="text-right">{formatCount(row.skjermingsverdig)}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    ) : (
                      <p className="mt-3 text-sm text-slate-600">No flagged properties found in this kommune.</p>
                    )}
                  </CardContent>
                </Card>

                <Card className="rounded-2xl">
                  <CardContent>
                    <h2 className="text-base font-semibold text-slate-900">Tenant / Business Activity Proxy</h2>
                    <div className="mt-3 grid gap-3 md:grid-cols-3">
                      <Badge variant="outline" className="justify-center py-1">With tenants: {formatCount(tenantSummary?.with_tenants_count)}</Badge>
                      <Badge variant="outline" className="justify-center py-1">Tenant share: {formatPercent(withTenantsSharePercent)}</Badge>
                      <Badge variant="outline" className="justify-center py-1">Max underenheter: {formatCount(tenantSummary?.max_underenheter)}</Badge>
                    </div>
                    {tenantTopRows.length ? (
                      <div className="mt-3 overflow-hidden rounded-xl border border-slate-200">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Address</TableHead>
                              <TableHead>Category</TableHead>
                              <TableHead className="text-right">Underenheter</TableHead>
                              <TableHead className="text-right">Owners</TableHead>
                              <TableHead className="text-right">Area</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {tenantTopRows.map((row) => (
                              <TableRow key={`${row.kommune}-${row.address_label}-${row.antall_underenheter}`}>
                                <TableCell>{textValue(row.address_label)}</TableCell>
                                <TableCell>{textValue(row.occupancy_category)}</TableCell>
                                <TableCell className="text-right">{formatCount(row.antall_underenheter)}</TableCell>
                                <TableCell className="text-right">{formatCount(row.antall_eiere)}</TableCell>
                                <TableCell className="text-right">{formatArea(row.total_bruksareal)}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    ) : (
                      <p className="mt-3 text-sm text-slate-600">No tenant-linked rows found for this kommune.</p>
                    )}
                  </CardContent>
                </Card>

                <Card className="rounded-2xl">
                  <CardContent>
                    <h2 className="text-base font-semibold text-slate-900">Data Quality Scoring</h2>
                    <EChart option={dataQualityOption} className="mt-3" height={300} />
                    <div className="mt-3 overflow-hidden rounded-xl border border-slate-200">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Field</TableHead>
                            <TableHead className="text-right">Present</TableHead>
                            <TableHead className="text-right">Missing</TableHead>
                            <TableHead className="text-right">Completeness</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {qualityFields.map((field) => (
                            <TableRow key={textValue(field.field, "field")}>
                              <TableCell>{textValue(field.label)}</TableCell>
                              <TableCell className="text-right">{formatCount(field.present_count)}</TableCell>
                              <TableCell className="text-right">{formatCount(field.missing_count)}</TableCell>
                              <TableCell className="text-right">{formatPercent(field.completeness_percent)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : null}
          </section>

          <aside className="hidden w-95 shrink-0 lg:block">
            <div className="sticky top-6">
              <InsightsChatPanel kommune={kommune} />
            </div>
          </aside>
        </div>
      </div>
    </main>
  );
}
