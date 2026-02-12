/* eslint-disable jsx-a11y/no-autofocus */
"use client";

import { FormEvent, KeyboardEvent } from "react";
import type { CSSProperties } from "react";

import { ChatSendButton } from "@/components/shared/Button";
import { chatBarThemes, getChatBarCssVars } from "@/components/shared/themes";

interface ChatBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  placeholder?: string;
  buttonLabel?: string;
  disabled?: boolean;
}

export function ChatBar({
  value,
  onChange,
  onSubmit,
  placeholder = "Message Kommune Assistant...",
  buttonLabel = "Send message",
  disabled = false,
}: ChatBarProps) {
  const themeVars = getChatBarCssVars(chatBarThemes.default) as CSSProperties;
  const canSubmit = value.trim().length > 0 && !disabled;

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (canSubmit) {
      onSubmit();
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (canSubmit) {
        onSubmit();
      }
    }
  };

  return (
    <section className="w-full" aria-label="Chat composer" style={themeVars}>
      <form
        className="flex w-full items-end gap-3 rounded-3xl border border-[color:var(--chat-panel-border)] bg-[var(--chat-panel-bg)] p-3 shadow-[0_10px_30px_rgba(17,49,76,0.14)] backdrop-blur-sm md:gap-3"
        onSubmit={handleSubmit}
      >
        <label className="sr-only" htmlFor="chat-input">
          Message
        </label>
        <textarea
          id="chat-input"
          className="min-h-11 max-h-56 w-full resize-none border-0 bg-transparent px-3 py-2 text-base leading-relaxed text-[var(--text)] placeholder:text-[var(--chat-placeholder)] focus:outline-none"
          placeholder={placeholder}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
          autoFocus
        />
        <ChatSendButton type="submit" aria-label={disabled ? "Thinking" : buttonLabel} disabled={!canSubmit} />
      </form>
    </section>
  );
}
