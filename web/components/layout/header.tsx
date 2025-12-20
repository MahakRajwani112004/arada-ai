"use client";

import { Search, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

interface HeaderProps {
  onSearchClick?: () => void;
}

export function Header({ onSearchClick }: HeaderProps) {
  const router = useRouter();
  const [isMac, setIsMac] = useState(true);

  useEffect(() => {
    setIsMac(navigator.platform.toUpperCase().indexOf("MAC") >= 0);
  }, []);

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border bg-background/95 px-6 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      {/* Search */}
      <button
        onClick={onSearchClick}
        className="flex h-9 w-72 items-center gap-2 rounded-md border border-border bg-secondary/50 px-3 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        <Search className="h-4 w-4" />
        <span>Search agents, tools...</span>
        <kbd className="ml-auto hidden rounded bg-muted px-1.5 py-0.5 text-xs font-medium sm:inline-block">
          {isMac ? "⌘" : "Ctrl"}K
        </kbd>
      </button>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <Button
          onClick={() => router.push("/agents/new")}
          size="sm"
          className="gap-1.5"
        >
          <Plus className="h-4 w-4" />
          Create Agent
        </Button>
      </div>
    </header>
  );
}
