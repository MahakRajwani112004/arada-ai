"use client";

import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { PageContainer } from "@/components/layout/page-container";
import { AgentForm } from "@/components/agents/agent-form";

export default function NewAgentPage() {
  const router = useRouter();

  return (
    <PageContainer>
      <div className="flex items-center gap-3 mb-6">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-xl font-semibold">Create Agent</h1>
      </div>
      <AgentForm />
    </PageContainer>
  );
}
