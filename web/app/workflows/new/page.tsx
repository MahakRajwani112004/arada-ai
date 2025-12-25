"use client";

import { ArrowLeft, Sparkles, Wrench, ArrowRight, Check } from "lucide-react";
import Link from "next/link";
import { Header } from "@/components/layout/header";
import { PageContainer } from "@/components/layout/page-container";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const options = [
  {
    id: "ai",
    title: "AI Generate",
    icon: Sparkles,
    description: "Describe what you want in plain English and let AI build it for you",
    benefits: [
      "Fast (under 30 seconds)",
      "Smart agent selection",
      "Fully customizable after",
    ],
    href: "/workflows/create",
    recommended: true,
    gradient: "from-purple-500/20 to-blue-500/20",
    iconColor: "text-purple-400",
  },
  {
    id: "manual",
    title: "Build Manually",
    icon: Wrench,
    description: "Full control over every step and configuration",
    benefits: [
      "Complete control",
      "Step-by-step guide",
      "Advanced options",
    ],
    href: "/workflows/new/manual",
    recommended: false,
    gradient: "from-gray-500/20 to-gray-600/20",
    iconColor: "text-gray-400",
  },
];

export default function NewWorkflowPage() {
  return (
    <>
      <Header />
      <PageContainer>
        <div className="mx-auto max-w-3xl">
          <Link
            href="/workflows"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Workflows
          </Link>

          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold">Create a New Workflow</h1>
            <p className="mt-2 text-muted-foreground">
              Choose how you&apos;d like to create your workflow
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {options.map((option) => {
              const Icon = option.icon;

              return (
                <Link key={option.id} href={option.href}>
                  <Card className="h-full cursor-pointer transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5 group relative overflow-hidden">
                    {option.recommended && (
                      <div className="absolute top-3 right-3">
                        <Badge className="bg-primary/90">Recommended</Badge>
                      </div>
                    )}
                    <CardHeader>
                      <div
                        className={`flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br ${option.gradient}`}
                      >
                        <Icon className={`h-6 w-6 ${option.iconColor}`} />
                      </div>
                      <CardTitle className="mt-4">{option.title}</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <p className="text-sm text-muted-foreground">
                        {option.description}
                      </p>

                      <ul className="space-y-2">
                        {option.benefits.map((benefit, index) => (
                          <li
                            key={index}
                            className="flex items-center gap-2 text-sm text-muted-foreground"
                          >
                            <Check className="h-4 w-4 text-green-400" />
                            {benefit}
                          </li>
                        ))}
                      </ul>

                      <div className="flex items-center gap-2 text-sm font-medium text-primary group-hover:gap-3 transition-all">
                        Get Started
                        <ArrowRight className="h-4 w-4" />
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        </div>
      </PageContainer>
    </>
  );
}
