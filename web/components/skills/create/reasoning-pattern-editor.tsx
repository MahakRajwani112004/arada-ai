"use client";

import { useState } from "react";
import { Plus, Trash2, Edit2, X, Check } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { ReasoningPattern } from "@/types/skill";
import { nanoid } from "nanoid";

interface ReasoningPatternEditorProps {
  patterns: ReasoningPattern[];
  onChange: (patterns: ReasoningPattern[]) => void;
}

export function ReasoningPatternEditor({
  patterns,
  onChange,
}: ReasoningPatternEditorProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<Partial<ReasoningPattern>>({});

  const handleAdd = () => {
    setIsAdding(true);
    setDraft({ name: "", description: "", steps: [""] });
  };

  const handleSaveNew = () => {
    if (!draft.name?.trim() || !draft.steps?.some((s) => s.trim())) return;

    onChange([
      ...patterns,
      {
        id: nanoid(),
        name: draft.name.trim(),
        description: draft.description?.trim(),
        steps: draft.steps.filter((s) => s.trim()),
      },
    ]);
    setIsAdding(false);
    setDraft({});
  };

  const handleEdit = (pattern: ReasoningPattern) => {
    setEditingId(pattern.id);
    setDraft({ ...pattern, steps: [...pattern.steps] });
  };

  const handleSaveEdit = () => {
    if (
      !editingId ||
      !draft.name?.trim() ||
      !draft.steps?.some((s) => s.trim())
    )
      return;

    onChange(
      patterns.map((p) =>
        p.id === editingId
          ? {
              ...p,
              name: draft.name!.trim(),
              description: draft.description?.trim(),
              steps: draft.steps!.filter((s) => s.trim()),
            }
          : p
      )
    );
    setEditingId(null);
    setDraft({});
  };

  const handleDelete = (id: string) => {
    onChange(patterns.filter((p) => p.id !== id));
  };

  const handleCancel = () => {
    setIsAdding(false);
    setEditingId(null);
    setDraft({});
  };

  const handleStepChange = (index: number, value: string) => {
    const newSteps = [...(draft.steps || [])];
    newSteps[index] = value;
    setDraft({ ...draft, steps: newSteps });
  };

  const handleAddStep = () => {
    setDraft({ ...draft, steps: [...(draft.steps || []), ""] });
  };

  const handleRemoveStep = (index: number) => {
    const newSteps = (draft.steps || []).filter((_, i) => i !== index);
    setDraft({ ...draft, steps: newSteps.length ? newSteps : [""] });
  };

  const renderStepEditor = () => (
    <div className="space-y-2">
      <span className="text-sm font-medium" id="steps-label">Steps</span>
      {(draft.steps || []).map((step, idx) => (
        <div key={idx} className="flex items-center gap-2">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-medium">
            {idx + 1}
          </span>
          <Input
            placeholder={`Step ${idx + 1}`}
            value={step}
            onChange={(e) => handleStepChange(idx, e.target.value)}
            aria-label={`Step ${idx + 1}`}
          />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-8 w-8 shrink-0"
            onClick={() => handleRemoveStep(idx)}
            disabled={(draft.steps || []).length <= 1}
            aria-label={`Remove step ${idx + 1}`}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      ))}
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={handleAddStep}
        className="gap-1"
      >
        <Plus className="h-4 w-4" />
        Add Step
      </Button>
    </div>
  );

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium">Reasoning Patterns</h4>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleAdd}
          disabled={isAdding || editingId !== null}
          className="gap-1"
        >
          <Plus className="h-4 w-4" />
          Add Pattern
        </Button>
      </div>

      {patterns.length === 0 && !isAdding && (
        <p className="text-sm text-muted-foreground">
          No reasoning patterns defined. Add step-by-step frameworks.
        </p>
      )}

      <div className="space-y-2">
        {patterns.map((pattern) => (
          <Card key={pattern.id} className="p-3">
            {editingId === pattern.id ? (
              <div className="space-y-3">
                <Input
                  placeholder="Pattern name"
                  value={draft.name || ""}
                  onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                  aria-label="Pattern name"
                  aria-required="true"
                />
                <Textarea
                  placeholder="Description (optional)"
                  value={draft.description || ""}
                  onChange={(e) =>
                    setDraft({ ...draft, description: e.target.value })
                  }
                  rows={2}
                  aria-label="Description"
                />
                {renderStepEditor()}
                <div className="flex justify-end gap-2">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={handleCancel}
                    aria-label="Cancel editing"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    onClick={handleSaveEdit}
                    disabled={
                      !draft.name?.trim() ||
                      !draft.steps?.some((s) => s.trim())
                    }
                    aria-label="Save changes"
                  >
                    <Check className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="font-medium">{pattern.name}</p>
                  {pattern.description && (
                    <p className="mt-1 text-sm text-muted-foreground">
                      {pattern.description}
                    </p>
                  )}
                  <ol className="mt-2 space-y-1">
                    {pattern.steps.map((step, idx) => (
                      <li
                        key={idx}
                        className="flex items-start gap-2 text-sm text-muted-foreground"
                      >
                        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                          {idx + 1}
                        </span>
                        {step}
                      </li>
                    ))}
                  </ol>
                </div>
                <div className="flex gap-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => handleEdit(pattern)}
                    aria-label={`Edit pattern ${pattern.name}`}
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-destructive hover:text-destructive"
                    onClick={() => handleDelete(pattern.id)}
                    aria-label={`Delete pattern ${pattern.name}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </Card>
        ))}

        {isAdding && (
          <Card className="border-dashed p-3">
            <div className="space-y-3">
              <Input
                placeholder="Pattern name (e.g., Risk Assessment)"
                value={draft.name || ""}
                onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                autoFocus
                aria-label="Pattern name"
                aria-required="true"
              />
              <Textarea
                placeholder="Description (optional)"
                value={draft.description || ""}
                onChange={(e) =>
                  setDraft({ ...draft, description: e.target.value })
                }
                rows={2}
                aria-label="Description"
              />
              {renderStepEditor()}
              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleCancel}
                >
                  Cancel
                </Button>
                <Button
                  type="button"
                  size="sm"
                  onClick={handleSaveNew}
                  disabled={
                    !draft.name?.trim() || !draft.steps?.some((s) => s.trim())
                  }
                >
                  Add
                </Button>
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
