"use client";

import { ArrowLeft, Play, MoreVertical, Trash2, Copy, AlertTriangle, LayoutGrid, CheckCircle2, Circle, Bot } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { WorkflowDetail } from "@/types/workflow";
import { formatDistanceToNow } from "date-fns";

export type WorkflowStatus = "draft" | "incomplete" | "ready";

interface WorkflowHeaderProps {
  workflow: WorkflowDetail;
  isBlocked?: boolean;
  executionCount?: number;
  totalSteps?: number;
  configuredSteps?: number;
  onRun?: () => void;
  onEdit?: () => void;
  onCopy?: () => void;
  onDelete?: () => void;
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

export function WorkflowHeader({
  workflow,
  isBlocked = false,
  executionCount = 0,
  totalSteps = 0,
  configuredSteps = 0,
  onRun,
  onEdit: _onEdit,
  onCopy,
  onDelete,
}: WorkflowHeaderProps) {
  void _onEdit; // Kept for API compatibility
  const router = useRouter();
  const updatedAgo = formatDistanceToNow(new Date(workflow.updated_at), {
    addSuffix: true,
  });

  // Determine status
  const computedStatus: WorkflowStatus = isBlocked ? "incomplete" : totalSteps > 0 ? "ready" : "draft";
  const statusInfo = statusConfig[computedStatus];
  const StatusIcon = statusInfo.icon;
  const progressPercent = totalSteps > 0 ? Math.round((configuredSteps / totalSteps) * 100) : 0;
  const hasProgress = totalSteps > 0;

  const handleEditInCanvas = () => {
    router.push(`/workflows/${workflow.id}/canvas`);
  };

  return (
    <div className="space-y-4">
      <Link
        href="/workflows"
        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Workflows
      </Link>

      <div className="rounded-lg border border-border bg-card p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-4">
            <div
              className={`flex h-12 w-12 items-center justify-center rounded-lg ${
                isBlocked
                  ? "bg-amber-500/10"
                  : "bg-gradient-to-br from-purple-500/20 to-blue-500/20"
              }`}
            >
              {isBlocked ? (
                <AlertTriangle className="h-6 w-6 text-amber-400" />
              ) : (
                <div className="h-6 w-6 rounded-full bg-gradient-to-br from-purple-500 to-blue-500" />
              )}
            </div>
            <div>
              <h1 className="text-2xl font-bold">{workflow.name}</h1>
              <p className="mt-1 text-muted-foreground">
                {workflow.description || "No description provided"}
              </p>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <Badge
                  variant="outline"
                  className={getCategoryColor(workflow.category)}
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
                <span className="text-sm text-muted-foreground">
                  • {executionCount} execution{executionCount !== 1 ? "s" : ""}
                </span>
                <span className="text-sm text-muted-foreground">
                  • Updated {updatedAgo}
                </span>
              </div>

              {/* Progress indicator */}
              {hasProgress && (
                <div className="mt-4 max-w-md space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Bot className="h-4 w-4" />
                      <span>
                        {configuredSteps}/{totalSteps} agents configured
                      </span>
                    </div>
                    <span className={computedStatus === "ready" ? "text-green-400 font-medium" : "text-muted-foreground"}>
                      {progressPercent}%
                    </span>
                  </div>
                  <Progress
                    value={progressPercent}
                    className="h-2"
                  />
                  {computedStatus === "incomplete" && (
                    <p className="text-xs text-amber-400">
                      {totalSteps - configuredSteps} agent{totalSteps - configuredSteps !== 1 ? "s" : ""} still need to be configured before running
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={handleEditInCanvas}
            >
              <LayoutGrid className="h-4 w-4" />
              Edit in Canvas
            </Button>
            <Button
              size="sm"
              className="gap-2"
              disabled={isBlocked}
              onClick={onRun}
            >
              <Play className="h-4 w-4" />
              Run
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={onCopy}>
                  <Copy className="mr-2 h-4 w-4" />
                  Duplicate
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onClick={onDelete}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </div>
  );
}
