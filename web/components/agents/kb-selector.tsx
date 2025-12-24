"use client";

import { useState } from "react";
import Link from "next/link";
import { BookOpen, ChevronDown, X, Plus, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Skeleton } from "@/components/ui/skeleton";
import { useKnowledgeBases } from "@/lib/hooks/use-knowledge";
import type { KnowledgeBase } from "@/types/knowledge";
import type { KnowledgeBaseConfig } from "@/types/agent";

interface KBSelectorProps {
  value?: KnowledgeBaseConfig;
  onChange: (config: KnowledgeBaseConfig | undefined) => void;
  disabled?: boolean;
}

export function KBSelector({ value, onChange, disabled }: KBSelectorProps) {
  const { data, isLoading } = useKnowledgeBases();
  const [open, setOpen] = useState(false);
  const [topK, setTopK] = useState(value?.top_k ?? 5);
  const [threshold, setThreshold] = useState(value?.similarity_threshold ?? 0.1);

  const knowledgeBases = data?.knowledge_bases ?? [];
  const selectedKB = knowledgeBases.find(
    (kb) => kb.collection_name === value?.collection_name
  );

  const handleSelect = (kb: KnowledgeBase) => {
    onChange({
      collection_name: kb.collection_name,
      embedding_model: kb.embedding_model,
      top_k: topK,
      similarity_threshold: threshold,
    });
    setOpen(false);
  };

  const handleClear = () => {
    onChange(undefined);
  };

  const handleAdvancedChange = () => {
    if (value) {
      onChange({
        ...value,
        top_k: topK,
        similarity_threshold: threshold,
      });
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Label>Knowledge Base</Label>
        <Skeleton className="h-10 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <Label>Knowledge Base</Label>

      {selectedKB ? (
        <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/30 p-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <BookOpen className="h-4 w-4" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="font-medium truncate">{selectedKB.name}</span>
              <Badge variant="secondary" className="shrink-0">
                {selectedKB.document_count} docs
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              {selectedKB.chunk_count.toLocaleString()} chunks indexed
            </p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 shrink-0"
            onClick={handleClear}
            disabled={disabled}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      ) : (
        <Popover open={open} onOpenChange={setOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              role="combobox"
              aria-expanded={open}
              className="w-full justify-between"
              disabled={disabled}
            >
              <span className="text-muted-foreground">
                Select a knowledge base...
              </span>
              <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-[400px] p-0" align="start">
            <Command>
              <CommandInput placeholder="Search knowledge bases..." />
              <CommandList>
                <CommandEmpty>
                  <div className="py-6 text-center">
                    <p className="text-sm text-muted-foreground">
                      No knowledge bases found.
                    </p>
                    <Link href="/integrations/knowledge">
                      <Button variant="link" size="sm" className="mt-2">
                        <Plus className="mr-1 h-3 w-3" />
                        Create one
                      </Button>
                    </Link>
                  </div>
                </CommandEmpty>
                <CommandGroup>
                  {knowledgeBases.map((kb) => (
                    <CommandItem
                      key={kb.id}
                      value={kb.name}
                      onSelect={() => handleSelect(kb)}
                      className="flex items-center gap-3 px-3 py-2.5"
                    >
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                        <BookOpen className="h-4 w-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="font-medium truncate">{kb.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {kb.document_count} documents &middot;{" "}
                          {kb.chunk_count.toLocaleString()} chunks
                        </div>
                      </div>
                    </CommandItem>
                  ))}
                </CommandGroup>
              </CommandList>
            </Command>
          </PopoverContent>
        </Popover>
      )}

      {!selectedKB && knowledgeBases.length === 0 && !isLoading && (
        <Link
          href="/integrations/knowledge"
          className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
        >
          <Plus className="h-3.5 w-3.5" />
          Create a Knowledge Base
          <ExternalLink className="h-3 w-3" />
        </Link>
      )}

      {selectedKB && (
        <Accordion type="single" collapsible className="w-full">
          <AccordionItem value="advanced" className="border-b-0">
            <AccordionTrigger className="py-2 text-sm text-muted-foreground hover:text-foreground">
              Advanced Settings
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-4 pt-2">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="top-k" className="text-xs">
                      Top K Results
                    </Label>
                    <Input
                      id="top-k"
                      type="number"
                      min={1}
                      max={20}
                      value={topK}
                      onChange={(e) => {
                        setTopK(parseInt(e.target.value) || 5);
                      }}
                      onBlur={handleAdvancedChange}
                      disabled={disabled}
                    />
                    <p className="text-xs text-muted-foreground">
                      Number of relevant chunks to retrieve
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="threshold" className="text-xs">
                      Similarity Threshold
                    </Label>
                    <Input
                      id="threshold"
                      type="number"
                      min={0}
                      max={1}
                      step={0.1}
                      value={threshold}
                      onChange={(e) => {
                        setThreshold(parseFloat(e.target.value) || 0.7);
                      }}
                      onBlur={handleAdvancedChange}
                      disabled={disabled}
                    />
                    <p className="text-xs text-muted-foreground">
                      Minimum similarity score (0-1)
                    </p>
                  </div>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      )}
    </div>
  );
}
