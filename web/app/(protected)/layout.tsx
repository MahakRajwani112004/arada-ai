"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { ProtectedRoute } from "@/components/auth/protected-route";

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="ml-56 flex flex-1 flex-col">{children}</div>
      </div>
    </ProtectedRoute>
  );
}
