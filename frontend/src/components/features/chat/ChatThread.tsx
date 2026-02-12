"use client";

import type { ChatMessage } from "@/components/features/chat/contracts";

interface ChatThreadProps {
  messages: ChatMessage[];
}

export function ChatThread({ messages }: ChatThreadProps) {
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-auto px-1 pb-2" aria-live="polite">
      {messages.map((message) => (
        <article
          key={message.id}
          className={`max-w-[82%] rounded-2xl border p-3 leading-relaxed shadow-sm ${
            message.role === "user"
              ? "ml-auto border-[rgba(67,92,133,0.28)] bg-[linear-gradient(160deg,rgba(226,236,255,0.88),rgba(214,230,247,0.88))]"
              : "mr-auto border-[rgba(80,98,124,0.24)] bg-[rgba(255,255,255,0.86)]"
          }`}
        >
          <p>{message.text}</p>
        </article>
      ))}
    </div>
  );
}
