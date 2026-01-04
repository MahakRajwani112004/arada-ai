"use client";

import { Bot } from "lucide-react";

interface StreamingMessageProps {
  content: string;
}

export function StreamingMessage({ content }: StreamingMessageProps) {
  if (!content) return null;

  return (
    <div className="flex gap-3">
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
        <Bot className="h-4 w-4 text-muted-foreground" />
      </div>

      {/* Message */}
      <div className="flex-1 max-w-[80%] rounded-lg bg-secondary p-3">
        <div className="prose prose-sm dark:prose-invert max-w-none">
          {content.split("\n").map((line, i) => (
            <p key={i} className="m-0 mt-0 first:mt-0">
              {line || "\u00A0"}
            </p>
          ))}
          {/* Cursor */}
          <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-0.5 align-middle" />
        </div>
      </div>
    </div>
  );
}
