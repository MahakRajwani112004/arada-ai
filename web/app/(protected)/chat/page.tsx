"use client";

import { Header } from "@/components/layout/header";
import { ChatLayout } from "@/components/chat/chat-layout";

export default function ChatPage() {
  return (
    <div className="flex flex-col h-screen">
      <Header />
      <main className="flex-1 overflow-hidden">
        <ChatLayout className="h-full" />
      </main>
    </div>
  );
}
