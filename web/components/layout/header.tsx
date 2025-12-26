"use client";

import { Search } from "lucide-react";
import { useEffect, useState } from "react";

interface HeaderProps {
  onSearchClick?: () => void;
}

export function Header({ onSearchClick }: HeaderProps) {
  const [isMac, setIsMac] = useState(true);

  useEffect(() => {
    setIsMac(navigator.platform.toUpperCase().indexOf("MAC") >= 0);
  }, []);

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center border-b border-border bg-background/95 px-6 backdrop-blur supports-[backdrop-filter]:bg-background/60">
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
    </header>
  );
}
