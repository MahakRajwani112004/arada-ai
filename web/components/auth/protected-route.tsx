"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, fetchUser, accessToken, hasHydrated } = useAuth();

  // Debug logging
  console.log("[ProtectedRoute] Rendering for path:", pathname, { hasHydrated, isAuthenticated, hasToken: !!accessToken });

  useEffect(() => {
    // If we have a token but no user, try to fetch user info
    if (hasHydrated && accessToken && !isLoading) {
      fetchUser();
    }
  }, [hasHydrated, accessToken, isLoading, fetchUser]);

  useEffect(() => {
    // Only redirect if we're sure the user is not authenticated AND hydration is complete
    if (hasHydrated && !isLoading && !isAuthenticated && !accessToken) {
      console.log("[ProtectedRoute] Redirecting to login from:", pathname);
      router.push(`/login?redirect=${encodeURIComponent(pathname)}`);
    }
  }, [hasHydrated, isAuthenticated, isLoading, accessToken, router, pathname]);

  // Show loading state while hydrating or checking auth
  if (!hasHydrated || isLoading || (!isAuthenticated && accessToken)) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // If not authenticated and no token, don't render (will redirect)
  if (!isAuthenticated && !accessToken) {
    return null;
  }

  return <>{children}</>;
}
