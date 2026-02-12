"use client";

import { useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";

import { ChatBar } from "@/components/shared";
import { chatWorkspaceThemes, getChatWorkspaceCssVars } from "@/components/shared/themes";
import { ChatThread } from "@/components/features/chat/ChatThread";
import { KommuneSelector } from "@/components/features/chat/KommuneSelector";
import type { ChatMessage, KommuneOption } from "@/components/features/chat/contracts";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8101";

interface KommuneListResponse {
  kommuner?: KommuneOption[];
  detail?: string;
}

interface ChatResponse {
  summary?: string;
  detail?: string;
}

export function ChatWorkspace() {
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [errorText, setErrorText] = useState("");
  const [kommuner, setKommuner] = useState<KommuneOption[]>([]);
  const [selectedKommuneKey, setSelectedKommuneKey] = useState("");
  const [isLoadingKommuner, setIsLoadingKommuner] = useState(true);

  const themeVars = getChatWorkspaceCssVars(chatWorkspaceThemes.default) as CSSProperties;

  const selectedKommuneLabel = useMemo(
    () => kommuner.find((item) => item.key === selectedKommuneKey)?.label || "",
    [kommuner, selectedKommuneKey]
  );

  useEffect(() => {
    const controller = new AbortController();

    const loadKommuner = async () => {
      setIsLoadingKommuner(true);

      try {
        const response = await fetch(`${API_URL}/agents/kommuner`, { signal: controller.signal });
        const payload = (await response.json()) as KommuneListResponse;

        if (!response.ok) {
          throw new Error(payload.detail || "Failed to load kommune options.");
        }

        const options = Array.isArray(payload.kommuner) ? payload.kommuner : [];
        setKommuner(options);
        setSelectedKommuneKey((current) => {
          if (current && options.some((option) => option.key === current)) {
            return current;
          }
          return options[0]?.key || "";
        });
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

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    if (!selectedKommuneLabel) {
      setErrorText("Select a kommune before sending a message.");
      return;
    }

    setErrorText("");
    setIsLoading(true);
    setInput("");
    setMessages((prev) => [...prev, { id: `u-${Date.now()}`, role: "user", text }]);

    try {
      const response = await fetch(`${API_URL}/agents/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          use_llm: true,
          workflow: "kommune_match_overview",
          kommune_name: selectedKommuneLabel,
        }),
      });

      const payload = (await response.json()) as ChatResponse;
      if (!response.ok) {
        const detail = payload.detail || "Failed to get response from backend.";
        throw new Error(detail);
      }

      const summary = (payload.summary || "").trim() || "No response generated.";
      setMessages((prev) => [...prev, { id: `a-${Date.now()}`, role: "assistant", text: summary }]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unexpected chat error.";
      setErrorText(message);
      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          text: "I could not complete that request. Please verify backend dependencies and Vertex credentials.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section
      className="flex h-full w-full max-w-[920px] flex-col gap-3"
      style={themeVars}
      aria-label="Municipality chat workspace"
    >
      <KommuneSelector
        options={kommuner}
        selectedKey={selectedKommuneKey}
        onChange={setSelectedKommuneKey}
        disabled={isLoading}
        isLoading={isLoadingKommuner}
      />
      <ChatThread messages={messages} />
      {errorText ? (
        <p className="px-1 text-sm text-red-700" role="alert">
          {errorText}
        </p>
      ) : null}
      <ChatBar
        value={input}
        onChange={setInput}
        onSubmit={sendMessage}
        disabled={isLoading || isLoadingKommuner || !selectedKommuneLabel}
      />
    </section>
  );
}
