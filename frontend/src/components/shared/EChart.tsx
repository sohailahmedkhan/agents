"use client";

import dynamic from "next/dynamic";
import type { EChartsOption } from "echarts";

const ReactECharts = dynamic(() => import("echarts-for-react"), {
  ssr: false,
});

interface EChartProps {
  option: EChartsOption;
  className?: string;
  height?: number | string;
}

export function EChart({ option, className = "", height = 320 }: EChartProps) {
  return (
    <div className={className}>
      <ReactECharts option={option} style={{ width: "100%", height }} opts={{ renderer: "canvas" }} />
    </div>
  );
}
