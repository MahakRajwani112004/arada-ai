"use client";

import { motion } from "framer-motion";
import { CheckCircle, XCircle, Clock, RotateCcw, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ExecutionStatus } from "@/types/workflow";

interface ExecutionCompleteProps {
  status: ExecutionStatus;
  durationMs?: number;
  onRunAgain?: () => void;
  onViewDetails?: () => void;
}

function formatDuration(ms: number | undefined): string {
  if (ms === undefined) return "";
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;
}

export function ExecutionComplete({
  status,
  durationMs,
  onRunAgain,
  onViewDetails,
}: ExecutionCompleteProps) {
  const isSuccess = status === "COMPLETED";
  const isFailed = status === "FAILED";

  return (
    <div className="flex flex-col items-center text-center py-8 space-y-4">
      {isSuccess && (
        <>
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 200, damping: 15 }}
          >
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-500/20">
              <CheckCircle className="h-8 w-8 text-green-400" />
            </div>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h3 className="text-lg font-semibold text-green-400">
              Workflow Complete!
            </h3>
            <p className="text-muted-foreground mt-1">
              That was fast!
            </p>
          </motion.div>
        </>
      )}

      {isFailed && (
        <>
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-500/20">
            <XCircle className="h-8 w-8 text-red-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-red-400">
              Workflow Failed
            </h3>
            <p className="text-muted-foreground mt-1">
              Something went wrong. Check the step details for more info.
            </p>
          </div>
        </>
      )}

      {durationMs !== undefined && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Clock className="h-4 w-4" />
          <span>Total time: {formatDuration(durationMs)}</span>
        </div>
      )}

      <div className="flex gap-3 pt-4">
        {onRunAgain && (
          <Button variant="outline" onClick={onRunAgain} className="gap-2">
            <RotateCcw className="h-4 w-4" />
            Run Again
          </Button>
        )}
        {onViewDetails && (
          <Button onClick={onViewDetails} className="gap-2">
            <ExternalLink className="h-4 w-4" />
            View Details
          </Button>
        )}
      </div>
    </div>
  );
}
