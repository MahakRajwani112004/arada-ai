"use client";

import { useState, useRef } from "react";
import { Info, Plus } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import type { SkillPrompts, SkillParameter, Terminology } from "@/types/skill";

interface PromptEditorProps {
  prompts: SkillPrompts;
  parameters: SkillParameter[];
  terminology: Terminology[];
  onChange: (prompts: SkillPrompts) => void;
}

const BUILT_IN_VARIABLES = [
  { name: "user_input", description: "The user's current message" },
  { name: "conversation_history", description: "Recent conversation context" },
  { name: "current_date", description: "Today's date" },
  { name: "agent_name", description: "The agent's configured name" },
];

export function PromptEditor({
  prompts,
  parameters,
  terminology,
  onChange,
}: PromptEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [isPopoverOpen, setIsPopoverOpen] = useState(false);

  const extractVariables = (text: string): string[] => {
    const matches = text.match(/\{\{(\w+)\}\}/g) || [];
    return Array.from(new Set(matches.map((m) => m.replace(/\{\{|\}\}/g, ""))));
  };

  const handleTextChange = (value: string) => {
    const variables = extractVariables(value);
    onChange({ system_enhancement: value, variables });
  };

  const insertVariable = (variableName: string) => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = prompts.system_enhancement;
    const insertion = `{{${variableName}}}`;
    const newText = text.substring(0, start) + insertion + text.substring(end);

    handleTextChange(newText);
    setIsPopoverOpen(false);

    // Restore focus and cursor position after state update
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(
        start + insertion.length,
        start + insertion.length
      );
    }, 0);
  };

  // Build available variables list
  const availableVariables = [
    ...BUILT_IN_VARIABLES,
    ...parameters.map((p) => ({
      name: `param_${p.name}`,
      description: p.description || `Parameter: ${p.name}`,
    })),
    ...terminology.slice(0, 5).map((t) => ({
      name: `term_${t.term.toLowerCase().replace(/\s+/g, "_")}`,
      description: `Definition of "${t.term}"`,
    })),
  ];

  return (
    <div className="space-y-4">
      <div>
        <div className="mb-2 flex items-center justify-between">
          <label className="text-sm font-medium">
            System Enhancement Template
          </label>
          <Popover open={isPopoverOpen} onOpenChange={setIsPopoverOpen}>
            <PopoverTrigger asChild>
              <Button type="button" variant="outline" size="sm" className="gap-1">
                <Plus className="h-4 w-4" />
                Insert Variable
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80" align="end">
              <div className="space-y-2">
                <h4 className="font-medium">Available Variables</h4>
                <p className="text-xs text-muted-foreground">
                  Click to insert at cursor position
                </p>
                <div className="max-h-60 space-y-1 overflow-y-auto">
                  {availableVariables.map((v) => (
                    <button
                      key={v.name}
                      type="button"
                      onClick={() => insertVariable(v.name)}
                      className="flex w-full items-start gap-2 rounded-md p-2 text-left hover:bg-muted"
                    >
                      <Badge variant="secondary" className="shrink-0 font-mono text-xs">
                        {`{{${v.name}}}`}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {v.description}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </PopoverContent>
          </Popover>
        </div>
        <Textarea
          ref={textareaRef}
          placeholder={`You are augmented with expertise in [domain].

When analyzing {{user_input}}, consider:
- Key terminology and concepts
- Domain-specific reasoning patterns
- Best practices and guidelines

Apply the following knowledge:
{{term_example}}

Use parameter: {{param_jurisdiction}}`}
          value={prompts.system_enhancement}
          onChange={(e) => handleTextChange(e.target.value)}
          rows={12}
          className="font-mono text-sm"
        />
        <p className="mt-1 text-xs text-muted-foreground">
          This template is injected into the agent&apos;s system prompt. Use{" "}
          <code className="rounded bg-muted px-1">{"{{variable}}"}</code> syntax
          for dynamic content.
        </p>
      </div>

      {prompts.variables.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-medium">Detected Variables</h4>
          <div className="flex flex-wrap gap-2">
            {prompts.variables.map((v) => (
              <Badge key={v} variant="outline" className="font-mono">
                {`{{${v}}}`}
              </Badge>
            ))}
          </div>
        </div>
      )}

      <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-3">
        <div className="flex gap-2">
          <Info className="h-4 w-4 shrink-0 text-blue-400" />
          <div className="text-sm text-muted-foreground">
            <p className="font-medium text-foreground">How it works</p>
            <p className="mt-1">
              When this skill is selected at runtime, the template above gets
              merged into the agent&apos;s system prompt. The terminology, reasoning
              patterns, and examples you defined are automatically formatted and
              included.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
