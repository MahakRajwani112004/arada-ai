"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { Send, Square, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (content: string) => void;
  onCancel?: () => void;
  isLoading?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  onCancel,
  isLoading,
  disabled,
  placeholder = "Type a message...",
}: ChatInputProps) {
  const [content, setContent] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [content]);

  const handleSend = () => {
    const trimmed = content.trim();
    if (trimmed && !disabled) {
      onSend(trimmed);
      setContent("");
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter (without Shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const canSend = content.trim().length > 0 && !disabled;

  return (
    <div className="relative">
      <Textarea
        ref={textareaRef}
        value={content}
        onChange={(e) => setContent(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className={cn(
          "min-h-[48px] max-h-[200px] resize-none pr-24",
          "focus-visible:ring-1 focus-visible:ring-ring"
        )}
        rows={1}
      />

      <div className="absolute right-2 bottom-2 flex items-center gap-1">
        {isLoading ? (
          <>
            <Button
              size="sm"
              variant="ghost"
              onClick={onCancel}
              className="h-8 px-2"
            >
              <Square className="h-4 w-4" />
              <span className="sr-only">Stop</span>
            </Button>
            <Button size="sm" disabled className="h-8 px-3">
              <Loader2 className="h-4 w-4 animate-spin" />
            </Button>
          </>
        ) : (
          <Button
            size="sm"
            onClick={handleSend}
            disabled={!canSend}
            className="h-8 px-3"
          >
            <Send className="h-4 w-4" />
            <span className="sr-only">Send</span>
          </Button>
        )}
      </div>

      {/* Character hint */}
      <div className="absolute right-2 -bottom-5 text-xs text-muted-foreground">
        <kbd className="px-1 py-0.5 rounded bg-muted text-[10px]">Enter</kbd>
        <span className="ml-1">to send</span>
        <span className="mx-1">&bull;</span>
        <kbd className="px-1 py-0.5 rounded bg-muted text-[10px]">Shift+Enter</kbd>
        <span className="ml-1">new line</span>
      </div>
    </div>
  );
}
