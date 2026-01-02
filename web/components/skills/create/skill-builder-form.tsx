"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  BookOpen,
  Brain,
  Settings,
  Sparkles,
  ChevronRight,
  Check,
  Loader2,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { BasicInfoSection } from "./basic-info-section";
import { DomainKnowledgeSection } from "./domain-knowledge-section";
import { ResourcesSection } from "./resources-section";
import { ParametersSection } from "./parameters-section";
import { PromptEditor } from "./prompt-editor";
import {
  createEmptySkillDefinition,
  type SkillCategory,
  type SkillDefinition,
  type CreateSkillRequest,
} from "@/types/skill";
import { useCreateSkill, useUpdateSkill } from "@/lib/hooks/use-skills";

interface SkillBuilderFormProps {
  initialData?: {
    id?: string;
    name: string;
    description: string;
    category: SkillCategory;
    tags: string[];
    definition: SkillDefinition;
  };
  mode: "create" | "edit";
}

interface SectionStatus {
  basicInfo: boolean;
  domain: boolean;
  parameters: boolean;
  prompts: boolean;
}

export function SkillBuilderForm({ initialData, mode }: SkillBuilderFormProps) {
  const router = useRouter();
  const createSkill = useCreateSkill();
  const updateSkill = useUpdateSkill();

  // Form state
  const [name, setName] = useState(initialData?.name || "");
  const [description, setDescription] = useState(initialData?.description || "");
  const [category, setCategory] = useState<SkillCategory>(
    initialData?.category || "custom"
  );
  const [tags, setTags] = useState<string[]>(initialData?.tags || []);
  const [tagInput, setTagInput] = useState("");
  const [definition, setDefinition] = useState<SkillDefinition>(
    initialData?.definition || createEmptySkillDefinition()
  );

  // Calculate section completion status
  const getSectionStatus = (): SectionStatus => ({
    basicInfo: !!name.trim() && !!category,
    domain:
      definition.capability.expertise.terminology.length > 0 ||
      definition.capability.expertise.reasoning_patterns.length > 0 ||
      definition.capability.expertise.examples.length > 0,
    parameters: true, // Optional section
    prompts: !!definition.prompts.system_enhancement.trim(),
  });

  const status = getSectionStatus();

  const isValid = status.basicInfo && (status.domain || status.prompts);

  const handleSubmit = () => {
    if (!isValid) return;

    // Update definition metadata
    const finalDefinition: SkillDefinition = {
      ...definition,
      metadata: {
        ...definition.metadata,
        name,
        category,
        tags,
      },
    };

    const request: CreateSkillRequest = {
      name,
      description,
      category,
      tags,
      definition: finalDefinition,
    };

    if (mode === "edit" && initialData?.id) {
      updateSkill.mutate(
        { skillId: initialData.id, request },
        {
          onSuccess: () => router.push(`/skills/${initialData.id}`),
        }
      );
    } else {
      createSkill.mutate(request, {
        onSuccess: (skill) => router.push(`/skills/${skill.id}`),
      });
    }
  };

  const isPending = createSkill.isPending || updateSkill.isPending;

  return (
    <div className="space-y-6">
      <Accordion
        type="multiple"
        defaultValue={["basicInfo", "domain"]}
        className="space-y-4"
      >
        {/* Basic Information */}
        <AccordionItem value="basicInfo" className="rounded-lg border">
          <AccordionTrigger className="px-4 hover:no-underline">
            <div className="flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-blue-400" />
              <span className="font-semibold">Basic Information</span>
              {status.basicInfo ? (
                <Badge variant="secondary" className="ml-2 gap-1">
                  <Check className="h-3 w-3" />
                  Complete
                </Badge>
              ) : (
                <Badge variant="outline" className="ml-2">
                  Required
                </Badge>
              )}
            </div>
          </AccordionTrigger>
          <AccordionContent className="px-4 pb-4">
            <BasicInfoSection
              name={name}
              description={description}
              category={category}
              tags={tags}
              tagInput={tagInput}
              onNameChange={setName}
              onDescriptionChange={setDescription}
              onCategoryChange={setCategory}
              onTagsChange={setTags}
              onTagInputChange={setTagInput}
            />
          </AccordionContent>
        </AccordionItem>

        {/* Domain Knowledge */}
        <AccordionItem value="domain" className="rounded-lg border">
          <AccordionTrigger className="px-4 hover:no-underline">
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-purple-400" />
              <span className="font-semibold">Domain Knowledge</span>
              {status.domain ? (
                <Badge variant="secondary" className="ml-2 gap-1">
                  <Check className="h-3 w-3" />
                  {definition.capability.expertise.terminology.length} terms,{" "}
                  {definition.capability.expertise.reasoning_patterns.length}{" "}
                  patterns
                </Badge>
              ) : (
                <Badge variant="outline" className="ml-2">
                  Add knowledge
                </Badge>
              )}
            </div>
          </AccordionTrigger>
          <AccordionContent className="px-4 pb-4">
            <DomainKnowledgeSection
              expertise={definition.capability.expertise}
              onChange={(expertise) =>
                setDefinition({
                  ...definition,
                  capability: { ...definition.capability, expertise },
                })
              }
            />
          </AccordionContent>
        </AccordionItem>

        {/* Resources */}
        <AccordionItem value="resources" className="rounded-lg border">
          <AccordionTrigger className="px-4 hover:no-underline">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-green-400" />
              <span className="font-semibold">Resources</span>
              <Badge variant="secondary" className="ml-2">
                {definition.resources.files.length} files,{" "}
                {definition.resources.code_snippets.length} snippets
              </Badge>
              <Badge variant="outline" className="text-xs">
                Optional
              </Badge>
            </div>
          </AccordionTrigger>
          <AccordionContent className="px-4 pb-4">
            <ResourcesSection
              skillId={initialData?.id}
              resources={definition.resources}
              onChange={(resources) =>
                setDefinition({ ...definition, resources })
              }
              mode={mode}
            />
          </AccordionContent>
        </AccordionItem>

        {/* Parameters */}
        <AccordionItem value="parameters" className="rounded-lg border">
          <AccordionTrigger className="px-4 hover:no-underline">
            <div className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-purple-400" />
              <span className="font-semibold">Parameters</span>
              <Badge variant="secondary" className="ml-2">
                {definition.parameters.length || "0"}
              </Badge>
              <Badge variant="outline" className="text-xs">
                Optional
              </Badge>
            </div>
          </AccordionTrigger>
          <AccordionContent className="px-4 pb-4">
            <ParametersSection
              parameters={definition.parameters}
              onChange={(parameters) =>
                setDefinition({ ...definition, parameters })
              }
            />
          </AccordionContent>
        </AccordionItem>

        {/* Prompt Enhancement */}
        <AccordionItem value="prompts" className="rounded-lg border">
          <AccordionTrigger className="px-4 hover:no-underline">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-amber-400" />
              <span className="font-semibold">Prompt Enhancement</span>
              {status.prompts ? (
                <Badge variant="secondary" className="ml-2 gap-1">
                  <Check className="h-3 w-3" />
                  Configured
                </Badge>
              ) : (
                <Badge variant="outline" className="ml-2">
                  Add template
                </Badge>
              )}
            </div>
          </AccordionTrigger>
          <AccordionContent className="px-4 pb-4">
            <PromptEditor
              prompts={definition.prompts}
              parameters={definition.parameters}
              terminology={definition.capability.expertise.terminology}
              onChange={(prompts) => setDefinition({ ...definition, prompts })}
            />
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      {/* Action Buttons */}
      <div className="flex items-center justify-between border-t pt-6">
        <Button variant="outline" onClick={() => router.back()}>
          Cancel
        </Button>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleSubmit}
            disabled={!isValid || isPending}
          >
            Save as Draft
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!isValid || isPending}
            className="gap-2"
          >
            {isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                {mode === "create" ? "Create Skill" : "Save Changes"}
                <ChevronRight className="h-4 w-4" />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
