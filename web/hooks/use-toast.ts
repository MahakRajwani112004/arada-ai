"use client";

import { toast as sonnerToast } from "sonner";

interface ToastOptions {
  title?: string;
  description?: string;
  variant?: "default" | "destructive";
  duration?: number;
}

function toast({ title, description, variant, duration }: ToastOptions) {
  const message = title || description || "";
  const options = {
    description: title ? description : undefined,
    duration: duration ?? 4000,
  };

  if (variant === "destructive") {
    sonnerToast.error(message, options);
  } else {
    sonnerToast(message, options);
  }
}

export function useToast() {
  return {
    toast,
  };
}

export { toast };
