"use client";

import { memo, useState, useCallback, useRef, useEffect } from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  useReactFlow,
  type EdgeProps,
} from "@xyflow/react";
import { Pencil } from "lucide-react";
import { useCanvasContext } from "../canvas-context";

interface LabeledEdgeData {
  label?: string;
  animated?: boolean;
}

function LabeledEdgeComponent({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  data,
  selected,
}: EdgeProps) {
  const { setEdges } = useReactFlow();
  const { markUnsaved } = useCanvasContext();
  const [isEditing, setIsEditing] = useState(false);
  const [labelValue, setLabelValue] = useState((data as LabeledEdgeData)?.label || "");
  const inputRef = useRef<HTMLInputElement>(null);

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleDoubleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setIsEditing(true);
  }, []);

  const handleSave = useCallback(() => {
    setEdges((edges) =>
      edges.map((edge) => {
        if (edge.id === id) {
          return {
            ...edge,
            data: {
              ...edge.data,
              label: labelValue.trim() || undefined,
            },
          };
        }
        return edge;
      })
    );
    setIsEditing(false);
    markUnsaved();
  }, [id, labelValue, setEdges, markUnsaved]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        handleSave();
      } else if (e.key === "Escape") {
        setLabelValue((data as LabeledEdgeData)?.label || "");
        setIsEditing(false);
      }
    },
    [handleSave, data]
  );

  const handleBlur = useCallback(() => {
    handleSave();
  }, [handleSave]);

  const label = (data as LabeledEdgeData)?.label;
  const hasLabel = label && label.trim().length > 0;

  return (
    <>
      <BaseEdge
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          strokeWidth: selected ? 2.5 : 1.5,
          stroke: selected ? "hsl(var(--primary))" : "hsl(var(--muted-foreground) / 0.4)",
        }}
      />
      <EdgeLabelRenderer>
        <div
          style={{
            position: "absolute",
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: "all",
          }}
          className="nodrag nopan"
        >
          {isEditing ? (
            <input
              ref={inputRef}
              value={labelValue}
              onChange={(e) => setLabelValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onBlur={handleBlur}
              className="px-2 py-1 text-xs rounded border border-primary bg-background shadow-sm focus:outline-none focus:ring-1 focus:ring-primary min-w-[60px]"
              placeholder="Label..."
            />
          ) : (
            <div
              onDoubleClick={handleDoubleClick}
              className={`
                group flex items-center gap-1 px-2 py-0.5 rounded text-xs cursor-pointer transition-colors
                ${hasLabel
                  ? "bg-card border border-border hover:border-muted-foreground"
                  : "bg-transparent hover:bg-muted"
                }
                ${selected ? "ring-1 ring-primary" : ""}
              `}
              title="Double-click to edit"
            >
              {hasLabel ? (
                <span className="text-muted-foreground">{label}</span>
              ) : (
                <span className="text-muted-foreground/50 opacity-0 group-hover:opacity-100 flex items-center gap-1">
                  <Pencil className="h-2.5 w-2.5" />
                  <span>Label</span>
                </span>
              )}
            </div>
          )}
        </div>
      </EdgeLabelRenderer>
    </>
  );
}

export const LabeledEdge = memo(LabeledEdgeComponent);
