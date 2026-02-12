"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

import { Send } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import type { ChatMessage } from "@/components/features/chat/contracts";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8101";

interface InsightsChatPanelProps {
  kommune: string;
}

export function InsightsChatPanel({ kommune }: InsightsChatPanelProps) {
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [errorText, setErrorText] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || isLoading) return;

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
          kommune_name: kommune,
        }),
      });

      const payload = (await response.json()) as { summary?: string; detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail || "Failed to get response from backend.");
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
          text: "I could not complete that request. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void sendMessage();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void sendMessage();
    }
  };

  const canSubmit = input.trim().length > 0 && !isLoading;

  return (
    <Card className="flex flex-col rounded-2xl">
      <CardHeader className="pb-0">
        <CardTitle className="text-base text-slate-800">Ask about {kommune}</CardTitle>
      </CardHeader>
      <Separator className="mx-6 mt-3 w-auto" />
      <CardContent className="flex flex-col gap-3 pt-3">
        {/* Messages */}
        <div
          ref={scrollRef}
          className="flex max-h-80 flex-col gap-2.5 overflow-y-auto pr-1"
          aria-live="polite"
        >
          {messages.length === 0 ? (
            <p className="py-8 text-center text-sm text-slate-400">
              Ask a question about this municipality&apos;s data.
            </p>
          ) : null}
          {messages.map((msg) => (
            <article
              key={msg.id}
              className={`max-w-[90%] rounded-2xl border p-3 text-sm leading-relaxed shadow-sm ${
                msg.role === "user"
                  ? "ml-auto border-[rgba(67,92,133,0.28)] bg-[linear-gradient(160deg,rgba(226,236,255,0.88),rgba(214,230,247,0.88))]"
                  : "mr-auto border-[rgba(80,98,124,0.24)] bg-[rgba(255,255,255,0.86)]"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.text}</p>
            </article>
          ))}
          {isLoading ? (
            <div className="mr-auto flex items-center gap-1.5 rounded-2xl border border-[rgba(80,98,124,0.24)] bg-[rgba(255,255,255,0.86)] px-4 py-3 text-sm text-slate-500 shadow-sm">
              <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-slate-400" />
              <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-slate-400 [animation-delay:150ms]" />
              <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-slate-400 [animation-delay:300ms]" />
            </div>
          ) : null}
        </div>

        {/* Error */}
        {errorText ? (
          <p className="text-xs text-red-600" role="alert">
            {errorText}
          </p>
        ) : null}

        {/* Input */}
        <form className="flex items-end gap-2" onSubmit={handleSubmit}>
          <textarea
            className="min-h-10 max-h-32 flex-1 resize-none rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm leading-relaxed text-slate-800 placeholder:text-slate-400 focus:border-primary-400 focus:outline-none"
            placeholder="Ask a question..."
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            rows={1}
          />
          <Button
            type="submit"
            size="icon"
            variant="default"
            className="h-10 w-10 shrink-0 rounded-xl"
            disabled={!canSubmit}
            aria-label={isLoading ? "Thinking" : "Send message"}
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
