"use client";

import { AlertCircle, AlertTriangle, CheckCircle2, Info } from "lucide-react";

import {
  Alert as ShadcnAlert,
  AlertTitle,
  AlertDescription,
} from "@/components/ui/alert";
import { cn } from "@/lib/utils";

type AlertType = "error" | "warning" | "success" | "info";

interface AlertProps {
  type: AlertType;
  title: string;
  message: string;
  details?: string;
  className?: string;
}

const alertTypeConfig: Record<
  AlertType,
  {
    icon: typeof AlertCircle;
    variant: "default" | "destructive";
    containerClass: string;
    iconClass: string;
  }
> = {
  error: {
    icon: AlertCircle,
    variant: "destructive",
    containerClass: "border-red-300 bg-red-50 text-red-900",
    iconClass: "text-red-500",
  },
  warning: {
    icon: AlertTriangle,
    variant: "default",
    containerClass: "border-amber-300 bg-amber-50 text-amber-900",
    iconClass: "text-amber-500",
  },
  success: {
    icon: CheckCircle2,
    variant: "default",
    containerClass: "border-primary-300 bg-primary-50 text-primary-900",
    iconClass: "text-primary-500",
  },
  info: {
    icon: Info,
    variant: "default",
    containerClass: "border-primary-300 bg-primary-50 text-primary-900",
    iconClass: "text-primary-500",
  },
};

export function Alert({ type, title, message, details, className }: AlertProps) {
  const config = alertTypeConfig[type];
  const Icon = config.icon;

  return (
    <ShadcnAlert
      variant={config.variant}
      className={cn("rounded-xl", config.containerClass, className)}
    >
      <Icon className={cn("h-5 w-5", config.iconClass)} />
      <AlertTitle className="text-sm font-semibold">{title}</AlertTitle>
      <AlertDescription className="text-sm">
        {message}
        {details && <p className="mt-2 text-xs opacity-80">{details}</p>}
      </AlertDescription>
    </ShadcnAlert>
  );
}
