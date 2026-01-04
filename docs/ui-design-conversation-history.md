# Conversation History UI Design Specification

## Overview

This document outlines the UI design for adding conversation session management to the AI Agent Chat interface. The design maintains consistency with existing shadcn/ui components while introducing a sidebar pattern for session navigation.

---

## Component Hierarchy

```
AgentChatWithHistory/
├── ConversationSidebar/           # Desktop: persistent, Mobile: Sheet
│   ├── SidebarHeader/
│   │   ├── Title ("Conversations")
│   │   └── NewChatButton
│   ├── SessionList/
│   │   ├── SessionListSkeleton     # Loading state
│   │   ├── SessionListEmpty        # Empty state
│   │   └── SessionItem[]           # Session cards
│   │       ├── SessionItemContent
│   │       │   ├── Title
│   │       │   ├── Preview snippet
│   │       │   └── Timestamp
│   │       └── SessionItemActions  # Dropdown menu
│   │           ├── Rename
│   │           └── Delete
│   └── SidebarFooter (optional)
├── ChatPanel/
│   ├── ChatHeader (mobile only)
│   │   └── SidebarToggle
│   ├── MessageArea (existing)
│   └── InputArea (existing)
└── RenameDialog/                   # Modal for renaming
    └── Form with Input
```

---

## Layout Specifications

### Desktop Layout (>= 1024px / lg breakpoint)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Chat Tab Content                                                      │
├─────────────────┬────────────────────────────────────────────────────┤
│                 │                                                     │
│  Sidebar        │            Chat Panel                               │
│  w-72 (288px)   │            flex-1                                   │
│                 │                                                     │
│ ┌─────────────┐ │  ┌───────────────────────────────────────────────┐ │
│ │ Convos   [+]│ │  │                                               │ │
│ ├─────────────┤ │  │         Messages Area                         │ │
│ │             │ │  │         h-[600px] - header - input            │ │
│ │ Session 1   │ │  │                                               │ │
│ │ ━━━━━━━━━━━ │ │  │                                               │ │
│ │ Session 2   │ │  │                                               │ │
│ │ ━━━━━━━━━━━ │ │  ├───────────────────────────────────────────────┤ │
│ │ Session 3   │ │  │ Input area                                    │ │
│ │             │ │  └───────────────────────────────────────────────┘ │
│ └─────────────┘ │                                                     │
│                 │                                                     │
└─────────────────┴────────────────────────────────────────────────────┘
```

**Measurements:**
- Total height: 600px (matches existing chat)
- Sidebar width: 288px (w-72)
- Gap between sidebar and chat: 16px (gap-4)
- Sidebar internal padding: 16px (p-4)
- Session item padding: 12px (p-3)

### Tablet Layout (768px - 1023px / md breakpoint)

```
┌────────────────────────────────────────────────────────────────────┐
│ Chat Tab Content                                                    │
├──────────────┬─────────────────────────────────────────────────────┤
│              │                                                      │
│  Sidebar     │            Chat Panel                                │
│  w-64 (256px)│            flex-1                                    │
│  collapsible │                                                      │
│              │                                                      │
└──────────────┴─────────────────────────────────────────────────────┘
```

**Measurements:**
- Sidebar width: 256px (w-64) when expanded
- Collapsed state: 48px (w-12) with icons only
- Toggle button in chat header

### Mobile Layout (< 768px / sm breakpoint)

```
┌──────────────────────────────────────┐
│ Chat Panel (full width)              │
│ ┌──────────────────────────────────┐ │
│ │ [=] Current Chat    [+]          │ │ <- Header with toggle
│ ├──────────────────────────────────┤ │
│ │                                  │ │
│ │       Messages Area              │ │
│ │                                  │ │
│ ├──────────────────────────────────┤ │
│ │ Input area                       │ │
│ └──────────────────────────────────┘ │
└──────────────────────────────────────┘

Sheet (slide from left on toggle):
┌──────────────────────────────────────┐
│ Conversations              [X]       │
├──────────────────────────────────────┤
│ [+ New Chat]                         │
├──────────────────────────────────────┤
│ Session 1                        ... │
│ Session 2                        ... │
│ Session 3                        ... │
└──────────────────────────────────────┘
```

**Measurements:**
- Sheet width: 75vw (max 320px via sm:max-w-sm)
- Header height: 48px (h-12)
- Full available height for messages

---

## Visual Design Specifications

### Color Palette (Dark Theme)

```css
/* Backgrounds */
--sidebar-bg: hsl(var(--card));           /* Same as card bg */
--session-bg: transparent;
--session-hover: hsl(var(--accent));
--session-active: hsl(var(--accent));
--session-active-border: hsl(var(--primary));

/* Text */
--session-title: hsl(var(--foreground));
--session-preview: hsl(var(--muted-foreground));
--session-date: hsl(var(--muted-foreground));

/* Borders */
--sidebar-border: hsl(var(--border));
--session-border: transparent;
--session-active-left-border: hsl(var(--primary));
```

### Session Item States

#### Default State
```tsx
className="
  group
  relative
  flex
  cursor-pointer
  flex-col
  gap-1
  rounded-lg
  border
  border-transparent
  p-3
  transition-all
  duration-150
"
```

#### Hover State
```tsx
className="
  hover:bg-accent
  hover:border-accent
"
```

#### Active/Selected State
```tsx
className="
  bg-accent
  border-l-2
  border-l-primary
  border-y-transparent
  border-r-transparent
"
```

#### Focus State
```tsx
className="
  focus-visible:outline-none
  focus-visible:ring-2
  focus-visible:ring-ring
  focus-visible:ring-offset-2
"
```

### Typography

```tsx
// Session title
<span className="text-sm font-medium text-foreground line-clamp-1">
  {title}
</span>

// Session preview
<span className="text-xs text-muted-foreground line-clamp-2">
  {preview}
</span>

// Session timestamp
<span className="text-[10px] text-muted-foreground">
  {formatRelativeTime(date)}
</span>
```

### Spacing System

```
Sidebar:
├── Padding: p-4 (16px)
├── Header margin-bottom: mb-4 (16px)
├── Session list gap: space-y-1 (4px)
└── Session item padding: p-3 (12px)

Session Item:
├── Title to preview gap: gap-1 (4px)
├── Content to meta gap: gap-2 (8px)
└── Icon size: h-4 w-4 (16px)
```

---

## Component Specifications

### 1. ConversationSidebar

**Props:**
```typescript
interface ConversationSidebarProps {
  sessions: ConversationSession[];
  activeSessionId: string | null;
  isLoading: boolean;
  onSelectSession: (sessionId: string) => void;
  onNewChat: () => void;
  onRenameSession: (sessionId: string, newTitle: string) => void;
  onDeleteSession: (sessionId: string) => void;
}
```

**Desktop Implementation:**
```tsx
<div className="flex h-[600px] w-72 flex-col rounded-lg border border-border bg-card">
  {/* Header */}
  <div className="flex items-center justify-between border-b border-border p-4">
    <h3 className="text-sm font-semibold text-foreground">
      Conversations
    </h3>
    <Button
      variant="ghost"
      size="icon"
      className="h-8 w-8"
      onClick={onNewChat}
    >
      <Plus className="h-4 w-4" />
    </Button>
  </div>

  {/* Session List */}
  <ScrollArea className="flex-1">
    <div className="space-y-1 p-2">
      {/* Sessions render here */}
    </div>
  </ScrollArea>
</div>
```

### 2. SessionItem

**Props:**
```typescript
interface SessionItemProps {
  session: ConversationSession;
  isActive: boolean;
  onSelect: () => void;
  onRename: (newTitle: string) => void;
  onDelete: () => void;
}

interface ConversationSession {
  id: string;
  title: string;
  preview: string;      // First ~50 chars of last message
  messageCount: number;
  createdAt: Date;
  updatedAt: Date;
}
```

**Implementation:**
```tsx
<div
  role="button"
  tabIndex={0}
  onClick={onSelect}
  onKeyDown={(e) => e.key === 'Enter' && onSelect()}
  className={cn(
    "group relative flex cursor-pointer flex-col gap-1 rounded-lg border p-3 transition-all duration-150",
    "hover:bg-accent hover:border-accent",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
    isActive && "bg-accent border-l-2 border-l-primary"
  )}
>
  <div className="flex items-start justify-between gap-2">
    <div className="flex-1 min-w-0">
      <p className="text-sm font-medium text-foreground line-clamp-1">
        {session.title}
      </p>
      <p className="mt-0.5 text-xs text-muted-foreground line-clamp-2">
        {session.preview}
      </p>
    </div>

    {/* Actions - visible on hover */}
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={(e) => e.stopPropagation()}
        >
          <MoreHorizontal className="h-3 w-3" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        <DropdownMenuItem onClick={() => setIsRenaming(true)}>
          <Pencil className="h-4 w-4 mr-2" />
          Rename
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="text-destructive focus:text-destructive"
          onClick={onDelete}
        >
          <Trash2 className="h-4 w-4 mr-2" />
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  </div>

  <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
    <span>{formatRelativeTime(session.updatedAt)}</span>
    <span>-</span>
    <span>{session.messageCount} messages</span>
  </div>
</div>
```

### 3. SessionListSkeleton

```tsx
export function SessionListSkeleton() {
  return (
    <div className="space-y-1 p-2">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="rounded-lg border border-transparent p-3">
          <Skeleton className="h-4 w-3/4 mb-2" />
          <Skeleton className="h-3 w-full mb-1" />
          <Skeleton className="h-3 w-2/3 mb-2" />
          <Skeleton className="h-2 w-1/3" />
        </div>
      ))}
    </div>
  );
}
```

### 4. SessionListEmpty

```tsx
export function SessionListEmpty({ onNewChat }: { onNewChat: () => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center p-6 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-secondary">
        <MessageSquare className="h-6 w-6 text-muted-foreground" />
      </div>
      <p className="mt-4 text-sm font-medium text-foreground">
        No conversations yet
      </p>
      <p className="mt-1 text-xs text-muted-foreground">
        Start a new chat to begin
      </p>
      <Button
        variant="outline"
        size="sm"
        className="mt-4"
        onClick={onNewChat}
      >
        <Plus className="h-4 w-4 mr-2" />
        New Chat
      </Button>
    </div>
  );
}
```

### 5. RenameSessionDialog

```tsx
export function RenameSessionDialog({
  open,
  onOpenChange,
  currentTitle,
  onRename,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentTitle: string;
  onRename: (newTitle: string) => void;
}) {
  const [title, setTitle] = useState(currentTitle);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (title.trim()) {
      onRename(title.trim());
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>Rename Conversation</DialogTitle>
          <DialogDescription>
            Enter a new name for this conversation.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="py-4">
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Conversation name"
              className="w-full"
              autoFocus
            />
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!title.trim()}>
              Save
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
```

### 6. Mobile Sheet Implementation

```tsx
export function MobileConversationSheet({
  open,
  onOpenChange,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
}) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="left" className="w-[280px] p-0">
        <SheetHeader className="border-b border-border p-4">
          <SheetTitle>Conversations</SheetTitle>
        </SheetHeader>
        {children}
      </SheetContent>
    </Sheet>
  );
}
```

---

## Responsive Behavior

### Breakpoint Strategy

| Breakpoint | Width | Sidebar Behavior |
|------------|-------|------------------|
| Mobile     | < 768px | Sheet (left slide) |
| Tablet     | 768px - 1023px | Collapsible sidebar |
| Desktop    | >= 1024px | Persistent sidebar |

### Implementation Pattern

```tsx
export function AgentChatWithHistory({ agentId }: { agentId: string }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isDesktop = useMediaQuery("(min-width: 1024px)");
  const isTablet = useMediaQuery("(min-width: 768px) and (max-width: 1023px)");
  const isMobile = useMediaQuery("(max-width: 767px)");

  return (
    <div className="flex h-[600px] gap-4">
      {/* Desktop: Always visible sidebar */}
      {isDesktop && (
        <ConversationSidebar
          className="hidden lg:flex"
          {...sidebarProps}
        />
      )}

      {/* Tablet: Collapsible sidebar */}
      {isTablet && (
        <CollapsibleSidebar
          collapsed={!sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          {...sidebarProps}
        />
      )}

      {/* Mobile: Sheet */}
      {isMobile && (
        <MobileConversationSheet
          open={sidebarOpen}
          onOpenChange={setSidebarOpen}
        >
          <ConversationSidebar {...sidebarProps} />
        </MobileConversationSheet>
      )}

      {/* Chat Panel */}
      <div className="flex-1">
        {/* Mobile header with toggle */}
        {!isDesktop && (
          <ChatHeader
            onToggleSidebar={() => setSidebarOpen(true)}
            sessionTitle={activeSession?.title}
          />
        )}
        <ChatMessages />
        <ChatInput />
      </div>
    </div>
  );
}
```

---

## Interaction Patterns

### Session Selection
1. Click/tap on session item
2. Active indicator appears (left border highlight)
3. Chat messages update to show selected session
4. URL updates with session ID parameter

### New Chat
1. Click "+" button in sidebar header
2. New session created with auto-generated title
3. New session becomes active
4. Chat area clears, ready for input
5. Title auto-updates after first message

### Rename Session
1. Hover session item to reveal actions menu
2. Click "..." button
3. Select "Rename" from dropdown
4. Dialog opens with current title pre-filled
5. Enter new title and click "Save"
6. Session title updates immediately

### Delete Session
1. Hover session item to reveal actions menu
2. Click "..." button
3. Select "Delete" from dropdown
4. Confirmation dialog appears
5. Click "Delete" to confirm
6. Session removed from list
7. If deleted session was active, select most recent session

### Mobile Interactions
1. Tap hamburger icon in chat header
2. Sheet slides in from left
3. Tap session to select
4. Sheet auto-closes on selection
5. Swipe right to dismiss sheet

---

## Keyboard Navigation

| Key | Action |
|-----|--------|
| Tab | Navigate between sessions |
| Enter | Select focused session |
| Arrow Up/Down | Navigate session list |
| Escape | Close dropdown/dialog |
| Delete | Delete selected session (with confirmation) |

---

## Animation Specifications

### Sidebar Transitions
```css
/* Collapsible sidebar */
transition: width 200ms ease-in-out;

/* Mobile sheet */
data-[state=open]:animate-in
data-[state=closed]:animate-out
data-[state=closed]:slide-out-to-left
data-[state=open]:slide-in-from-left
duration-300 ease-in-out
```

### Session Item Interactions
```css
/* Hover/active background */
transition: background-color 150ms ease, border-color 150ms ease;

/* Actions menu visibility */
transition: opacity 150ms ease;
```

### Active Indicator
```css
/* Left border highlight */
transition: border-color 150ms ease;
```

---

## Accessibility Requirements

### ARIA Labels
```tsx
<aside aria-label="Conversation history">
<button aria-label="Start new conversation">
<button aria-label="Open conversation menu">
<div role="listbox" aria-label="Conversation sessions">
<div role="option" aria-selected={isActive}>
```

### Focus Management
- Focus trap in modal dialogs
- Return focus to trigger after dialog close
- Visible focus indicators on all interactive elements
- Skip link to main chat area

### Screen Reader Announcements
- "New conversation created"
- "Conversation renamed to [title]"
- "Conversation deleted"
- "[N] conversations available"

---

## Type Definitions

```typescript
// types/conversation.ts

export interface ConversationSession {
  id: string;
  agentId: string;
  title: string;
  preview: string;
  messageCount: number;
  createdAt: string;   // ISO date string
  updatedAt: string;   // ISO date string
}

export interface ConversationMessage {
  id: string;
  sessionId: string;
  role: "user" | "assistant";
  content: string;
  clarificationOptions?: string[];
  createdAt: string;
}

export interface ConversationState {
  sessions: ConversationSession[];
  activeSessionId: string | null;
  messages: ConversationMessage[];
  isLoadingSessions: boolean;
  isLoadingMessages: boolean;
}
```

---

## File Structure Recommendation

```
web/components/
├── agents/
│   ├── agent-chat.tsx              # Existing (refactor)
│   ├── agent-chat-with-history.tsx # New wrapper component
│   └── chat/
│       ├── index.ts
│       ├── conversation-sidebar.tsx
│       ├── session-item.tsx
│       ├── session-list-skeleton.tsx
│       ├── session-list-empty.tsx
│       ├── rename-session-dialog.tsx
│       ├── delete-session-dialog.tsx
│       ├── mobile-conversation-sheet.tsx
│       ├── chat-header.tsx
│       └── use-conversations.ts    # Custom hook for state
```

---

## Implementation Priority

### Phase 1: Core Components (Day 1-2)
1. ConversationSidebar (desktop only)
2. SessionItem with all states
3. SessionListEmpty
4. SessionListSkeleton
5. Basic session selection

### Phase 2: Actions & Dialogs (Day 2-3)
1. RenameSessionDialog
2. DeleteSessionDialog (AlertDialog)
3. DropdownMenu actions
4. New chat functionality

### Phase 3: Responsive & Polish (Day 3-4)
1. Mobile Sheet implementation
2. Tablet collapsible sidebar
3. Keyboard navigation
4. Animation polish
5. Accessibility audit

### Phase 4: Integration (Day 4-5)
1. API integration for session CRUD
2. URL state management
3. Local storage for session persistence
4. Error handling states
5. Testing

---

## Quick Reference: Tailwind Classes

### Session Item (Complete)
```tsx
// Container
"group relative flex cursor-pointer flex-col gap-1 rounded-lg border border-transparent p-3 transition-all duration-150 hover:bg-accent hover:border-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"

// Active state addition
"bg-accent border-l-2 border-l-primary"

// Title
"text-sm font-medium text-foreground line-clamp-1"

// Preview
"text-xs text-muted-foreground line-clamp-2"

// Timestamp
"text-[10px] text-muted-foreground"

// Actions button
"h-6 w-6 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
```

### Sidebar (Complete)
```tsx
// Container
"flex h-[600px] w-72 flex-col rounded-lg border border-border bg-card"

// Header
"flex items-center justify-between border-b border-border p-4"

// Title
"text-sm font-semibold text-foreground"

// New chat button
"h-8 w-8"
```
