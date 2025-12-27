"use client";

import { X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  SKILL_CATEGORY_LABELS,
  type SkillCategory,
} from "@/types/skill";

interface BasicInfoSectionProps {
  name: string;
  description: string;
  category: SkillCategory;
  tags: string[];
  tagInput: string;
  onNameChange: (name: string) => void;
  onDescriptionChange: (description: string) => void;
  onCategoryChange: (category: SkillCategory) => void;
  onTagsChange: (tags: string[]) => void;
  onTagInputChange: (input: string) => void;
}

export function BasicInfoSection({
  name,
  description,
  category,
  tags,
  tagInput,
  onNameChange,
  onDescriptionChange,
  onCategoryChange,
  onTagsChange,
  onTagInputChange,
}: BasicInfoSectionProps) {
  const handleAddTag = () => {
    const trimmed = tagInput.trim().toLowerCase();
    if (trimmed && !tags.includes(trimmed)) {
      onTagsChange([...tags, trimmed]);
      onTagInputChange("");
    }
  };

  const handleRemoveTag = (tag: string) => {
    onTagsChange(tags.filter((t) => t !== tag));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddTag();
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="skill-name" className="mb-2 block text-sm font-medium">
          Name <span className="text-destructive">*</span>
        </label>
        <Input
          id="skill-name"
          placeholder="e.g., Legal Contract Analysis"
          value={name}
          onChange={(e) => onNameChange(e.target.value)}
          aria-required="true"
        />
      </div>

      <div>
        <label htmlFor="skill-category" className="mb-2 block text-sm font-medium">
          Category <span className="text-destructive">*</span>
        </label>
        <Select value={category} onValueChange={(v) => onCategoryChange(v as SkillCategory)}>
          <SelectTrigger id="skill-category" aria-required="true">
            <SelectValue placeholder="Select a category" />
          </SelectTrigger>
          <SelectContent>
            {Object.entries(SKILL_CATEGORY_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div>
        <label htmlFor="skill-description" className="mb-2 block text-sm font-medium">Description</label>
        <Textarea
          id="skill-description"
          placeholder="Describe what this skill does and when to use it..."
          value={description}
          onChange={(e) => onDescriptionChange(e.target.value)}
          rows={3}
        />
      </div>

      <div>
        <label htmlFor="skill-tags" className="mb-2 block text-sm font-medium">Tags</label>
        <div className="flex gap-2">
          <Input
            id="skill-tags"
            placeholder="Add a tag..."
            value={tagInput}
            onChange={(e) => onTagInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1"
          />
          <Button type="button" variant="outline" onClick={handleAddTag}>
            Add
          </Button>
        </div>
        {tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2" role="list" aria-label="Added tags">
            {tags.map((tag) => (
              <Badge key={tag} variant="secondary" className="gap-1" role="listitem">
                {tag}
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  className="ml-1 rounded-full hover:bg-muted-foreground/20"
                  aria-label={`Remove tag ${tag}`}
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
