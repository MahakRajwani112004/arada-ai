"use client";

import { useState, useEffect, useCallback } from "react";
import { X, Tag, Folder, User, Save, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  updateDocumentMetadata,
  getDocumentTags,
  getDocumentCategories,
} from "@/lib/api/knowledge";
import type { KnowledgeDocument, DocumentTag } from "@/types/knowledge";
import { useToast } from "@/hooks/use-toast";

interface DocumentMetadataEditorProps {
  document: KnowledgeDocument | null;
  kbId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdate?: (doc: KnowledgeDocument) => void;
}

export function DocumentMetadataEditor({
  document,
  kbId,
  open,
  onOpenChange,
  onUpdate,
}: DocumentMetadataEditorProps) {
  const { toast } = useToast();

  // Form state
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const [category, setCategory] = useState("");
  const [author, setAuthor] = useState("");

  // Autocomplete state
  const [suggestedTags, setSuggestedTags] = useState<DocumentTag[]>([]);
  const [existingCategories, setExistingCategories] = useState<string[]>([]);
  const [showTagSuggestions, setShowTagSuggestions] = useState(false);

  // Loading state
  const [isSaving, setIsSaving] = useState(false);
  const [isLoadingTags, setIsLoadingTags] = useState(false);

  // Initialize form with document data
  useEffect(() => {
    if (document && open) {
      setTags(document.tags || []);
      setCategory(document.category || "");
      setAuthor(document.author || "");
      setTagInput("");

      // Load existing categories for dropdown
      loadCategories();
    }
  }, [document, open, kbId]);

  const loadCategories = async () => {
    try {
      const result = await getDocumentCategories(kbId);
      setExistingCategories(result.categories);
    } catch {
      // Ignore errors
    }
  };

  const loadTagSuggestions = useCallback(
    async (prefix: string) => {
      if (prefix.length < 1) {
        setSuggestedTags([]);
        return;
      }

      setIsLoadingTags(true);
      try {
        const result = await getDocumentTags(kbId, prefix, 10);
        // Filter out tags that are already added
        const filtered = result.tags.filter((t) => !tags.includes(t.tag));
        setSuggestedTags(filtered);
      } catch {
        setSuggestedTags([]);
      } finally {
        setIsLoadingTags(false);
      }
    },
    [kbId, tags]
  );

  // Debounced tag input handler
  useEffect(() => {
    const timer = setTimeout(() => {
      if (tagInput) {
        loadTagSuggestions(tagInput);
      } else {
        setSuggestedTags([]);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [tagInput, loadTagSuggestions]);

  const addTag = (tag: string) => {
    const trimmedTag = tag.trim().toLowerCase();
    if (trimmedTag && !tags.includes(trimmedTag)) {
      setTags([...tags, trimmedTag]);
    }
    setTagInput("");
    setSuggestedTags([]);
    setShowTagSuggestions(false);
  };

  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter((t) => t !== tagToRemove));
  };

  const handleTagInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (tagInput.trim()) {
        addTag(tagInput);
      }
    } else if (e.key === "Backspace" && !tagInput && tags.length > 0) {
      // Remove last tag when backspace pressed on empty input
      removeTag(tags[tags.length - 1]);
    }
  };

  const handleSave = async () => {
    if (!document) return;

    setIsSaving(true);
    try {
      const updatedDoc = await updateDocumentMetadata(kbId, document.id, {
        tags,
        category: category || undefined,
        author: author || undefined,
      });

      toast({
        title: "Metadata updated",
        description: "Document metadata has been saved.",
      });

      onUpdate?.(updatedDoc);
      onOpenChange(false);
    } catch (error) {
      toast({
        title: "Failed to save",
        description:
          error instanceof Error ? error.message : "Unknown error occurred",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (!document) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            Edit Metadata
            <span className="text-sm font-normal text-muted-foreground truncate max-w-[200px]">
              {document.filename}
            </span>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Tags */}
          <div className="space-y-2">
            <Label className="flex items-center gap-1">
              <Tag className="h-4 w-4" />
              Tags
            </Label>
            <div className="flex flex-wrap gap-1 p-2 border rounded-md min-h-[44px]">
              {tags.map((tag) => (
                <Badge key={tag} variant="secondary" className="gap-1">
                  {tag}
                  <button
                    onClick={() => removeTag(tag)}
                    className="ml-1 hover:text-destructive"
                    type="button"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
              <div className="relative flex-1 min-w-[120px]">
                <Input
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={handleTagInputKeyDown}
                  onFocus={() => setShowTagSuggestions(true)}
                  onBlur={() => {
                    // Delay to allow click on suggestions
                    setTimeout(() => setShowTagSuggestions(false), 200);
                  }}
                  placeholder="Add tag..."
                  className="border-0 h-7 px-2 focus-visible:ring-0"
                />
                {/* Tag suggestions dropdown */}
                {showTagSuggestions && suggestedTags.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-1 bg-background border rounded-md shadow-lg z-50 max-h-[150px] overflow-y-auto">
                    {isLoadingTags ? (
                      <div className="p-2 text-sm text-muted-foreground flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Loading...
                      </div>
                    ) : (
                      suggestedTags.map((suggestion) => (
                        <button
                          key={suggestion.tag}
                          onClick={() => addTag(suggestion.tag)}
                          className="w-full text-left px-3 py-2 hover:bg-muted text-sm flex justify-between"
                          type="button"
                        >
                          <span>{suggestion.tag}</span>
                          <span className="text-muted-foreground text-xs">
                            {suggestion.usage_count} docs
                          </span>
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              Press Enter to add a tag, or select from suggestions
            </p>
          </div>

          {/* Category */}
          <div className="space-y-2">
            <Label className="flex items-center gap-1">
              <Folder className="h-4 w-4" />
              Category
            </Label>
            <div className="flex gap-2">
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger className="flex-1">
                  <SelectValue placeholder="Select or type category..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">No category</SelectItem>
                  {existingCategories.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {cat}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Input
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="Or type new..."
                className="flex-1"
              />
            </div>
          </div>

          {/* Author */}
          <div className="space-y-2">
            <Label className="flex items-center gap-1">
              <User className="h-4 w-4" />
              Author
            </Label>
            <Input
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              placeholder="Document author..."
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
