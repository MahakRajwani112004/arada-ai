"use client";

import { useState } from "react";
import { Sparkles, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";

interface AIPromptInputProps {
  onSubmit: (prompt: string) => void;
  isLoading?: boolean;
}

const examplePrompts = [
  {
    icon: "📧",
    title: "Process support tickets automatically",
    prompt:
      "When a support ticket comes in, classify it by priority, route to the right team, and send an acknowledgment email.",
  },
  {
    icon: "📊",
    title: "Generate daily sales reports",
    prompt:
      "Every morning, collect sales data from the CRM, analyze trends, and send a summary report to the sales team.",
  },
  {
    icon: "🔔",
    title: "Alert on unusual patterns",
    prompt:
      "Monitor system metrics and send alerts when anomalies are detected, including suggested remediation steps.",
  },
];

export function AIPromptInput({ onSubmit, isLoading }: AIPromptInputProps) {
  const [prompt, setPrompt] = useState("");

  const handleSubmit = () => {
    if (prompt.trim()) {
      onSubmit(prompt.trim());
    }
  };

  const handleExampleClick = (examplePrompt: string) => {
    setPrompt(examplePrompt);
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h2 className="text-xl font-semibold">What should this workflow do?</h2>
        <p className="text-muted-foreground">
          Describe your workflow in plain English. We&apos;ll figure out the rest.
        </p>
      </div>

      <div className="space-y-4">
        <Textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="When a new customer signs up, verify their email, enrich their profile with company data, and send a personalized welcome email based on company size..."
          className="min-h-[120px] resize-none"
          disabled={isLoading}
        />

        <Button
          onClick={handleSubmit}
          disabled={!prompt.trim() || isLoading}
          className="gap-2"
        >
          <Sparkles className="h-4 w-4" />
          Generate Workflow
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>

      <div className="space-y-3">
        <p className="text-sm text-muted-foreground">Try these examples:</p>
        <div className="grid gap-2">
          {examplePrompts.map((example, index) => (
            <Card
              key={index}
              className="cursor-pointer transition-all hover:border-primary/50 hover:bg-secondary/50"
              onClick={() => handleExampleClick(example.prompt)}
            >
              <CardContent className="flex items-center gap-3 p-3">
                <span className="text-xl">{example.icon}</span>
                <span className="text-sm">{example.title}</span>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
