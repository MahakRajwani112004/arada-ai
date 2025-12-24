"use client";

import { useState } from "react";
import { Play, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

interface RunWorkflowPanelProps {
  workflowId: string;
  isBlocked?: boolean;
  isExecuting?: boolean;
  onRun: (userInput: string, context?: Record<string, unknown>) => void;
}

export function RunWorkflowPanel({
  isBlocked = false,
  isExecuting = false,
  onRun,
}: RunWorkflowPanelProps) {
  const [userInput, setUserInput] = useState("");

  const handleRun = () => {
    onRun(userInput);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Run Workflow</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="user-input">User Input</Label>
          <Textarea
            id="user-input"
            placeholder="Enter input for the workflow..."
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            disabled={isBlocked || isExecuting}
            className="min-h-[80px] resize-none"
          />
        </div>
        <Button
          onClick={handleRun}
          disabled={isBlocked || isExecuting}
          className="w-full gap-2"
        >
          {isExecuting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Running...
            </>
          ) : (
            <>
              <Play className="h-4 w-4" />
              Start Execution
            </>
          )}
        </Button>
        {isBlocked && (
          <p className="text-xs text-amber-400 text-center">
            Create missing agents to run this workflow
          </p>
        )}
      </CardContent>
    </Card>
  );
}
