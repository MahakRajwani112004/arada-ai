"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Sparkles, Bot, Workflow, Zap } from "lucide-react";

const loadingMessages = [
  { text: "Analyzing your requirements...", icon: Sparkles },
  { text: "Checking your existing agents...", icon: Bot },
  { text: "Finding the best matches...", icon: Workflow },
  { text: "Designing the workflow...", icon: Zap },
  { text: "Almost there, finalizing the plan...", icon: Sparkles },
];

export function AIGenerationLoader() {
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % loadingMessages.length);
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const currentMessage = loadingMessages[messageIndex];
  const Icon = currentMessage.icon;

  return (
    <div className="flex flex-col items-center justify-center py-16">
      <motion.div
        animate={{
          scale: [1, 1.1, 1],
          rotate: [0, 5, -5, 0],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-purple-500/20 to-blue-500/20"
      >
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-purple-500/30 to-blue-500/30">
          <Icon className="h-7 w-7 text-primary" />
        </div>
      </motion.div>

      <motion.p
        key={messageIndex}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className="mt-6 text-lg font-medium"
      >
        {currentMessage.text}
      </motion.p>

      <div className="mt-4 flex gap-2">
        {loadingMessages.map((_, index) => (
          <div
            key={index}
            className={`h-1.5 w-1.5 rounded-full transition-colors ${
              index === messageIndex ? "bg-primary" : "bg-muted"
            }`}
          />
        ))}
      </div>

      <p className="mt-8 max-w-sm text-center text-sm text-muted-foreground">
        We&apos;re analyzing your request and checking which existing agents and tools
        can be reused to build your workflow.
      </p>
    </div>
  );
}
