# Arada POC - UI Integration Guide

This guide explains how to integrate the Arada POC agents with your UI.

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR UI (Next.js)                        │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Chat Input  │───>│  useChat()   │───>│  API Client  │      │
│  └──────────────┘    │    Hook      │    └──────────────┘      │
│         │            └──────────────┘           │               │
│         v                   │                   v               │
│  ┌──────────────┐           │         POST /conversations/     │
│  │ Chat Messages│<──────────┘              {id}/stream         │
│  └──────────────┘                           (SSE)              │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                            │
│                                                                 │
│  POST /conversations/{id}/stream                                │
│         │                                                       │
│         ▼                                                       │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              StreamingExecutor                             │ │
│  │  1. Save user message                                      │ │
│  │  2. Emit SSE events (thinking, retrieving, generating...)  │ │
│  │  3. Execute AgentWorkflow via Temporal                     │ │
│  │  4. Stream response chunks back                            │ │
│  └───────────────────────────────────────────────────────────┘ │
│                           │                                     │
│                           ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Analytics Orchestrator                        │ │
│  │         (arada_analytics_orchestrator)                     │ │
│  │                                                            │ │
│  │  Routes to:                                                │ │
│  │  ├── arada_descriptive_agent (KPIs, trends)                │ │
│  │  ├── arada_deepdive_agent (drill-down)                     │ │
│  │  ├── arada_decomposition_agent (waterfall)                 │ │
│  │  └── arada_whatif_agent (scenarios)                        │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Step-by-Step Setup

### Step 1: Register the Agents

```bash
# From project root
python scripts/register_arada_agents.py register
```

This registers all 5 agents:
- `arada_analytics_orchestrator` (master)
- `arada_descriptive_agent`
- `arada_deepdive_agent`
- `arada_decomposition_agent`
- `arada_whatif_agent`

### Step 2: Verify Agents are Registered

```bash
# List all agents
python scripts/register_arada_agents.py list

# Or via API
curl http://localhost:8000/api/v1/agents
```

---

## 3. UI Integration Patterns

### Option A: Use the Orchestrator (Recommended)

The orchestrator automatically routes queries to the right specialist agent.

```typescript
// web/app/(protected)/arada/page.tsx

"use client";

import { useState } from "react";
import { ChatLayout } from "@/components/chat/chat-layout";

// The orchestrator agent ID
const ARADA_ORCHESTRATOR_ID = "arada_analytics_orchestrator";

export default function AradaAnalyticsPage() {
  return (
    <ChatLayout
      agentId={ARADA_ORCHESTRATOR_ID}
      title="Arada Analytics"
      placeholder="Ask about KPIs, trends, or run what-if scenarios..."
    />
  );
}
```

**User asks:** "What is the trend of net sales in 2024?"
**Orchestrator routes to:** `arada_descriptive_agent`
**Response:** Chart + insights about net sales trend

**User follows up:** "Break it down by region"
**Orchestrator routes to:** `arada_deepdive_agent`
**Response:** Regional breakdown with drill-down options

---

### Option B: Direct Agent Selection (Tab-based UI)

Let users pick a specific analysis type:

```typescript
// web/app/(protected)/arada/page.tsx

"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChatLayout } from "@/components/chat/chat-layout";

const AGENTS = {
  descriptive: {
    id: "arada_descriptive_agent",
    label: "KPIs & Trends",
    placeholder: "Ask about KPIs, trends, comparisons...",
  },
  deepdive: {
    id: "arada_deepdive_agent",
    label: "Deep Dive",
    placeholder: "Drill into regions, projects, segments...",
  },
  decomposition: {
    id: "arada_decomposition_agent",
    label: "Decomposition",
    placeholder: "Break down changes, waterfall analysis...",
  },
  whatif: {
    id: "arada_whatif_agent",
    label: "What-If",
    placeholder: "Run scenarios, simulate impacts...",
  },
};

export default function AradaAnalyticsPage() {
  const [activeAgent, setActiveAgent] = useState("descriptive");

  return (
    <div className="h-full flex flex-col">
      <Tabs value={activeAgent} onValueChange={setActiveAgent}>
        <TabsList className="grid grid-cols-4">
          {Object.entries(AGENTS).map(([key, agent]) => (
            <TabsTrigger key={key} value={key}>
              {agent.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {Object.entries(AGENTS).map(([key, agent]) => (
          <TabsContent key={key} value={key} className="flex-1">
            <ChatLayout
              agentId={agent.id}
              title={agent.label}
              placeholder={agent.placeholder}
            />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
```

---

## 4. API Endpoints to Use

### Create Conversation

```typescript
// POST /api/v1/agents/{agent_id}/conversations
const response = await fetch(
  `${API_URL}/api/v1/agents/${ARADA_ORCHESTRATOR_ID}/conversations`,
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      title: "Arada Analytics Session",
    }),
  }
);

const { id: conversationId } = await response.json();
```

### Send Message (Streaming)

```typescript
// POST /api/v1/conversations/{conversation_id}/stream
// Returns Server-Sent Events (SSE)

const eventSource = new EventSource(
  `${API_URL}/api/v1/conversations/${conversationId}/stream`,
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      content: "What is the trend of net sales in 2024?",
    }),
  }
);

// Or use fetch with ReadableStream
const response = await fetch(
  `${API_URL}/api/v1/conversations/${conversationId}/stream`,
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      content: "What is the trend of net sales in 2024?",
    }),
  }
);

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const text = decoder.decode(value);
  // Parse SSE events
  const events = text.split("\n\n").filter(Boolean);
  for (const event of events) {
    if (event.startsWith("data: ")) {
      const data = JSON.parse(event.slice(6));
      handleStreamEvent(data);
    }
  }
}
```

### Stream Event Types

```typescript
type StreamEventType =
  | "thinking"         // Agent is processing
  | "retrieving"       // Fetching from knowledge base
  | "retrieved"        // KB results received
  | "tool_start"       // Tool execution starting
  | "tool_end"         // Tool execution complete
  | "generating"       // LLM generating response
  | "chunk"            // Response text chunk
  | "complete"         // Execution complete
  | "error"            // Error occurred
  | "message_saved";   // Message persisted

interface StreamEvent {
  type: StreamEventType;
  data: {
    content?: string;        // For chunk events
    step?: string;           // For thinking events
    tool_name?: string;      // For tool events
    message_id?: string;     // For complete/saved events
    error?: string;          // For error events
  };
}
```

---

## 5. Using the Existing Hooks

Your codebase already has hooks for streaming chat:

```typescript
// web/lib/hooks/use-conversations.ts

import { useStreamingChat } from "@/lib/hooks/use-conversations";

function AradaChat({ conversationId }: { conversationId: string }) {
  const {
    messages,
    streamingState,
    sendMessage,
    cancelStreaming,
  } = useStreamingChat(conversationId);

  const handleSend = async (content: string) => {
    await sendMessage(content);
  };

  return (
    <div>
      {/* Messages */}
      {messages.map((msg) => (
        <Message key={msg.id} message={msg} />
      ))}

      {/* Streaming indicator */}
      {streamingState.status !== "idle" && (
        <StreamingIndicator state={streamingState} />
      )}

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={streamingState.status !== "idle"} />
    </div>
  );
}
```

---

## 6. Handling Visualizations

The agents return charts in two formats:

### ASCII Chart (in response text)

```
Net Sales by Quarter
████████████████████  Q4: 140M
███████████████       Q2: 120M
██████████████        Q3: 115M
████████████          Q1: 100M
```

### Chart Config (in metadata)

```typescript
interface ChartConfig {
  type: "bar" | "line" | "pie" | "horizontal_bar" | "area" | "scatter";
  data: {
    labels: string[];
    datasets: Array<{
      label: string;
      data: number[];
      backgroundColor?: string[];
    }>;
  };
  options: {
    responsive: boolean;
    plugins: {
      title: { text: string };
      legend: { display: boolean };
    };
  };
}
```

### Rendering Charts

```typescript
// components/chart-renderer.tsx

import { Bar, Line, Pie } from "react-chartjs-2";

interface ChartRendererProps {
  config: ChartConfig;
}

export function ChartRenderer({ config }: ChartRendererProps) {
  switch (config.type) {
    case "bar":
      return <Bar data={config.data} options={config.options} />;
    case "line":
      return <Line data={config.data} options={config.options} />;
    case "pie":
      return <Pie data={config.data} options={config.options} />;
    // ... other types
  }
}

// In message component
function Message({ message }) {
  const chartConfig = message.metadata?.chart_config;

  return (
    <div>
      <Markdown>{message.content}</Markdown>
      {chartConfig && <ChartRenderer config={chartConfig} />}
    </div>
  );
}
```

---

## 7. Pre-Identified Insights Widget

Display insights at the top of the chat:

```typescript
// components/insights-widget.tsx

interface Insight {
  id: string;
  type: "warning" | "info" | "success";
  message: string;
  kpi: string;
  created_at: string;
}

async function fetchInsights(): Promise<Insight[]> {
  const response = await fetch("/api/v1/insights?limit=5");
  return response.json();
}

export function InsightsWidget() {
  const [insights, setInsights] = useState<Insight[]>([]);

  useEffect(() => {
    fetchInsights().then(setInsights);
    // Refresh every 5 minutes
    const interval = setInterval(() => fetchInsights().then(setInsights), 300000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-muted p-4 rounded-lg mb-4">
      <h3 className="font-semibold mb-2">Pre-Identified Insights</h3>
      <ul className="space-y-2">
        {insights.map((insight) => (
          <li
            key={insight.id}
            className={cn(
              "flex items-start gap-2 text-sm",
              insight.type === "warning" && "text-yellow-600",
              insight.type === "info" && "text-blue-600",
              insight.type === "success" && "text-green-600"
            )}
          >
            <AlertIcon type={insight.type} />
            <span>{insight.message}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## 8. Complete Page Example

```typescript
// web/app/(protected)/arada/page.tsx

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { InsightsWidget } from "@/components/insights-widget";
import { ChatArea } from "@/components/chat/chat-area";
import { ChatInput } from "@/components/chat/chat-input";
import { useStreamingChat } from "@/lib/hooks/use-conversations";
import { createConversation } from "@/lib/api/conversations";

const ORCHESTRATOR_ID = "arada_analytics_orchestrator";

export default function AradaAnalyticsPage() {
  const router = useRouter();
  const [conversationId, setConversationId] = useState<string | null>(null);

  // Create conversation on mount
  useEffect(() => {
    createConversation(ORCHESTRATOR_ID, "Arada Analytics").then((conv) => {
      setConversationId(conv.id);
    });
  }, []);

  if (!conversationId) {
    return <div>Loading...</div>;
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <header className="border-b p-4">
        <h1 className="text-xl font-bold">Arada Analytics</h1>
        <p className="text-muted-foreground">
          Ask about KPIs, trends, drill-downs, or run what-if scenarios
        </p>
      </header>

      {/* Pre-identified insights */}
      <InsightsWidget />

      {/* Chat area */}
      <div className="flex-1 overflow-hidden">
        <AradaChatArea conversationId={conversationId} />
      </div>
    </div>
  );
}

function AradaChatArea({ conversationId }: { conversationId: string }) {
  const {
    messages,
    streamingState,
    sendMessage,
  } = useStreamingChat(conversationId);

  return (
    <div className="h-full flex flex-col">
      {/* Messages */}
      <div className="flex-1 overflow-auto p-4">
        {messages.length === 0 && (
          <div className="text-center text-muted-foreground mt-8">
            <p>Try asking:</p>
            <ul className="mt-2 space-y-1">
              <li>"What is the trend of net sales in 2024?"</li>
              <li>"Show me cancellation rate by region"</li>
              <li>"What if we increase prices by 5%?"</li>
            </ul>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {streamingState.status !== "idle" && (
          <StreamingIndicator state={streamingState} />
        )}
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <ChatInput
          onSend={sendMessage}
          disabled={streamingState.status !== "idle"}
          placeholder="Ask about Arada analytics..."
        />
      </div>
    </div>
  );
}
```

---

## 9. Conversation Flow Example

```
┌─────────────────────────────────────────────────────────────────┐
│ Pre-Identified Insights                                         │
│ ⚠ Cancellation rate in Dubai increased 12% this month          │
│ ℹ Net Sales exceeded target by 8% in Q4                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ USER: What is the trend of net sales in 2024?                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    [Orchestrator routes to]
                    [arada_descriptive_agent]
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ ASSISTANT:                                                      │
│                                                                 │
│ ## Net Sales Trend - 2024                                       │
│                                                                 │
│ [LINE CHART: Monthly Net Sales]                                 │
│                                                                 │
│ **Key Insights:**                                               │
│ - Total 2024: 568M AED (+18% YoY)                               │
│ - Q4 strongest at 165M AED                                      │
│ - Q3 dip recovered in Q4                                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ USER: Break it down by region                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    [Orchestrator routes to]
                    [arada_deepdive_agent]
                    [With context: kpi=net_sales, year=2024]
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ ASSISTANT:                                                      │
│                                                                 │
│ ## Net Sales by Region - 2024                                   │
│ **Context:** Net Sales | 2024                                   │
│                                                                 │
│ [BAR CHART: Regional Breakdown]                                 │
│                                                                 │
│ | Region    | Sales   | Share |                                 │
│ |-----------|---------|-------|                                 │
│ | Dubai     | 280M    | 49%   |                                 │
│ | Abu Dhabi | 168M    | 30%   |                                 │
│ | Sharjah   | 85M     | 15%   |                                 │
│ | RAK       | 35M     | 6%    |                                 │
│                                                                 │
│ **Drill-down options:**                                         │
│ - "Drill into Dubai" → Project breakdown                        │
│ - "Why is Sharjah low?" → Root cause analysis                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ USER: What if we increase Dubai prices by 5%?                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    [Orchestrator routes to]
                    [arada_whatif_agent]
                    [With context: region=Dubai, base=280M]
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ ASSISTANT:                                                      │
│                                                                 │
│ ## Scenario: 5% Price Increase in Dubai                         │
│                                                                 │
│ **Baseline:** Dubai Net Sales = 280M AED                        │
│                                                                 │
│ | Scenario | Impact    | Probability |                         │
│ |----------|-----------|-------------|                         │
│ | Best     | +8% (302M)| 25%         |                         │
│ | Expected | +2% (286M)| 50%         |                         │
│ | Worst    | -4% (269M)| 25%         |                         │
│                                                                 │
│ **Confidence:** 74%                                             │
│ **Assumptions:** Price elasticity -0.6, stable market           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Summary

| Step | What to Do |
|------|------------|
| 1 | Run `python scripts/register_arada_agents.py` to register agents |
| 2 | Create a chat page using `arada_analytics_orchestrator` |
| 3 | Use `useStreamingChat` hook for real-time responses |
| 4 | Handle chart rendering from response metadata |
| 5 | Add insights widget for pre-identified insights |

The orchestrator handles routing automatically - users just chat naturally and get routed to the right specialist agent based on their query.

---

## Next Steps

1. **Add insights endpoint** - Create `/api/v1/insights` for pre-computed insights
2. **Enhance chart types** - Add waterfall, bridge charts for decomposition
3. **Add data source** - Connect agents to actual Arada data
4. **Customize UI** - Add Arada branding and styling
