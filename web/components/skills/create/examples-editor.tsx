"use client";

import { useState } from "react";
import { Plus, Trash2, Edit2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { SkillExample } from "@/types/skill";
import { nanoid } from "nanoid";

interface ExamplesEditorProps {
  examples: SkillExample[];
  onChange: (examples: SkillExample[]) => void;
}

export function ExamplesEditor({ examples, onChange }: ExamplesEditorProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<Partial<SkillExample>>({});

  const handleAdd = () => {
    setIsAdding(true);
    setDraft({ input: "", output: "", context: "" });
  };

  const handleSaveNew = () => {
    if (!draft.input?.trim() || !draft.output?.trim()) return;

    onChange([
      ...examples,
      {
        id: nanoid(),
        input: draft.input.trim(),
        output: draft.output.trim(),
        context: draft.context?.trim() || undefined,
      },
    ]);
    setIsAdding(false);
    setDraft({});
  };

  const handleEdit = (example: SkillExample) => {
    setEditingId(example.id);
    setDraft({ ...example });
  };

  const handleSaveEdit = () => {
    if (!editingId || !draft.input?.trim() || !draft.output?.trim()) return;

    onChange(
      examples.map((e) =>
        e.id === editingId
          ? {
              ...e,
              input: draft.input!.trim(),
              output: draft.output!.trim(),
              context: draft.context?.trim() || undefined,
            }
          : e
      )
    );
    setEditingId(null);
    setDraft({});
  };

  const handleDelete = (id: string) => {
    onChange(examples.filter((e) => e.id !== id));
  };

  const handleCancel = () => {
    setIsAdding(false);
    setEditingId(null);
    setDraft({});
  };

  const renderForm = (isNew: boolean) => (
    <div className="space-y-3">
      <div>
        <label className="mb-1 block text-sm font-medium">Context (optional)</label>
        <Input
          placeholder="e.g., Customer requesting refund"
          value={draft.context || ""}
          onChange={(e) => setDraft({ ...draft, context: e.target.value })}
          autoFocus={isNew}
        />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">
          Input <span className="text-destructive">*</span>
        </label>
        <Textarea
          placeholder="Sample input or question..."
          value={draft.input || ""}
          onChange={(e) => setDraft({ ...draft, input: e.target.value })}
          rows={3}
        />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">
          Expected Output <span className="text-destructive">*</span>
        </label>
        <Textarea
          placeholder="Ideal response..."
          value={draft.output || ""}
          onChange={(e) => setDraft({ ...draft, output: e.target.value })}
          rows={3}
        />
      </div>
      <div className="flex justify-end gap-2">
        <Button type="button" variant="ghost" size="sm" onClick={handleCancel}>
          Cancel
        </Button>
        <Button
          type="button"
          size="sm"
          onClick={isNew ? handleSaveNew : handleSaveEdit}
          disabled={!draft.input?.trim() || !draft.output?.trim()}
        >
          {isNew ? "Add" : "Save"}
        </Button>
      </div>
    </div>
  );

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium">Examples</h4>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleAdd}
          disabled={isAdding || editingId !== null}
          className="gap-1"
        >
          <Plus className="h-4 w-4" />
          Add Example
        </Button>
      </div>

      {examples.length === 0 && !isAdding && (
        <p className="text-sm text-muted-foreground">
          No examples defined. Add input/output pairs to guide the skill.
        </p>
      )}

      <div className="space-y-2">
        {examples.map((example) => (
          <Card key={example.id} className="p-3">
            {editingId === example.id ? (
              renderForm(false)
            ) : (
              <div className="flex items-start justify-between">
                <div className="flex-1 space-y-2">
                  {example.context && (
                    <p className="text-xs text-muted-foreground">
                      Context: {example.context}
                    </p>
                  )}
                  <div>
                    <p className="text-xs font-medium text-muted-foreground">
                      Input
                    </p>
                    <p className="mt-1 rounded bg-muted p-2 text-sm">
                      {example.input}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-muted-foreground">
                      Output
                    </p>
                    <p className="mt-1 rounded bg-muted p-2 text-sm">
                      {example.output}
                    </p>
                  </div>
                </div>
                <div className="ml-2 flex flex-col gap-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => handleEdit(example)}
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-destructive hover:text-destructive"
                    onClick={() => handleDelete(example.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </Card>
        ))}

        {isAdding && (
          <Card className="border-dashed p-3">{renderForm(true)}</Card>
        )}
      </div>
    </div>
  );
}
