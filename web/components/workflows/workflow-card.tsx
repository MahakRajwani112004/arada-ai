"use client";

import Link from "next/link";
import {
  Workflow,
  Play,
  MoreVertical,
  Trash2,
  Copy,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Circle,
  Bot,
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
import { Progress } from "@/components/ui/progress";
import type { WorkflowSummary } from "@/types/workflow";
import { formatDistanceToNow } from "date-fns";

export type WorkflowStatus = "draft" | "incomplete" | "ready";

interface WorkflowCardProps {
  workflow: WorkflowSummary;
  onDelete?: (id: string) => void;
  onCopy?: (id: string) => void;
  onRun?: (id: string) => void;
  isBlocked?: boolean;
  // New props for progress tracking
  totalSteps?: number;
  configuredSteps?: number;
  status?: WorkflowStatus;
}

const categoryColors: Record<string, string> = {
  "customer-support": "bg-blue-500/10 text-blue-400 border-blue-500/20",
  "data-processing": "bg-green-500/10 text-green-400 border-green-500/20",
  "content-creation": "bg-purple-500/10 text-purple-400 border-purple-500/20",
  "sales-automation": "bg-orange-500/10 text-orange-400 border-orange-500/20",
  "hr-onboarding": "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
  "ai-generated": "bg-violet-500/10 text-violet-400 border-violet-500/20",
  general: "bg-gray-500/10 text-gray-400 border-gray-500/20",
};

function getCategoryColor(category: string): string {
  return categoryColors[category] || categoryColors.general;
}

function formatCategory(category: string): string {
  return category
    .split("-")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

const statusConfig = {
  draft: {
    label: "Draft",
    color: "bg-gray-500/10 text-gray-400 border-gray-500/20",
    icon: Circle,
  },
  incomplete: {
    label: "Incomplete",
    color: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    icon: AlertTriangle,
  },
  ready: {
    label: "Ready",
    color: "bg-green-500/10 text-green-400 border-green-500/20",
    icon: CheckCircle2,
  },
};

export function WorkflowCard({
  workflow,
  onDelete,
  onCopy,
  onRun,
  isBlocked = false,
  totalSteps = 0,
  configuredSteps = 0,
  status,
}: WorkflowCardProps) {
  const updatedAgo = formatDistanceToNow(new Date(workflow.updated_at), {
    addSuffix: true,
  });

  // Determine status from props or compute from isBlocked
  const computedStatus: WorkflowStatus = status || (isBlocked ? "incomplete" : totalSteps > 0 ? "ready" : "draft");
  const statusInfo = statusConfig[computedStatus];
  const StatusIcon = statusInfo.icon;
  const progressPercent = totalSteps > 0 ? Math.round((configuredSteps / totalSteps) * 100) : 0;

  return (
    <Link href={`/workflows/${workflow.id}`}>
      <Card className="group h-full cursor-pointer transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5">
        <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
          <div className="flex items-center gap-3">
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                isBlocked
                  ? "bg-amber-500/10"
                  : "bg-gradient-to-br from-purple-500/20 to-blue-500/20"
              }`}
            >
              {isBlocked ? (
                <AlertTriangle className="h-5 w-5 text-amber-400" />
              ) : (
                <Workflow className="h-5 w-5 text-primary" />
              )}
            </div>
            <div>
              <h3 className="font-semibold leading-none tracking-tight">
                {workflow.name}
              </h3>
              <div className="mt-1.5 flex items-center gap-2">
                <Badge
                  variant="outline"
                  className={`gap-1 ${getCategoryColor(workflow.category)}`}
                >
                  {formatCategory(workflow.category)}
                </Badge>
                {workflow.is_template && (
                  <Badge
                    variant="outline"
                    className="bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
                  >
                    Template
                  </Badge>
                )}
                <Badge
                  variant="outline"
                  className={`gap-1 ${statusInfo.color}`}
                >
                  <StatusIcon className="h-3 w-3" />
                  {statusInfo.label}
                </Badge>
              </div>
            </div>
          </div>
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
              {!isBlocked && (
                <DropdownMenuItem
                  onClick={(e) => {
                    e.preventDefault();
                    onRun?.(workflow.id);
                  }}
                >
                  <Play className="mr-2 h-4 w-4" />
                  Run Workflow
                </DropdownMenuItem>
              )}
              <DropdownMenuItem
                onClick={(e) => {
                  e.preventDefault();
                  onCopy?.(workflow.id);
                }}
              >
                <Copy className="mr-2 h-4 w-4" />
                Copy
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onClick={(e) => {
                  e.preventDefault();
                  onDelete?.(workflow.id);
                }}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </CardHeader>
        <CardContent className="flex flex-col">
          {/* Description - fixed height with ellipsis */}
          <p className="line-clamp-2 text-sm text-muted-foreground h-10">
            {workflow.description || "No description provided"}
          </p>

          {/* Progress indicator - always shown */}
          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-1 text-muted-foreground">
                <Bot className="h-3 w-3" />
                <span>
                  {configuredSteps}/{totalSteps} agents configured
                </span>
              </div>
              <span className={computedStatus === "ready" ? "text-green-400" : "text-muted-foreground"}>
                {progressPercent}%
              </span>
            </div>
            <Progress
              value={progressPercent}
              className="h-1.5"
            />
          </div>

          {/* Footer - fixed at bottom */}
          <div className="mt-4 flex items-center justify-between border-t border-border pt-3">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              <span>Updated {updatedAgo}</span>
            </div>
            <div className="text-xs text-muted-foreground">
              v{workflow.version}
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
