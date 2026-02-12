"use client";

import type { ReactNode } from "react";

import { Card, CardContent } from "@/components/ui/card";
import type { ColorTheme } from "@/components/shared/themes";
import { summaryBannerStyles } from "@/components/shared/themes";
import { cn } from "@/lib/utils";

interface SummaryBannerProps {
  title: string;
  description?: string;
  meta?: string;
  actions?: ReactNode;
  colorTheme?: ColorTheme;
  className?: string;
}

export function SummaryBanner({
  title,
  description,
  meta,
  actions,
  colorTheme = "primary",
  className,
}: SummaryBannerProps) {
  const styles = summaryBannerStyles[colorTheme];

  return (
    <Card className={cn(styles.container, className)}>
      <CardContent className="flex flex-wrap items-center justify-between gap-4">
        <div className="min-w-0 flex-1">
          <h3 className={cn("text-lg font-bold", styles.title)}>{title}</h3>
          {description && <p className={cn("mt-1 text-sm", styles.subtitle)}>{description}</p>}
          {meta && <p className={cn("mt-1 text-xs font-medium", styles.meta)}>{meta}</p>}
        </div>
        {actions && <div className="shrink-0">{actions}</div>}
      </CardContent>
    </Card>
  );
}
