"use client";

import { useState } from "react";
import { Plus, Trash2, Edit2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { SkillParameter } from "@/types/skill";
import { nanoid } from "nanoid";

interface ParametersSectionProps {
  parameters: SkillParameter[];
  onChange: (parameters: SkillParameter[]) => void;
}

const PARAM_TYPES = [
  { value: "string", label: "Text" },
  { value: "number", label: "Number" },
  { value: "boolean", label: "Yes/No" },
  { value: "select", label: "Selection" },
] as const;

export function ParametersSection({
  parameters,
  onChange,
}: ParametersSectionProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<Partial<SkillParameter>>({});
  const [optionsInput, setOptionsInput] = useState("");

  const handleAdd = () => {
    setIsAdding(true);
    setDraft({ name: "", type: "string", required: false });
    setOptionsInput("");
  };

  const handleSaveNew = () => {
    if (!draft.name?.trim()) return;

    const param: SkillParameter = {
      id: nanoid(),
      name: draft.name.trim(),
      type: draft.type || "string",
      description: draft.description?.trim(),
      required: draft.required || false,
      default_value: draft.default_value,
      options:
        draft.type === "select"
          ? optionsInput
              .split(",")
              .map((o) => o.trim())
              .filter(Boolean)
          : undefined,
    };

    onChange([...parameters, param]);
    setIsAdding(false);
    setDraft({});
    setOptionsInput("");
  };

  const handleEdit = (param: SkillParameter) => {
    setEditingId(param.id);
    setDraft({ ...param });
    setOptionsInput(param.options?.join(", ") || "");
  };

  const handleSaveEdit = () => {
    if (!editingId || !draft.name?.trim()) return;

    onChange(
      parameters.map((p) =>
        p.id === editingId
          ? {
              ...p,
              name: draft.name!.trim(),
              type: draft.type || "string",
              description: draft.description?.trim(),
              required: draft.required || false,
              default_value: draft.default_value,
              options:
                draft.type === "select"
                  ? optionsInput
                      .split(",")
                      .map((o) => o.trim())
                      .filter(Boolean)
                  : undefined,
            }
          : p
      )
    );
    setEditingId(null);
    setDraft({});
    setOptionsInput("");
  };

  const handleDelete = (id: string) => {
    onChange(parameters.filter((p) => p.id !== id));
  };

  const handleCancel = () => {
    setIsAdding(false);
    setEditingId(null);
    setDraft({});
    setOptionsInput("");
  };

  const renderForm = (isNew: boolean) => (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-sm font-medium">
            Parameter Name <span className="text-destructive">*</span>
          </label>
          <Input
            placeholder="e.g., jurisdiction"
            value={draft.name || ""}
            onChange={(e) => setDraft({ ...draft, name: e.target.value })}
            autoFocus={isNew}
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Type</label>
          <Select
            value={draft.type || "string"}
            onValueChange={(v) =>
              setDraft({
                ...draft,
                type: v as SkillParameter["type"],
                default_value: undefined,
              })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PARAM_TYPES.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  {type.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium">Description</label>
        <Textarea
          placeholder="What does this parameter control?"
          value={draft.description || ""}
          onChange={(e) => setDraft({ ...draft, description: e.target.value })}
          rows={2}
        />
      </div>

      {draft.type === "select" && (
        <div>
          <label className="mb-1 block text-sm font-medium">
            Options (comma-separated)
          </label>
          <Input
            placeholder="e.g., US, UK, EU, Other"
            value={optionsInput}
            onChange={(e) => setOptionsInput(e.target.value)}
          />
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-sm font-medium">Default Value</label>
          {draft.type === "boolean" ? (
            <Select
              value={String(draft.default_value ?? "")}
              onValueChange={(v) =>
                setDraft({
                  ...draft,
                  default_value: v === "true" ? true : v === "false" ? false : undefined,
                })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="No default" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">No default</SelectItem>
                <SelectItem value="true">Yes</SelectItem>
                <SelectItem value="false">No</SelectItem>
              </SelectContent>
            </Select>
          ) : draft.type === "select" && optionsInput ? (
            <Select
              value={String(draft.default_value ?? "")}
              onValueChange={(v) => setDraft({ ...draft, default_value: v || undefined })}
            >
              <SelectTrigger>
                <SelectValue placeholder="No default" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">No default</SelectItem>
                {optionsInput
                  .split(",")
                  .map((o) => o.trim())
                  .filter(Boolean)
                  .map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          ) : (
            <Input
              type={draft.type === "number" ? "number" : "text"}
              placeholder="Optional default"
              value={draft.default_value as string ?? ""}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  default_value: e.target.value || undefined,
                })
              }
            />
          )}
        </div>
        <div className="flex items-end">
          <label className="flex items-center gap-2">
            <Checkbox
              checked={draft.required || false}
              onCheckedChange={(checked) =>
                setDraft({ ...draft, required: !!checked })
              }
            />
            <span className="text-sm">Required</span>
          </label>
        </div>
      </div>

      <div className="flex justify-end gap-2">
        <Button type="button" variant="ghost" size="sm" onClick={handleCancel}>
          Cancel
        </Button>
        <Button
          type="button"
          size="sm"
          onClick={isNew ? handleSaveNew : handleSaveEdit}
          disabled={!draft.name?.trim()}
        >
          {isNew ? "Add" : "Save"}
        </Button>
      </div>
    </div>
  );

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-medium">Parameters</h4>
          <p className="text-xs text-muted-foreground">
            Configurable options that can be set when using the skill
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleAdd}
          disabled={isAdding || editingId !== null}
          className="gap-1"
        >
          <Plus className="h-4 w-4" />
          Add Parameter
        </Button>
      </div>

      {parameters.length === 0 && !isAdding && (
        <p className="text-sm text-muted-foreground">
          No parameters defined. Parameters let agents customize skill behavior.
        </p>
      )}

      <div className="space-y-2">
        {parameters.map((param) => (
          <Card key={param.id} className="p-3">
            {editingId === param.id ? (
              renderForm(false)
            ) : (
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{param.name}</p>
                    <Badge variant="outline" className="text-xs">
                      {PARAM_TYPES.find((t) => t.value === param.type)?.label}
                    </Badge>
                    {param.required && (
                      <Badge variant="secondary" className="text-xs">
                        Required
                      </Badge>
                    )}
                  </div>
                  {param.description && (
                    <p className="mt-1 text-sm text-muted-foreground">
                      {param.description}
                    </p>
                  )}
                  <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                    {param.default_value !== undefined && (
                      <span>Default: {String(param.default_value)}</span>
                    )}
                    {param.options && param.options.length > 0 && (
                      <span>Options: {param.options.join(", ")}</span>
                    )}
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => handleEdit(param)}
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-destructive hover:text-destructive"
                    onClick={() => handleDelete(param.id)}
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
