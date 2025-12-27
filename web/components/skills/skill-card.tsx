"use client";

import Link from "next/link";
import {
  Lightbulb,
  MoreVertical,
  Trash2,
  Copy,
  Clock,
  Globe,
  Star,
  Download,
  Eye,
} from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { SkillSummary, SkillCategory } from "@/types/skill";
import { SKILL_CATEGORY_LABELS, SKILL_STATUS_LABELS } from "@/types/skill";
import { formatDistanceToNow } from "date-fns";

interface SkillCardProps {
  skill: SkillSummary;
  onDelete?: (id: string) => void;
  onDuplicate?: (id: string) => void;
  onView?: (id: string) => void;
  showActions?: boolean;
}

const categoryColors: Record<SkillCategory, string> = {
  domain_expertise: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  document_generation: "bg-green-500/10 text-green-400 border-green-500/20",
  data_analysis: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  communication: "bg-orange-500/10 text-orange-400 border-orange-500/20",
  research: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
  coding: "bg-violet-500/10 text-violet-400 border-violet-500/20",
  custom: "bg-gray-500/10 text-gray-400 border-gray-500/20",
};

const statusColors: Record<string, string> = {
  draft: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
  published: "bg-green-500/10 text-green-400 border-green-500/20",
  archived: "bg-gray-500/10 text-gray-400 border-gray-500/20",
};

function getCategoryColor(category: SkillCategory): string {
  return categoryColors[category] || categoryColors.custom;
}

function getStatusColor(status: string): string {
  return statusColors[status] || statusColors.draft;
}

export function SkillCard({
  skill,
  onDelete,
  onDuplicate,
  onView,
  showActions = true,
}: SkillCardProps) {
  const updatedAgo = formatDistanceToNow(new Date(skill.updated_at), {
    addSuffix: true,
  });

  return (
    <Link href={`/skills/${skill.id}`}>
      <Card className="group h-full cursor-pointer transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5">
        <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-amber-500/20 to-orange-500/20">
              <Lightbulb className="h-5 w-5 text-amber-400" />
            </div>
            <div>
              <h3 className="font-semibold leading-none tracking-tight">
                {skill.name}
              </h3>
              <div className="mt-1.5 flex items-center gap-2 flex-wrap">
                <Badge
                  variant="outline"
                  className={`gap-1 ${getCategoryColor(skill.category)}`}
                >
                  {SKILL_CATEGORY_LABELS[skill.category]}
                </Badge>
                <Badge
                  variant="outline"
                  className={getStatusColor(skill.status)}
                >
                  {SKILL_STATUS_LABELS[skill.status]}
                </Badge>
              </div>
            </div>
          </div>
          {showActions && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild onClick={(e) => e.preventDefault()}>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 opacity-0 group-hover:opacity-100"
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={(e) => {
                    e.preventDefault();
                    onView?.(skill.id);
                  }}
                >
                  <Eye className="mr-2 h-4 w-4" />
                  View Details
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={(e) => {
                    e.preventDefault();
                    onDuplicate?.(skill.id);
                  }}
                >
                  <Copy className="mr-2 h-4 w-4" />
                  Duplicate
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onClick={(e) => {
                    e.preventDefault();
                    onDelete?.(skill.id);
                  }}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </CardHeader>
        <CardContent>
          <p className="line-clamp-2 text-sm text-muted-foreground">
            {skill.description || "No description provided"}
          </p>

          {/* Tags */}
          {skill.tags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1">
              {skill.tags.slice(0, 3).map((tag) => (
                <Badge
                  key={tag}
                  variant="secondary"
                  className="text-xs px-1.5 py-0"
                >
                  {tag}
                </Badge>
              ))}
              {skill.tags.length > 3 && (
                <Badge
                  variant="secondary"
                  className="text-xs px-1.5 py-0 opacity-60"
                >
                  +{skill.tags.length - 3}
                </Badge>
              )}
            </div>
          )}

          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              <span>Updated {updatedAgo}</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {skill.is_public && (
                <div className="flex items-center gap-1">
                  <Globe className="h-3 w-3" />
                  <span>Public</span>
                </div>
              )}
              {skill.rating_avg && (
                <div className="flex items-center gap-0.5">
                  <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                  <span>{skill.rating_avg.toFixed(1)}</span>
                </div>
              )}
              <span>v{skill.version}</span>
            </div>
          </div>

          {/* Marketplace stats for public skills */}
          {skill.is_public && skill.rating_count > 0 && (
            <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <Download className="h-3 w-3" />
                <span>{skill.rating_count} installs</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
