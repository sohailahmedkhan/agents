"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";
import { ArrowUp, Loader2 } from "lucide-react";

import { Button as ShadcnButton } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary" | "danger" | "ghost" | "outline" | "icon" | "accent" | "chat-send";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: ReactNode;
}

const variantMap = {
  primary: "default",
  secondary: "secondary",
  danger: "destructive",
  ghost: "ghost",
  outline: "outline",
  icon: "ghost",
} as const;

const sizeMap = {
  sm: "sm",
  md: "default",
  lg: "lg",
} as const;

export function Button({
  children,
  className,
  type = "button",
  variant = "primary",
  size = "md",
  loading = false,
  leftIcon,
  disabled,
  ...props
}: ButtonProps) {
  if (variant === "chat-send") {
    return (
      <button
        type={type}
        className={cn(
          "inline-flex items-center justify-center font-semibold transition disabled:cursor-not-allowed disabled:opacity-60",
          "h-14 w-14 min-w-14 rounded-full border border-(--chat-btn-border) bg-(--chat-btn-bg) text-(--chat-send-icon) shadow-lg hover:brightness-110 active:translate-y-px disabled:hover:brightness-100",
          className,
        )}
        disabled={disabled || loading}
        {...props}
      >
        {children}
      </button>
    );
  }

  if (variant === "accent") {
    return (
      <ShadcnButton
        type={type}
        variant="default"
        className={cn(
          "h-11 min-w-21 rounded-2xl border border-slate-300 bg-slate-700 px-4 text-sm tracking-[0.01em] text-slate-50 shadow-md hover:bg-slate-800 active:translate-y-px disabled:hover:bg-slate-700",
          className,
        )}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {!loading && leftIcon}
        {children}
      </ShadcnButton>
    );
  }

  const shadcnVariant = variantMap[variant as keyof typeof variantMap] || "default";
  const shadcnSize = sizeMap[size];

  return (
    <ShadcnButton
      type={type}
      variant={shadcnVariant}
      size={shadcnSize}
      className={className}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" />}
      {!loading && leftIcon}
      {children}
    </ShadcnButton>
  );
}

type ChatSendButtonProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children">;

export function ChatSendButton({ className, type = "button", ...props }: ChatSendButtonProps) {
  return (
    <Button type={type} variant="chat-send" className={className} {...props}>
      <ArrowUp className="h-6 w-6" strokeWidth={2.8} aria-hidden="true" />
    </Button>
  );
}
