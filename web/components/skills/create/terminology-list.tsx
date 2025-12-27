"use client";

import { useState } from "react";
import { Plus, Trash2, Edit2, X, Check } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { Terminology } from "@/types/skill";
import { nanoid } from "nanoid";

interface TerminologyListProps {
  items: Terminology[];
  onChange: (items: Terminology[]) => void;
}

export function TerminologyList({ items, onChange }: TerminologyListProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<Partial<Terminology>>({});

  const handleAdd = () => {
    setIsAdding(true);
    setDraft({ term: "", definition: "", aliases: [] });
  };

  const handleSaveNew = () => {
    if (!draft.term?.trim() || !draft.definition?.trim()) return;

    onChange([
      ...items,
      {
        id: nanoid(),
        term: draft.term.trim(),
        definition: draft.definition.trim(),
        aliases: draft.aliases || [],
      },
    ]);
    setIsAdding(false);
    setDraft({});
  };

  const handleEdit = (item: Terminology) => {
    setEditingId(item.id);
    setDraft({ ...item });
  };

  const handleSaveEdit = () => {
    if (!editingId || !draft.term?.trim() || !draft.definition?.trim()) return;

    onChange(
      items.map((item) =>
        item.id === editingId
          ? {
              ...item,
              term: draft.term!.trim(),
              definition: draft.definition!.trim(),
              aliases: draft.aliases || [],
            }
          : item
      )
    );
    setEditingId(null);
    setDraft({});
  };

  const handleDelete = (id: string) => {
    onChange(items.filter((item) => item.id !== id));
  };

  const handleCancel = () => {
    setIsAdding(false);
    setEditingId(null);
    setDraft({});
  };

  const handleAliasesChange = (value: string) => {
    const aliases = value
      .split(",")
      .map((a) => a.trim())
      .filter(Boolean);
    setDraft({ ...draft, aliases });
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium">Terminology</h4>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleAdd}
          disabled={isAdding || editingId !== null}
          className="gap-1"
        >
          <Plus className="h-4 w-4" />
          Add Term
        </Button>
      </div>

      {items.length === 0 && !isAdding && (
        <p className="text-sm text-muted-foreground">
          No terminology defined. Add key terms and their definitions.
        </p>
      )}

      <div className="space-y-2">
        {items.map((item) => (
          <Card key={item.id} className="p-3">
            {editingId === item.id ? (
              <div className="space-y-3">
                <Input
                  placeholder="Term"
                  value={draft.term || ""}
                  onChange={(e) => setDraft({ ...draft, term: e.target.value })}
                />
                <Textarea
                  placeholder="Definition"
                  value={draft.definition || ""}
                  onChange={(e) =>
                    setDraft({ ...draft, definition: e.target.value })
                  }
                  rows={2}
                />
                <Input
                  placeholder="Aliases (comma-separated)"
                  value={draft.aliases?.join(", ") || ""}
                  onChange={(e) => handleAliasesChange(e.target.value)}
                />
                <div className="flex justify-end gap-2">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={handleCancel}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    onClick={handleSaveEdit}
                    disabled={!draft.term?.trim() || !draft.definition?.trim()}
                  >
                    <Check className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium">{item.term}</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {item.definition}
                  </p>
                  {item.aliases && item.aliases.length > 0 && (
                    <p className="mt-1 text-xs text-muted-foreground">
                      Also: {item.aliases.join(", ")}
                    </p>
                  )}
                </div>
                <div className="flex gap-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => handleEdit(item)}
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-destructive hover:text-destructive"
                    onClick={() => handleDelete(item.id)}
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
                placeholder="Term"
                value={draft.term || ""}
                onChange={(e) => setDraft({ ...draft, term: e.target.value })}
                autoFocus
              />
              <Textarea
                placeholder="Definition"
                value={draft.definition || ""}
                onChange={(e) =>
                  setDraft({ ...draft, definition: e.target.value })
                }
                rows={2}
              />
              <Input
                placeholder="Aliases (comma-separated, optional)"
                value={draft.aliases?.join(", ") || ""}
                onChange={(e) => handleAliasesChange(e.target.value)}
              />
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
                  disabled={!draft.term?.trim() || !draft.definition?.trim()}
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
