"use client";

import { useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Sparkles, Search, Loader2 } from "lucide-react";
import { useSkills } from "@/lib/hooks/use-skills";
import { cn } from "@/lib/utils";
import { SKILL_CATEGORY_LABELS } from "@/types/skill";

interface SkillSelectorSheetProps {
  selectedSkills: string[];
  onSkillsChange: (skills: string[]) => void;
  trigger?: React.ReactNode;
}

export function SkillSelectorSheet({
  selectedSkills,
  onSkillsChange,
  trigger,
}: SkillSelectorSheetProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  // Show all user's skills (draft + published) - they can use their own drafts
  const { data: skillsData, isLoading } = useSkills();

  const skills = skillsData?.skills || [];

  // Filter skills by search
  const filteredSkills = skills.filter(
    (skill) =>
      skill.name.toLowerCase().includes(search.toLowerCase()) ||
      skill.description.toLowerCase().includes(search.toLowerCase()) ||
      skill.tags.some((tag) =>
        tag.toLowerCase().includes(search.toLowerCase())
      )
  );

  const toggleSkill = (skillId: string) => {
    if (selectedSkills.includes(skillId)) {
      onSkillsChange(selectedSkills.filter((id) => id !== skillId));
    } else {
      onSkillsChange([...selectedSkills, skillId]);
    }
  };

  const clearAll = () => {
    onSkillsChange([]);
  };

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        {trigger || (
          <Button variant="outline" size="sm">
            <Sparkles className="h-3 w-3 mr-1" />
            Select Skills ({selectedSkills.length})
          </Button>
        )}
      </SheetTrigger>
      <SheetContent side="right" className="w-[400px] sm:w-[450px]">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Select Skills
          </SheetTitle>
        </SheetHeader>

        <div className="mt-4 space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search skills..."
              className="pl-9"
            />
          </div>

          <p className="text-sm text-muted-foreground">
            Skills provide domain expertise, terminology, and reasoning patterns
            to enhance your agent.
          </p>

          {/* Skills List */}
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : filteredSkills.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {search ? "No skills match your search" : "No skills available"}
            </div>
          ) : (
            <div className="space-y-2 max-h-[60vh] overflow-y-auto">
              {filteredSkills.map((skill) => {
                const isSelected = selectedSkills.includes(skill.id);
                return (
                  <div
                    key={skill.id}
                    className={cn(
                      "flex items-start justify-between p-3 rounded-lg border transition-colors",
                      isSelected && "border-primary bg-primary/5"
                    )}
                  >
                    <div className="flex-1 min-w-0 mr-3">
                      <div className="font-medium truncate">{skill.name}</div>
                      <div className="text-sm text-muted-foreground line-clamp-2">
                        {skill.description}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="secondary" className="text-xs">
                          {SKILL_CATEGORY_LABELS[skill.category]}
                        </Badge>
                        {skill.tags.slice(0, 2).map((tag) => (
                          <Badge
                            key={tag}
                            variant="outline"
                            className="text-xs"
                          >
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <Switch
                      checked={isSelected}
                      onCheckedChange={() => toggleSkill(skill.id)}
                    />
                  </div>
                );
              })}
            </div>
          )}

          {/* Actions */}
          {selectedSkills.length > 0 && (
            <div className="flex justify-end pt-2 border-t">
              <Button variant="outline" size="sm" onClick={clearAll}>
                Clear All ({selectedSkills.length})
              </Button>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
