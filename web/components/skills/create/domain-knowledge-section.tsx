"use client";

import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { TerminologyList } from "./terminology-list";
import { ReasoningPatternEditor } from "./reasoning-pattern-editor";
import { ExamplesEditor } from "./examples-editor";
import type { SkillExpertise } from "@/types/skill";

interface DomainKnowledgeSectionProps {
  expertise: SkillExpertise;
  onChange: (expertise: SkillExpertise) => void;
}

export function DomainKnowledgeSection({
  expertise,
  onChange,
}: DomainKnowledgeSectionProps) {
  return (
    <div className="space-y-6">
      <div>
        <label className="mb-2 block text-sm font-medium">Domain</label>
        <Input
          placeholder="e.g., legal-contract-law, healthcare-compliance, financial-analysis"
          value={expertise.domain}
          onChange={(e) => onChange({ ...expertise, domain: e.target.value })}
        />
        <p className="mt-1 text-xs text-muted-foreground">
          A short identifier for the knowledge domain this skill covers
        </p>
      </div>

      <Separator />

      <TerminologyList
        items={expertise.terminology}
        onChange={(terminology) => onChange({ ...expertise, terminology })}
      />

      <Separator />

      <ReasoningPatternEditor
        patterns={expertise.reasoning_patterns}
        onChange={(reasoning_patterns) =>
          onChange({ ...expertise, reasoning_patterns })
        }
      />

      <Separator />

      <ExamplesEditor
        examples={expertise.examples}
        onChange={(examples) => onChange({ ...expertise, examples })}
      />
    </div>
  );
}
