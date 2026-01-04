"use client";

import { useState, useEffect } from "react";

/**
 * Hook that returns whether a media query matches.
 *
 * @param query - CSS media query string (e.g., "(max-width: 768px)")
 * @returns Whether the media query matches
 *
 * @example
 * ```tsx
 * function Component() {
 *   const isMobile = useMediaQuery("(max-width: 768px)");
 *   return isMobile ? <MobileView /> : <DesktopView />;
 * }
 * ```
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    // Check if window is available (SSR safety)
    if (typeof window === "undefined") {
      return;
    }

    const mediaQuery = window.matchMedia(query);

    // Set initial value
    setMatches(mediaQuery.matches);

    // Create handler
    const handler = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    // Add listener
    mediaQuery.addEventListener("change", handler);

    // Cleanup
    return () => {
      mediaQuery.removeEventListener("change", handler);
    };
  }, [query]);

  return matches;
}
