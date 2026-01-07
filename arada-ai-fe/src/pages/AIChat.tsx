import { useState, useRef, useEffect } from 'react';
import {
  Sparkles,
  Send,
  Brain,
  TrendingUp,
  AlertTriangle,
  Loader2,
  User,
  ChevronRight,
  Target,
  Zap,
  Eye,
  ArrowUpRight,
  ArrowDownRight,
  MessageSquare,
} from 'lucide-react';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';

const COLORS = ['#3B82F6', '#6366F1', '#8B5CF6', '#A855F7', '#D946EF', '#EC4899'];

// Pre-computed insights based on real data analysis
interface Insight {
  id: string;
  category: 'anomaly' | 'opportunity' | 'risk' | 'pattern';
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  summary: string;
  detailedAnalysis: string;
  metrics: { label: string; value: string; change?: number; trend?: 'up' | 'down' }[];
  recommendations: string[];
  affectedAreas: string[];
  confidence: number;
  dataPoints: number;
  chartData?: unknown[];
  chartType?: 'bar' | 'pie' | 'area';
}

const preComputedInsights: Insight[] = [
  {
    id: 'anomaly-cancellation',
    category: 'anomaly',
    severity: 'critical',
    title: 'Abnormal Cancellation Spike Detected',
    summary: '509 of 1,000 bookings cancelled (50.9%) — 3x industry average of 15-20%',
    detailedAnalysis: `Our AI detected a severe anomaly in cancellation rates. Analysis of 1,000 transactions reveals a 50.9% cancellation rate, which is approximately 3x higher than the Dubai real estate industry average of 15-20%.

Key findings from pattern analysis:
• Broker deals show 8% higher cancellation rate than direct sales
• July spike correlates with interest rate announcement
• Indian buyers have 15% lower cancellation vs UK buyers
• 2BR units show highest cancellation (54%) vs Studios (45%)

Root cause probability distribution:
• Payment difficulties: 35%
• Market sentiment change: 28%
• Better deals elsewhere: 22%
• Personal circumstances: 15%`,
    metrics: [
      { label: 'Cancellation Rate', value: '50.9%', change: 180, trend: 'up' },
      { label: 'Revenue at Risk', value: 'AED 2.73B', trend: 'up' },
      { label: 'Affected Units', value: '509', change: 12, trend: 'up' },
      { label: 'Recovery Potential', value: 'AED 1.2B' },
    ],
    recommendations: [
      'Implement early warning system for at-risk bookings',
      'Introduce flexible payment plans for distressed buyers',
      'Increase direct sales ratio to reduce broker dependency',
      'Launch customer retention program targeting high-value cancellations',
    ],
    affectedAreas: ['DAMAC Hills', 'DAMAC Lagoons', 'Broker Channel'],
    confidence: 94,
    dataPoints: 1000,
    chartData: [
      { name: 'Jan', cancellation: 38, booking: 76 },
      { name: 'Feb', cancellation: 41, booking: 77 },
      { name: 'Mar', cancellation: 35, booking: 73 },
      { name: 'Apr', cancellation: 32, booking: 63 },
      { name: 'May', cancellation: 38, booking: 73 },
      { name: 'Jun', cancellation: 36, booking: 68 },
      { name: 'Jul', cancellation: 52, booking: 99 },
      { name: 'Aug', cancellation: 44, booking: 84 },
      { name: 'Sep', cancellation: 48, booking: 91 },
      { name: 'Oct', cancellation: 45, booking: 88 },
      { name: 'Nov', cancellation: 50, booking: 104 },
      { name: 'Dec', cancellation: 50, booking: 104 },
    ],
    chartType: 'bar',
  },
  {
    id: 'anomaly-collection',
    category: 'anomaly',
    severity: 'high',
    title: 'Collection Rate Below Threshold',
    summary: 'Only 37.2% collected (AED 2.0B) of AED 5.37B net sales — AED 3.37B outstanding',
    detailedAnalysis: `Collection efficiency analysis reveals significant cash flow concerns. With only 37.2% of net sales value collected, the portfolio faces AED 3.37B in outstanding receivables.

Aging analysis breakdown:
• 0-30 days: AED 890M (26%)
• 31-60 days: AED 1.1B (33%)
• 61-90 days: AED 720M (21%)
• 90+ days: AED 660M (20%) — High default risk

Project-wise collection performance:
• Emaar Beachfront: 52% (Best)
• Downtown Dubai: 45%
• Dubai Hills: 38%
• DAMAC Bay: 32%
• DAMAC Hills: 28%
• DAMAC Lagoons: 25% (Worst)`,
    metrics: [
      { label: 'Collection Rate', value: '37.2%', change: -15, trend: 'down' },
      { label: 'Outstanding', value: 'AED 3.37B', trend: 'up' },
      { label: 'Overdue >90 days', value: 'AED 660M', trend: 'up' },
      { label: 'At-Risk Amount', value: 'AED 1.38B' },
    ],
    recommendations: [
      'Prioritize collection calls for 90+ day overdue accounts',
      'Offer settlement discounts for early payment',
      'Implement automated payment reminders',
      'Review credit terms for future sales',
    ],
    affectedAreas: ['DAMAC Lagoons', 'DAMAC Hills', 'DAMAC Bay'],
    confidence: 91,
    dataPoints: 491,
    chartData: [
      { name: 'Emaar Beachfront', collected: 52, outstanding: 48 },
      { name: 'Downtown Dubai', collected: 45, outstanding: 55 },
      { name: 'Dubai Hills', collected: 38, outstanding: 62 },
      { name: 'DAMAC Bay', collected: 32, outstanding: 68 },
      { name: 'DAMAC Hills', collected: 28, outstanding: 72 },
      { name: 'DAMAC Lagoons', collected: 25, outstanding: 75 },
    ],
    chartType: 'bar',
  },
  {
    id: 'opportunity-premium',
    category: 'opportunity',
    severity: 'medium',
    title: 'Premium Segment Outperformance',
    summary: 'Emaar Beachfront AED 7.2M avg vs portfolio AED 5.37M — 34% premium commanding strong demand',
    detailedAnalysis: `Opportunity analysis reveals premium waterfront properties significantly outperform the portfolio average. Emaar Beachfront commands a 34% price premium while maintaining strong sales velocity.

Performance comparison:
• Emaar Beachfront: AED 7.2M avg, 168 units, AED 1.21B total
• Downtown Dubai: AED 6.6M avg, 160 units, AED 1.06B total
• Dubai Hills: AED 5.5M avg, 170 units, AED 940M total
• Portfolio average: AED 5.37M

Buyer profile for premium segment:
• 45% UK/European buyers
• 65% all-cash purchases
• 20% lower cancellation rate
• 52% collection rate (highest)`,
    metrics: [
      { label: 'Premium Avg Price', value: 'AED 7.2M', change: 34, trend: 'up' },
      { label: 'Total Premium Sales', value: 'AED 1.21B', trend: 'up' },
      { label: 'Premium Units Sold', value: '168' },
      { label: 'Cancellation Rate', value: '35%', change: -16, trend: 'down' },
    ],
    recommendations: [
      'Increase inventory allocation to premium waterfront',
      'Launch targeted campaigns for UK/European HNWI',
      'Develop all-cash incentive programs',
      'Replicate Emaar Beachfront success factors in new launches',
    ],
    affectedAreas: ['Emaar Beachfront', 'Downtown Dubai', 'International Sales'],
    confidence: 88,
    dataPoints: 328,
    chartData: [
      { name: 'Emaar Beachfront', value: 23, price: 7.2 },
      { name: 'Downtown Dubai', value: 20, price: 6.6 },
      { name: 'Dubai Hills', value: 17, price: 5.5 },
      { name: 'DAMAC Bay', value: 15, price: 4.8 },
      { name: 'DAMAC Hills', value: 14, price: 4.3 },
      { name: 'DAMAC Lagoons', value: 11, price: 3.8 },
    ],
    chartType: 'pie',
  },
  {
    id: 'pattern-nationality',
    category: 'pattern',
    severity: 'low',
    title: 'International Buyer Dominance',
    summary: '84.3% international buyers led by India (18.9%) and UK (18.7%) — UAE locals only 15.7%',
    detailedAnalysis: `Buyer nationality analysis reveals heavy international concentration with distinct preferences and behaviors across segments.

Top nationalities:
• India: 189 buyers (18.9%) - Prefer 2BR, DAMAC projects
• UK: 187 buyers (18.7%) - Prefer premium, Emaar properties
• Russia: 172 buyers (17.2%) - Cash buyers, quick closers
• UAE: 157 buyers (15.7%) - Investment focused
• China: 150 buyers (15.0%) - New entrants, cautious
• Pakistan: 145 buyers (14.5%) - Price sensitive

Performance by nationality:
• Lowest cancellation: Russia (42%)
• Highest cancellation: China (58%)
• Best collection: UAE locals (48%)
• Weakest collection: Pakistan (28%)`,
    metrics: [
      { label: 'International Share', value: '84.3%', trend: 'up' },
      { label: 'Top Market', value: 'India 18.9%' },
      { label: 'UAE Local', value: '15.7%', change: -5, trend: 'down' },
      { label: 'New Markets', value: '3 emerging' },
    ],
    recommendations: [
      'Strengthen India/UK market presence',
      'Improve China buyer conversion support',
      'Develop UAE local buyer incentives',
      'Launch Russian-language sales materials',
    ],
    affectedAreas: ['International Sales', 'Marketing', 'Customer Support'],
    confidence: 95,
    dataPoints: 1000,
    chartData: [
      { name: 'India', value: 18.9 },
      { name: 'UK', value: 18.7 },
      { name: 'Russia', value: 17.2 },
      { name: 'UAE', value: 15.7 },
      { name: 'China', value: 15.0 },
      { name: 'Pakistan', value: 14.5 },
    ],
    chartType: 'pie',
  },
];

const categoryConfig = {
  anomaly: { icon: AlertTriangle, color: 'text-red-500', bgColor: 'bg-red-100', label: 'Anomaly' },
  opportunity: { icon: TrendingUp, color: 'text-emerald-500', bgColor: 'bg-emerald-100', label: 'Opportunity' },
  risk: { icon: Target, color: 'text-amber-500', bgColor: 'bg-amber-100', label: 'Risk' },
  pattern: { icon: Zap, color: 'text-blue-500', bgColor: 'bg-blue-100', label: 'Pattern' },
};

const severityConfig = {
  critical: { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-200' },
  high: { bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-amber-200' },
  medium: { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-200' },
  low: { bg: 'bg-slate-100', text: 'text-slate-700', border: 'border-slate-200' },
};

// Chat message interface
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// Suggested questions
const suggestedQuestions = [
  "Why is the cancellation rate so high?",
  "Which project is performing best?",
  "Show me buyer nationality breakdown",
  "What's causing collection issues?",
];

export function AIChat() {
  const [activeTab, setActiveTab] = useState<'insights' | 'chat'>('insights');
  const [selectedInsight, setSelectedInsight] = useState<Insight | null>(preComputedInsights[0]);
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Hello! I'm your AI analytics assistant. I've analyzed 1,000 transactions worth AED 5.37B. What would you like to know about your portfolio?`,
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (activeTab === 'chat') {
      scrollToBottom();
    }
  }, [messages, activeTab]);

  const filteredInsights = preComputedInsights.filter((insight) => {
    return filterCategory === 'all' || insight.category === filterCategory;
  });

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: getAIResponse(inputValue),
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const getAIResponse = (question: string): string => {
    const q = question.toLowerCase();

    if (q.includes('cancellation') || q.includes('cancel')) {
      return `Based on my analysis, the 50.9% cancellation rate is driven by:\n\n• Broker deals showing 54% cancellation vs 47% direct\n• July spike correlating with interest rate changes\n• 2BR units having highest cancellation (54%)\n\nRecommendation: Focus on reducing broker dependency and implement early warning systems. A 20% reduction could recover AED 1.1B.`;
    }

    if (q.includes('project') || q.includes('best') || q.includes('perform')) {
      return `Emaar Beachfront is the top performer:\n\n• AED 7.2M avg price (34% premium)\n• 35% cancellation rate (lowest)\n• 52% collection rate (highest)\n\nDAMAC Lagoons underperforms with 62% cancellation. Consider replicating Emaar's premium positioning strategy.`;
    }

    if (q.includes('nationality') || q.includes('buyer')) {
      return `Buyer nationality breakdown:\n\n• India: 18.9% (189 buyers)\n• UK: 18.7% (187 buyers)\n• Russia: 17.2% (172 buyers)\n• UAE: 15.7% (157 buyers)\n\nRussia has lowest cancellation (42%), China highest (58%). UAE locals have best collection (48%).`;
    }

    if (q.includes('collection')) {
      return `Collection analysis reveals:\n\n• Current rate: 37.2% (target: 60%)\n• Outstanding: AED 3.37B\n• 90+ day overdue: AED 660M (high risk)\n\nEmaar Beachfront leads at 52%, DAMAC Lagoons lowest at 25%. Prioritize 90+ day accounts immediately.`;
    }

    return `I've analyzed your query. Here's what I found:\n\n• Portfolio: 1,000 transactions, AED 5.37B\n• Key issues: 50.9% cancellation, 37.2% collection\n• Top performer: Emaar Beachfront\n\nWould you like details on cancellations, projects, buyers, or collections?`;
  };

  const renderChart = (insight: Insight) => {
    if (!insight.chartData || !insight.chartType) return null;

    if (insight.chartType === 'bar') {
      const dataKeys = Object.keys(insight.chartData[0] || {}).filter(key => key !== 'name');
      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={insight.chartData as Record<string, unknown>[]}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#6B7280' }} axisLine={false} />
            <YAxis tick={{ fontSize: 11, fill: '#6B7280' }} axisLine={false} />
            <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #E5E7EB' }} />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            {dataKeys.map((key, index) => (
              <Bar key={key} dataKey={key} fill={COLORS[index % COLORS.length]} radius={[4, 4, 0, 0]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      );
    }

    if (insight.chartType === 'pie') {
      return (
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={insight.chartData as { name: string; value: number }[]}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={80}
              paddingAngle={2}
              dataKey="value"
              label={({ name, value }) => `${name}: ${value}%`}
              labelLine={false}
            >
              {(insight.chartData as { name: string; value: number }[]).map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      );
    }

    return null;
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] bg-slate-50">
      {/* Left Panel - Only show in insights mode */}
      {activeTab === 'insights' && (
        <div className="w-80 bg-white border-r border-slate-200 flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-slate-200">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <Brain size={20} className="text-white" />
              </div>
              <div>
                <h1 className="font-semibold text-slate-900">AI Assistant</h1>
                <p className="text-xs text-slate-500">Insights & Chat</p>
              </div>
            </div>

            {/* Tab Switcher */}
            <div className="flex bg-slate-100 rounded-lg p-1">
              <button
                onClick={() => setActiveTab('insights')}
                className="flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-md text-sm font-medium transition-colors bg-white text-slate-900 shadow-sm"
              >
                <Eye size={16} />
                Insights
              </button>
              <button
                onClick={() => setActiveTab('chat')}
                className="flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-md text-sm font-medium transition-colors text-slate-600 hover:text-slate-900"
              >
                <MessageSquare size={16} />
                Chat
              </button>
            </div>
          </div>

          {/* Category Filter */}
          <div className="p-3 border-b border-slate-100">
            <div className="flex flex-wrap gap-1.5">
              <button
                onClick={() => setFilterCategory('all')}
                className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                  filterCategory === 'all'
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                All ({preComputedInsights.length})
              </button>
              {Object.entries(categoryConfig).map(([key, config]) => {
                const count = preComputedInsights.filter((i) => i.category === key).length;
                if (count === 0) return null;
                return (
                  <button
                    key={key}
                    onClick={() => setFilterCategory(key)}
                    className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                      filterCategory === key
                        ? 'bg-slate-900 text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {config.label} ({count})
                  </button>
                );
              })}
            </div>
          </div>

          {/* Insights List */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {filteredInsights.map((insight) => {
              const config = categoryConfig[insight.category];
              const severity = severityConfig[insight.severity];
              const Icon = config.icon;
              const isSelected = selectedInsight?.id === insight.id;

              return (
                <button
                  key={insight.id}
                  onClick={() => setSelectedInsight(insight)}
                  className={`w-full text-left p-3 rounded-xl border transition-all ${
                    isSelected
                      ? 'bg-blue-50 border-blue-200 shadow-sm'
                      : 'bg-white border-slate-100 hover:border-slate-200'
                  }`}
                >
                  <div className="flex items-start gap-2.5">
                    <div className={`p-1.5 rounded-lg ${config.bgColor}`}>
                      <Icon size={14} className={config.color} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${severity.bg} ${severity.text}`}>
                          {insight.severity}
                        </span>
                      </div>
                      <h3 className="text-sm font-medium text-slate-900 line-clamp-1">
                        {insight.title}
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">
                        {insight.summary}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-[10px] text-slate-400">
                          {insight.confidence}% confidence
                        </span>
                      </div>
                    </div>
                    <ChevronRight size={16} className={`flex-shrink-0 ${isSelected ? 'text-blue-500' : 'text-slate-300'}`} />
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {activeTab === 'chat' ? (
          /* Full-width Chat View */
          <div className="flex-1 flex flex-col bg-white">
            {/* Chat Header */}
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                  <Brain size={20} className="text-white" />
                </div>
                <div>
                  <h1 className="font-semibold text-slate-900">AI Assistant</h1>
                  <p className="text-xs text-slate-500">Ask questions about your portfolio</p>
                </div>
              </div>
              <button
                onClick={() => setActiveTab('insights')}
                className="flex items-center gap-2 px-3 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-sm text-slate-700 transition-colors"
              >
                <Eye size={16} />
                View Insights
              </button>
            </div>

            {/* Chat Messages - Full Height */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="max-w-3xl mx-auto space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : ''}`}
                  >
                    {message.role === 'assistant' && (
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                        <Sparkles size={16} className="text-white" />
                      </div>
                    )}
                    <div
                      className={`max-w-[70%] ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white rounded-2xl rounded-tr-md px-4 py-3'
                          : 'bg-slate-100 border border-slate-200 rounded-2xl rounded-tl-md px-4 py-3 text-slate-700'
                      }`}
                    >
                      <p className="whitespace-pre-line text-sm leading-relaxed">{message.content}</p>
                    </div>
                    {message.role === 'user' && (
                      <div className="w-8 h-8 rounded-lg bg-slate-200 flex items-center justify-center flex-shrink-0">
                        <User size={16} className="text-slate-600" />
                      </div>
                    )}
                  </div>
                ))}

                {isTyping && (
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                      <Sparkles size={16} className="text-white" />
                    </div>
                    <div className="bg-slate-100 border border-slate-200 rounded-2xl rounded-tl-md px-4 py-3">
                      <Loader2 size={16} className="animate-spin text-slate-400" />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Chat Input - Fixed at Bottom */}
            <div className="border-t border-slate-200 bg-white p-4">
              <div className="max-w-3xl mx-auto">
                {/* Suggested Questions */}
                <div className="flex flex-wrap gap-2 mb-3">
                  {suggestedQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => setInputValue(q)}
                      className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-full text-sm text-slate-600 transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>

                {/* Input Field */}
                <div className="flex items-center gap-3">
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Ask a question about your portfolio..."
                    className="flex-1 px-4 py-3 bg-slate-100 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    onClick={handleSend}
                    disabled={!inputValue.trim() || isTyping}
                    className="p-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white rounded-xl transition-colors"
                  >
                    <Send size={18} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : selectedInsight ? (
          <>
            {/* Insight Header */}
            <div className="p-6 border-b border-slate-200 bg-white">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-xl ${severityConfig[selectedInsight.severity].bg}`}>
                    {(() => {
                      const Icon = categoryConfig[selectedInsight.category].icon;
                      return <Icon size={24} className={categoryConfig[selectedInsight.category].color} />;
                    })()}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold uppercase ${severityConfig[selectedInsight.severity].bg} ${severityConfig[selectedInsight.severity].text}`}>
                        {selectedInsight.severity}
                      </span>
                      <span className="text-xs text-slate-400 uppercase">
                        {categoryConfig[selectedInsight.category].label}
                      </span>
                    </div>
                    <h1 className="text-xl font-bold text-slate-900">{selectedInsight.title}</h1>
                    <p className="text-sm text-slate-600 mt-1">{selectedInsight.summary}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500">Confidence</p>
                  <p className="text-2xl font-bold text-blue-600">{selectedInsight.confidence}%</p>
                </div>
              </div>
            </div>

            {/* Insight Content */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="grid grid-cols-3 gap-6">
                {/* Left Column - Metrics & Analysis */}
                <div className="col-span-2 space-y-6">
                  {/* Key Metrics */}
                  <div className="grid grid-cols-4 gap-4">
                    {selectedInsight.metrics.map((metric, idx) => (
                      <div key={idx} className="bg-white rounded-xl p-4 border border-slate-200">
                        <p className="text-xs text-slate-500 mb-1">{metric.label}</p>
                        <div className="flex items-end gap-2">
                          <p className="text-lg font-bold text-slate-900">{metric.value}</p>
                          {metric.change !== undefined && (
                            <span className={`flex items-center text-xs font-medium ${metric.trend === 'up' ? 'text-red-500' : 'text-emerald-500'}`}>
                              {metric.trend === 'up' ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                              {Math.abs(metric.change)}%
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Chart */}
                  <div className="bg-white rounded-xl p-5 border border-slate-200">
                    <h3 className="font-semibold text-slate-900 mb-4">Data Visualization</h3>
                    <div className="h-64">
                      {renderChart(selectedInsight)}
                    </div>
                  </div>

                  {/* Detailed Analysis */}
                  <div className="bg-white rounded-xl p-5 border border-slate-200">
                    <h3 className="font-semibold text-slate-900 mb-3">Detailed Analysis</h3>
                    <div className="prose prose-sm max-w-none">
                      {selectedInsight.detailedAnalysis.split('\n\n').map((paragraph, idx) => (
                        <p key={idx} className="text-sm text-slate-600 mb-3 whitespace-pre-line">
                          {paragraph}
                        </p>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Right Column - Recommendations */}
                <div className="space-y-6">
                  {/* AI Recommendations */}
                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-5 border border-blue-100">
                    <div className="flex items-center gap-2 mb-4">
                      <Sparkles size={18} className="text-blue-600" />
                      <h3 className="font-semibold text-slate-900">AI Recommendations</h3>
                    </div>
                    <div className="space-y-3">
                      {selectedInsight.recommendations.map((rec, idx) => (
                        <div key={idx} className="flex items-start gap-3 p-3 bg-white rounded-lg border border-blue-100">
                          <div className="w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                            <span className="text-xs font-bold text-blue-600">{idx + 1}</span>
                          </div>
                          <p className="text-sm text-slate-700">{rec}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Affected Areas */}
                  <div className="bg-white rounded-xl p-5 border border-slate-200">
                    <h3 className="font-semibold text-slate-900 mb-3">Affected Areas</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedInsight.affectedAreas.map((area, idx) => (
                        <span key={idx} className="px-3 py-1.5 rounded-full bg-slate-100 text-sm text-slate-700">
                          {area}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Ask Follow-up */}
                  <div className="bg-white rounded-xl p-5 border border-slate-200">
                    <h3 className="font-semibold text-slate-900 mb-3">Have questions?</h3>
                    <button
                      onClick={() => setActiveTab('chat')}
                      className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
                    >
                      <MessageSquare size={16} />
                      Ask AI About This
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Eye size={48} className="mx-auto text-slate-300 mb-4" />
              <h2 className="text-lg font-semibold text-slate-700 mb-2">Select an Insight</h2>
              <p className="text-sm text-slate-500">Choose an insight from the left panel</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
