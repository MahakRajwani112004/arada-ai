"use client";

import { useState } from "react";
import { GripVertical, Trash2, Edit2, Check, X, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import type { SkeletonStep, SuggestedAgent } from "@/types/workflow";

interface SkeletonStepCardProps {
  step: SkeletonStep;
  suggestion?: SuggestedAgent;
  stepNumber: number;
  totalSteps: number;
  onUpdate: (name: string, role: string) => void;
  onRemove: () => void;
  canRemove: boolean;
}

export function SkeletonStepCard({
  step,
  suggestion,
  stepNumber,
  totalSteps: _totalSteps,
  onUpdate,
  onRemove,
  canRemove,
}: SkeletonStepCardProps) {
  void _totalSteps; // Suppress unused variable warning - kept for API compatibility
  const [isEditing, setIsEditing] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [editName, setEditName] = useState(step.name);
  const [editRole, setEditRole] = useState(step.role);

  const handleSave = () => {
    onUpdate(editName, editRole);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditName(step.name);
    setEditRole(step.role);
    setIsEditing(false);
  };

  return (
    <div className="border rounded-lg bg-card">
      <div className="flex items-center gap-2 p-3">
        {/* Drag Handle */}
        <div className="cursor-grab text-muted-foreground hover:text-foreground">
          <GripVertical className="h-4 w-4" />
        </div>

        {/* Step Number */}
        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-medium">
          {stepNumber}
        </div>

        {/* Step Content */}
        <div className="flex-1 min-w-0">
          {isEditing ? (
            <div className="space-y-2">
              <Input
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                placeholder="Step name"
                className="h-8"
              />
              <Textarea
                value={editRole}
                onChange={(e) => setEditRole(e.target.value)}
                placeholder="What should this step do?"
                rows={2}
                className="resize-none text-sm"
              />
              <div className="flex gap-2">
                <Button size="sm" onClick={handleSave}>
                  <Check className="h-3 w-3 mr-1" />
                  Save
                </Button>
                <Button size="sm" variant="ghost" onClick={handleCancel}>
                  <X className="h-3 w-3 mr-1" />
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-1">
              <p className="font-medium text-sm truncate">{step.name}</p>
              <p className="text-xs text-muted-foreground line-clamp-2">{step.role}</p>
            </div>
          )}
        </div>

        {/* Actions */}
        {!isEditing && (
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => setIsEditing(true)}
            >
              <Edit2 className="h-3.5 w-3.5" />
            </Button>
            {canRemove && (
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-destructive hover:text-destructive"
                onClick={onRemove}
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
        )}
      </div>

      {/* AI Suggestion Preview */}
      {suggestion && !isEditing && (
        <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
          <CollapsibleTrigger asChild>
            <button className="w-full flex items-center justify-between px-3 py-2 border-t text-xs text-muted-foreground hover:bg-muted/50 transition-colors">
              <span>AI suggests: {suggestion.name}</span>
              {isExpanded ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
            </button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="px-3 pb-3 space-y-2">
              <div>
                <p className="text-xs font-medium text-muted-foreground">Goal:</p>
                <p className="text-xs">{suggestion.goal}</p>
              </div>
              {suggestion.required_mcps.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Required integrations:</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {suggestion.required_mcps.map((mcp) => (
                      <Badge key={mcp} variant="outline" className="text-xs">
                        {mcp}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {suggestion.suggested_tools.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Suggested tools:</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {suggestion.suggested_tools.map((tool) => (
                      <Badge key={tool} variant="secondary" className="text-xs">
                        {tool}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CollapsibleContent>
        </Collapsible>
      )}
    </div>
  );
}
