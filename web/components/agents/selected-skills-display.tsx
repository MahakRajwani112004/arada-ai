"use client";

import { Badge } from "@/components/ui/badge";
import { X, Sparkles } from "lucide-react";
import { useSkills } from "@/lib/hooks/use-skills";

interface SelectedSkillsDisplayProps {
  selectedSkills: string[];
  onRemove: (skillId: string) => void;
}

export function SelectedSkillsDisplay({
  selectedSkills,
  onRemove,
}: SelectedSkillsDisplayProps) {
  const { data: skillsData } = useSkills();
  const skills = skillsData?.skills || [];

  if (selectedSkills.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No skills selected</p>
    );
  }

  const getSkillName = (skillId: string) => {
    const skill = skills.find((s) => s.id === skillId);
    return skill?.name || skillId;
  };

  return (
    <div className="flex flex-wrap gap-2">
      {selectedSkills.map((skillId) => (
        <Badge key={skillId} variant="secondary" className="gap-1 pr-1">
          <Sparkles className="h-3 w-3" />
          <span>{getSkillName(skillId)}</span>
          <button
            type="button"
            onClick={() => onRemove(skillId)}
            className="ml-1 hover:bg-muted rounded-full p-0.5"
          >
            <X className="h-3 w-3" />
          </button>
        </Badge>
      ))}
    </div>
  );
}
