"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Search,
  Filter,
  Inbox,
  ExternalLink,
  MessageSquare,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { PageContainer, PageHeader } from "@/components/layout/page-container";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { useApprovals, useApprovalStats, useRespondToApproval } from "@/lib/hooks/use-approvals";
import type { ApprovalStatus, ApprovalSummary } from "@/types/approval";
import { formatDistanceToNow } from "date-fns";

// ==================== Skeleton Components ====================

function ApprovalCardSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <Skeleton className="h-5 w-48 mb-2" />
            <Skeleton className="h-4 w-32" />
          </div>
          <Skeleton className="h-6 w-20" />
        </div>
      </CardHeader>
      <CardContent>
        <Skeleton className="h-4 w-full mb-2" />
        <Skeleton className="h-4 w-3/4" />
        <div className="mt-4 flex justify-between">
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-8 w-24" />
        </div>
      </CardContent>
    </Card>
  );
}

function StatCardSkeleton() {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-12 w-12 rounded-full" />
          <div>
            <Skeleton className="h-8 w-16" />
            <Skeleton className="h-4 w-24 mt-1" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ==================== Empty State ====================

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card/50 py-16">
      <motion.div
        animate={{ y: [0, -10, 0] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-green-500/20 to-emerald-500/20"
      >
        <Inbox className="h-8 w-8 text-green-400" />
      </motion.div>
      <h3 className="mt-6 text-lg font-semibold">All caught up!</h3>
      <p className="mt-2 max-w-sm text-center text-sm text-muted-foreground">
        You have no pending approval requests. Approvals will appear here when
        workflows require your sign-off.
      </p>
    </div>
  );
}

// ==================== Status Badge ====================

function StatusBadge({ status }: { status: ApprovalStatus }) {
  const variants: Record<ApprovalStatus, { icon: React.ReactNode; className: string; label: string }> = {
    pending: {
      icon: <Clock className="h-3 w-3" />,
      className: "bg-amber-500/10 text-amber-600 border-amber-500/20",
      label: "Pending",
    },
    approved: {
      icon: <CheckCircle2 className="h-3 w-3" />,
      className: "bg-green-500/10 text-green-600 border-green-500/20",
      label: "Approved",
    },
    rejected: {
      icon: <XCircle className="h-3 w-3" />,
      className: "bg-red-500/10 text-red-600 border-red-500/20",
      label: "Rejected",
    },
    expired: {
      icon: <AlertTriangle className="h-3 w-3" />,
      className: "bg-gray-500/10 text-gray-600 border-gray-500/20",
      label: "Expired",
    },
  };

  const variant = variants[status];

  return (
    <Badge variant="outline" className={`gap-1 ${variant.className}`}>
      {variant.icon}
      {variant.label}
    </Badge>
  );
}

// ==================== Approval Card ====================

interface ApprovalCardProps {
  approval: ApprovalSummary;
  onApprove: () => void;
  onReject: () => void;
}

function ApprovalCard({ approval, onApprove, onReject }: ApprovalCardProps) {
  const isPending = approval.status === "pending";
  const progress = approval.approvals_received_count / approval.required_approvals;

  return (
    <Card className={isPending ? "border-amber-500/30" : ""}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-base truncate">{approval.title}</CardTitle>
            <CardDescription className="mt-1 flex items-center gap-2">
              <span className="truncate">{approval.workflow_name || approval.workflow_id}</span>
              <Link
                href={`/workflows/${approval.workflow_id}`}
                className="text-primary hover:underline flex-shrink-0"
              >
                <ExternalLink className="h-3 w-3" />
              </Link>
            </CardDescription>
          </div>
          <StatusBadge status={approval.status} />
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground line-clamp-2">{approval.message}</p>

        {/* Progress indicator */}
        {approval.required_approvals > 1 && (
          <div className="mt-3">
            <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
              <span>Approvals</span>
              <span>
                {approval.approvals_received_count} / {approval.required_approvals}
              </span>
            </div>
            <div className="h-1.5 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all"
                style={{ width: `${Math.min(progress * 100, 100)}%` }}
              />
            </div>
          </div>
        )}

        {/* Timestamp and actions */}
        <div className="mt-4 flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            {formatDistanceToNow(new Date(approval.created_at), { addSuffix: true })}
          </span>
          {isPending && (
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={onReject}>
                <XCircle className="h-4 w-4 mr-1" />
                Reject
              </Button>
              <Button size="sm" onClick={onApprove}>
                <CheckCircle2 className="h-4 w-4 mr-1" />
                Approve
              </Button>
            </div>
          )}
        </div>

        {/* Timeout warning */}
        {isPending && approval.timeout_at && (
          <div className="mt-3 flex items-center gap-2 text-xs text-amber-600">
            <Clock className="h-3 w-3" />
            <span>
              Expires {formatDistanceToNow(new Date(approval.timeout_at), { addSuffix: true })}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ==================== Stats Card ====================

interface StatCardProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  color: string;
}

function StatCard({ label, value, icon, color }: StatCardProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center gap-4">
          <div className={`flex h-12 w-12 items-center justify-center rounded-full ${color}`}>
            {icon}
          </div>
          <div>
            <p className="text-2xl font-bold">{value}</p>
            <p className="text-sm text-muted-foreground">{label}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ==================== Response Dialog ====================

interface ResponseDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  approvalId: string | null;
  action: "approve" | "reject";
  onConfirm: (comment: string) => void;
  isLoading: boolean;
}

function ResponseDialog({
  open,
  onOpenChange,
  action,
  onConfirm,
  isLoading,
}: ResponseDialogProps) {
  const [comment, setComment] = useState("");

  const handleConfirm = () => {
    onConfirm(comment);
    setComment("");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {action === "approve" ? "Approve Request" : "Reject Request"}
          </DialogTitle>
          <DialogDescription>
            {action === "approve"
              ? "The workflow will continue after your approval."
              : "The workflow will be stopped or take an alternate path."}
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <label className="text-sm font-medium mb-2 block">
            <MessageSquare className="h-4 w-4 inline mr-2" />
            Comment (optional)
          </label>
          <Textarea
            placeholder="Add a note explaining your decision..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={3}
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            variant={action === "approve" ? "default" : "destructive"}
            onClick={handleConfirm}
            disabled={isLoading}
          >
            {isLoading ? (
              "Processing..."
            ) : action === "approve" ? (
              <>
                <CheckCircle2 className="h-4 w-4 mr-1" />
                Approve
              </>
            ) : (
              <>
                <XCircle className="h-4 w-4 mr-1" />
                Reject
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ==================== Main Page ====================

export default function ApprovalsPage() {
  const [statusFilter, setStatusFilter] = useState<ApprovalStatus | "all">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedApproval, setSelectedApproval] = useState<string | null>(null);
  const [dialogAction, setDialogAction] = useState<"approve" | "reject">("approve");

  // Fetch data
  const { data, isLoading, error } = useApprovals({
    status: statusFilter === "all" ? undefined : statusFilter,
  });
  const { data: stats, isLoading: statsLoading } = useApprovalStats();
  const respondMutation = useRespondToApproval();

  // Handlers
  const handleApprove = (approvalId: string) => {
    setSelectedApproval(approvalId);
    setDialogAction("approve");
    setDialogOpen(true);
  };

  const handleReject = (approvalId: string) => {
    setSelectedApproval(approvalId);
    setDialogAction("reject");
    setDialogOpen(true);
  };

  const handleConfirm = (comment: string) => {
    if (!selectedApproval) return;

    respondMutation.mutate(
      {
        approvalId: selectedApproval,
        request: {
          decision: dialogAction,
          comment: comment || undefined,
        },
      },
      {
        onSuccess: () => {
          setDialogOpen(false);
          setSelectedApproval(null);
        },
      }
    );
  };

  // Filter approvals by search
  const filteredApprovals = data?.approvals.filter((approval) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      approval.title.toLowerCase().includes(query) ||
      approval.message.toLowerCase().includes(query) ||
      approval.workflow_name?.toLowerCase().includes(query) ||
      approval.workflow_id.toLowerCase().includes(query)
    );
  });

  return (
    <>
      <Header />
      <PageContainer>
        <PageHeader
          title="Approvals"
          description="Review and respond to workflow approval requests"
        />

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-4 mb-6">
          {statsLoading ? (
            <>
              <StatCardSkeleton />
              <StatCardSkeleton />
              <StatCardSkeleton />
              <StatCardSkeleton />
            </>
          ) : stats ? (
            <>
              <StatCard
                label="Pending"
                value={stats.pending_count}
                icon={<Clock className="h-6 w-6 text-amber-600" />}
                color="bg-amber-500/10"
              />
              <StatCard
                label="Approved"
                value={stats.approved_count}
                icon={<CheckCircle2 className="h-6 w-6 text-green-600" />}
                color="bg-green-500/10"
              />
              <StatCard
                label="Rejected"
                value={stats.rejected_count}
                icon={<XCircle className="h-6 w-6 text-red-600" />}
                color="bg-red-500/10"
              />
              <StatCard
                label="Expired"
                value={stats.expired_count}
                icon={<AlertTriangle className="h-6 w-6 text-gray-600" />}
                color="bg-gray-500/10"
              />
            </>
          ) : null}
        </div>

        {/* Filters */}
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search approvals..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="flex gap-2">
            <Select
              value={statusFilter}
              onValueChange={(value) => setStatusFilter(value as ApprovalStatus | "all")}
            >
              <SelectTrigger className="w-[160px]">
                <Filter className="mr-2 h-4 w-4" />
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
                <SelectItem value="expired">Expired</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <ApprovalCardSkeleton key={i} />
            ))}
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-destructive">
            Failed to load approvals: {error.message}
          </div>
        )}

        {/* Empty State */}
        {data && filteredApprovals?.length === 0 && !searchQuery && statusFilter === "all" && (
          <EmptyState />
        )}

        {/* No Results */}
        {data && filteredApprovals?.length === 0 && (searchQuery || statusFilter !== "all") && (
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card/50 py-12">
            <Search className="h-12 w-12 text-muted-foreground/50" />
            <h3 className="mt-4 text-lg font-semibold">No approvals found</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Try adjusting your search or filters
            </p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => {
                setSearchQuery("");
                setStatusFilter("all");
              }}
            >
              Clear filters
            </Button>
          </div>
        )}

        {/* Approval Cards */}
        {data && filteredApprovals && filteredApprovals.length > 0 && (
          <>
            <div className="mb-4 text-sm text-muted-foreground">
              {filteredApprovals.length} approval{filteredApprovals.length !== 1 ? "s" : ""}
              {data.pending_count > 0 && (
                <span className="ml-2 text-amber-600">
                  ({data.pending_count} pending)
                </span>
              )}
            </div>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredApprovals.map((approval) => (
                <ApprovalCard
                  key={approval.id}
                  approval={approval}
                  onApprove={() => handleApprove(approval.id)}
                  onReject={() => handleReject(approval.id)}
                />
              ))}
            </div>
          </>
        )}

        {/* Response Dialog */}
        <ResponseDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          approvalId={selectedApproval}
          action={dialogAction}
          onConfirm={handleConfirm}
          isLoading={respondMutation.isPending}
        />
      </PageContainer>
    </>
  );
}
