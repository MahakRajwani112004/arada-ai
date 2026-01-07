import { useState, useRef, useEffect } from 'react';
import { X, Send, Sparkles, User, ChevronRight, Loader2 } from 'lucide-react';
import type { ChatMessage } from '../../types';
import { mockChatMessages, suggestedQuestions } from '../../data/mockData';

interface ChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  contextTitle?: string;
}

export function ChatDrawer({ isOpen, onClose, contextTitle }: ChatDrawerProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(mockChatMessages);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Based on your question about "${inputValue}", I've analyzed the relevant data. Here's what I found:\n\nThe trend shows consistent growth over the past quarter, with a notable spike in the last two weeks. Key contributing factors include seasonal patterns and recent marketing campaigns.\n\nWould you like me to dig deeper into any specific aspect?`,
        timestamp: new Date(),
        followUpQuestions: [
          'Show me the breakdown by region',
          'Compare to the same period last year',
          'What are the top contributing factors?',
        ],
      };
      setMessages(prev => [...prev, aiResponse]);
      setIsLoading(false);
    }, 1500);
  };

  const handleSuggestedQuestion = (question: string) => {
    setInputValue(question);
    inputRef.current?.focus();
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed right-0 top-0 h-screen w-[420px] bg-white shadow-modal z-50
        transform transition-transform duration-300 ease-out flex flex-col">
        {/* Header */}
        <div className="px-5 py-4 border-b border-neutral-100 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-brand-purple/10 to-brand-blue/10">
              <Sparkles size={20} className="text-primary-500" />
            </div>
            <div>
              <h3 className="text-heading-sm text-neutral-950">AI Assistant</h3>
              {contextTitle && (
                <p className="text-caption text-neutral-500">
                  Context: {contextTitle}
                </p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
          >
            <X size={20} className="text-neutral-500" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 scrollbar-thin">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              {/* Avatar */}
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                ${message.role === 'assistant'
                  ? 'bg-gradient-to-br from-brand-purple to-brand-blue'
                  : 'bg-neutral-200'
                }`}
              >
                {message.role === 'assistant' ? (
                  <Sparkles size={14} className="text-white" />
                ) : (
                  <User size={14} className="text-neutral-600" />
                )}
              </div>

              {/* Message Content */}
              <div className={`max-w-[85%] ${message.role === 'user' ? 'text-right' : ''}`}>
                <div className={`rounded-2xl px-4 py-3
                  ${message.role === 'assistant'
                    ? 'bg-neutral-100 text-neutral-800 rounded-tl-md'
                    : 'bg-primary-500 text-white rounded-tr-md'
                  }`}
                >
                  <p className="text-body-sm whitespace-pre-wrap">{message.content}</p>
                </div>

                {/* Follow-up Questions */}
                {message.role === 'assistant' && message.followUpQuestions && (
                  <div className="mt-3 space-y-2">
                    <p className="text-caption text-neutral-500 font-medium">Follow-up:</p>
                    {message.followUpQuestions.map((question, index) => (
                      <button
                        key={index}
                        onClick={() => handleSuggestedQuestion(question)}
                        className="w-full text-left flex items-center gap-2 px-3 py-2 rounded-lg
                          border border-neutral-200 hover:border-primary-300 hover:bg-primary-50
                          text-body-sm text-neutral-700 transition-colors group"
                      >
                        <span className="flex-1">{question}</span>
                        <ChevronRight size={14} className="text-neutral-400 group-hover:text-primary-500" />
                      </button>
                    ))}
                  </div>
                )}

                <p className="text-caption text-neutral-400 mt-1">
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-purple to-brand-blue
                flex items-center justify-center">
                <Sparkles size={14} className="text-white" />
              </div>
              <div className="bg-neutral-100 rounded-2xl rounded-tl-md px-4 py-3">
                <Loader2 size={16} className="text-neutral-500 animate-spin" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Questions (shown when no recent messages) */}
        {messages.length <= 1 && (
          <div className="px-5 pb-3">
            <p className="text-caption text-neutral-500 font-medium mb-2">Try asking:</p>
            <div className="flex flex-wrap gap-2">
              {suggestedQuestions.slice(0, 4).map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestedQuestion(question)}
                  className="px-3 py-1.5 rounded-full border border-neutral-200
                    text-caption text-neutral-600 hover:border-primary-300
                    hover:bg-primary-50 hover:text-primary-600 transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 border-t border-neutral-100">
          <div className="flex items-center gap-2">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask about your data..."
              className="flex-1 px-4 py-3 rounded-xl border border-neutral-200 bg-neutral-50
                text-body-sm text-neutral-950 placeholder:text-neutral-500
                focus:outline-none focus:ring-2 focus:ring-primary-300 focus:border-primary-400
                transition-all duration-200"
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || isLoading}
              className="p-3 rounded-xl bg-primary-500 text-white
                hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed
                transition-colors"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
