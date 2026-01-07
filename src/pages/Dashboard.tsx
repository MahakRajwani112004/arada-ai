import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  ArrowRight,
  Zap,
  ChevronRight,
  Target,
  Eye,
  Brain,
  CheckCircle2,
  Activity,
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
} from 'recharts';

// AI-generated discoveries
const aiDiscoveries = [
  {
    id: 1,
    type: 'anomaly',
    icon: AlertTriangle,
    color: 'text-red-500',
    bgColor: 'bg-red-500',
    title: "Cancellation spike detected",
    finding: "50.9% cancellation rate is 3x higher than industry benchmark",
    impact: "AED 2.73B revenue at risk",
    confidence: 94,
  },
  {
    id: 2,
    type: 'pattern',
    icon: Activity,
    color: 'text-amber-500',
    bgColor: 'bg-amber-500',
    title: "Collection bottleneck found",
    finding: "37.2% collection rate with AED 3.37B outstanding",
    impact: "Cash flow severely constrained",
    confidence: 91,
  },
  {
    id: 3,
    type: 'opportunity',
    icon: TrendingUp,
    color: 'text-emerald-500',
    bgColor: 'bg-emerald-500',
    title: "Premium segment outperforming",
    finding: "Emaar Beachfront yields 34% higher avg deal size",
    impact: "Potential AED 420M upside",
    confidence: 88,
  },
];

// What AI analyzed
const analysisStats = {
  transactions: "1,000",
  dataPoints: "47,000+",
  patterns: "23",
  anomalies: "5",
  lastUpdated: "Just now",
};

// Portfolio metrics
const portfolioMetrics = [
  { label: "Portfolio Value", value: "5.37B", prefix: "AED", trend: "+18.2%", isUp: true },
  { label: "Active Deals", value: "491", trend: "-3.2%", isUp: false },
  { label: "Avg Deal Size", value: "5.37M", prefix: "AED", trend: "+4.2%", isUp: true },
  { label: "Health Score", value: "52", suffix: "/100", trend: "At Risk", isUp: false, isScore: true },
];

// AI recommendations
const aiRecommendations = [
  {
    priority: "urgent",
    action: "Reduce cancellation rate to 30%",
    impact: "Recover AED 1.1B in potential lost revenue",
    path: "/what-if",
  },
  {
    priority: "high",
    action: "Accelerate collection on 90+ day accounts",
    impact: "Unlock AED 660M in overdue payments",
    path: "/deep-dive",
  },
  {
    priority: "medium",
    action: "Shift 15% sales from broker to direct",
    impact: "Save AED 95M in commissions annually",
    path: "/what-if",
  },
];

// Distribution data
const distributionData = [
  { name: 'Emaar Beachfront', value: 23, color: '#3B82F6' },
  { name: 'Downtown Dubai', value: 20, color: '#6366F1' },
  { name: 'Dubai Hills', value: 17, color: '#8B5CF6' },
  { name: 'DAMAC Bay', value: 15, color: '#A855F7' },
  { name: 'DAMAC Hills', value: 14, color: '#D946EF' },
  { name: 'DAMAC Lagoons', value: 11, color: '#EC4899' },
];

export function Dashboard() {
  const navigate = useNavigate();
  const [hoveredProject, setHoveredProject] = useState<string | null>(null);
  const [activeDiscovery, setActiveDiscovery] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(true);

  // Simulate AI analysis completion
  useEffect(() => {
    const timer = setTimeout(() => setIsAnalyzing(false), 1500);
    return () => clearTimeout(timer);
  }, []);

  // Rotate through discoveries
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveDiscovery((prev) => (prev + 1) % aiDiscoveries.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30">
      <div className="p-6 space-y-6">

        {/* Compact AI Header */}
        <div className="relative overflow-hidden rounded-xl bg-white border border-slate-200 shadow-sm">
          <div className="h-0.5 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"></div>
          <div className="px-5 py-4">
            <div className="flex items-center justify-between">
              {/* Left: AI Status + Greeting */}
              <div className="flex items-center gap-4">
                <div className="relative">
                  <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                    <Brain size={18} className="text-white" />
                  </div>
                  <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-500 rounded-full border-2 border-white"></span>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-lg font-bold text-slate-900">{getGreeting()}</h1>
                    <span className="text-slate-400">•</span>
                    {isAnalyzing ? (
                      <span className="flex items-center gap-1 text-sm text-blue-600">
                        <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></span>
                        Analyzing...
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-sm text-emerald-600">
                        <CheckCircle2 size={12} />
                        Ready
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-slate-500">
                    Analyzed <strong className="text-slate-700">1,000 transactions</strong> • AED 5.37B •
                    <span className="text-red-600 font-medium"> {analysisStats.anomalies} anomalies</span>,
                    <span className="text-emerald-600 font-medium"> 3 opportunities</span>
                  </p>
                </div>
              </div>

              {/* Right: Compact Stats */}
              <div className="flex items-center gap-3 text-xs">
                {[
                  { label: "Data Points", value: analysisStats.dataPoints },
                  { label: "Patterns", value: analysisStats.patterns },
                ].map((stat, idx) => (
                  <div key={idx} className="text-center px-3 py-1.5 bg-slate-50 rounded-lg">
                    <p className="text-slate-400">{stat.label}</p>
                    <p className="font-semibold text-slate-700">{stat.value}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Portfolio Metrics Row */}
        <div className="grid grid-cols-4 gap-4">
          {portfolioMetrics.map((metric, idx) => (
            <div key={idx} className="p-4 bg-white rounded-xl border border-slate-200">
              <div className="flex items-center justify-between">
                <p className="text-sm text-slate-500">{metric.label}</p>
                <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                  metric.isScore
                    ? 'bg-amber-50 text-amber-600'
                    : metric.isUp ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-500'
                }`}>
                  {!metric.isScore && (metric.isUp ? <TrendingUp size={10} className="inline" /> : <TrendingDown size={10} className="inline" />)}
                  {' '}{metric.trend}
                </span>
              </div>
              <p className="text-xl font-bold text-slate-900 mt-1">
                {metric.prefix && <span className="text-sm text-slate-400">{metric.prefix} </span>}
                {metric.value}
                {metric.suffix && <span className="text-sm text-slate-400">{metric.suffix}</span>}
              </p>
            </div>
          ))}
        </div>

        {/* AI Discoveries Section */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Sparkles size={20} className="text-purple-500" />
              <h2 className="text-xl font-bold text-slate-900">AI Discoveries</h2>
            </div>
            <div className="flex items-center gap-1">
              {aiDiscoveries.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => setActiveDiscovery(idx)}
                  className={`w-2 h-2 rounded-full transition-all ${
                    activeDiscovery === idx ? 'w-6 bg-purple-500' : 'bg-slate-300'
                  }`}
                />
              ))}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {aiDiscoveries.map((discovery, idx) => {
              const Icon = discovery.icon;
              const isActive = activeDiscovery === idx;
              return (
                <div
                  key={discovery.id}
                  onClick={() => setActiveDiscovery(idx)}
                  className={`relative p-5 rounded-xl border-2 cursor-pointer transition-all ${
                    isActive
                      ? 'border-purple-200 bg-gradient-to-br from-purple-50 to-white shadow-lg scale-[1.02]'
                      : 'border-slate-100 bg-white hover:border-slate-200'
                  }`}
                >
                  {isActive && (
                    <div className="absolute top-3 right-3">
                      <span className="flex items-center gap-1 text-xs font-medium text-purple-600 bg-purple-100 px-2 py-1 rounded-full">
                        <Activity size={10} />
                        Active
                      </span>
                    </div>
                  )}

                  <div className={`w-10 h-10 rounded-lg ${discovery.bgColor} bg-opacity-10 flex items-center justify-center mb-3`}>
                    <Icon size={20} className={discovery.color} />
                  </div>

                  <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">
                    {discovery.type}
                  </p>
                  <h3 className="font-semibold text-slate-900">{discovery.title}</h3>
                  <p className="text-sm text-slate-600 mt-2">{discovery.finding}</p>

                  <div className="mt-4 pt-4 border-t border-slate-100">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-slate-500">Impact</p>
                        <p className="text-sm font-semibold text-slate-900">{discovery.impact}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-slate-500">Confidence</p>
                        <p className="text-sm font-semibold text-purple-600">{discovery.confidence}%</p>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-3 gap-6">
          {/* AI Recommendations */}
          <div className="col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <Target size={20} className="text-blue-500" />
              <h2 className="text-xl font-bold text-slate-900">AI Recommendations</h2>
            </div>

            <div className="space-y-3">
              {aiRecommendations.map((rec, idx) => (
                <div
                  key={idx}
                  onClick={() => navigate(rec.path)}
                  className="group p-5 bg-white rounded-xl border border-slate-200 hover:border-blue-200 hover:shadow-md cursor-pointer transition-all"
                >
                  <div className="flex items-start gap-4">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      rec.priority === 'urgent' ? 'bg-red-100' :
                      rec.priority === 'high' ? 'bg-amber-100' : 'bg-blue-100'
                    }`}>
                      <span className={`text-sm font-bold ${
                        rec.priority === 'urgent' ? 'text-red-600' :
                        rec.priority === 'high' ? 'text-amber-600' : 'text-blue-600'
                      }`}>
                        {idx + 1}
                      </span>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-slate-900">{rec.action}</h3>
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                          rec.priority === 'urgent' ? 'bg-red-100 text-red-700' :
                          rec.priority === 'high' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'
                        }`}>
                          {rec.priority}
                        </span>
                      </div>
                      <p className="text-sm text-slate-600 mt-1">{rec.impact}</p>
                    </div>
                    <ArrowRight size={20} className="text-slate-300 group-hover:text-blue-500 group-hover:translate-x-1 transition-all" />
                  </div>
                </div>
              ))}
            </div>

            {/* CTA Card */}
            <div className="mt-4 p-5 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl text-white">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-lg">Ready to explore scenarios?</h3>
                  <p className="text-blue-100 text-sm mt-1">
                    Use What-If analysis to simulate the impact of these recommendations
                  </p>
                </div>
                <button
                  onClick={() => navigate('/what-if')}
                  className="px-5 py-2.5 bg-white text-blue-600 font-medium rounded-lg hover:bg-blue-50 transition-colors flex items-center gap-2"
                >
                  Open What-If
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="space-y-6">
            {/* Portfolio Distribution */}
            <div className="bg-white rounded-xl p-5 border border-slate-200">
              <h3 className="font-semibold text-slate-900 mb-4">Portfolio Distribution</h3>
              <div className="relative h-44">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={distributionData}
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={70}
                      paddingAngle={2}
                      dataKey="value"
                      onMouseEnter={(_, index) => setHoveredProject(distributionData[index].name)}
                      onMouseLeave={() => setHoveredProject(null)}
                    >
                      {distributionData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={entry.color}
                          opacity={hoveredProject === null || hoveredProject === entry.name ? 1 : 0.3}
                          style={{ transition: 'opacity 0.2s' }}
                        />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  {hoveredProject ? (
                    <div className="text-center">
                      <p className="text-xs text-slate-500">{hoveredProject}</p>
                      <p className="text-xl font-bold text-slate-900">
                        {distributionData.find(d => d.name === hoveredProject)?.value}%
                      </p>
                    </div>
                  ) : (
                    <div className="text-center">
                      <p className="text-xs text-slate-500">Total</p>
                      <p className="text-xl font-bold text-slate-900">6</p>
                      <p className="text-xs text-slate-500">Projects</p>
                    </div>
                  )}
                </div>
              </div>
              <div className="mt-3 space-y-2">
                {distributionData.slice(0, 4).map((item) => (
                  <div
                    key={item.name}
                    className="flex items-center justify-between text-sm cursor-pointer hover:bg-slate-50 p-1 rounded"
                    onMouseEnter={() => setHoveredProject(item.name)}
                    onMouseLeave={() => setHoveredProject(null)}
                  >
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }}></span>
                      <span className="text-slate-600">{item.name}</span>
                    </div>
                    <span className="font-medium text-slate-900">{item.value}%</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-xl p-5 border border-slate-200">
              <div className="flex items-center gap-2 mb-4">
                <Zap size={18} className="text-amber-500" />
                <h3 className="font-semibold text-slate-900">Quick Actions</h3>
              </div>
              <div className="space-y-2">
                {[
                  { label: "Ask AI a question", path: "/ai-chat", icon: Brain },
                  { label: "Run scenario simulation", path: "/what-if", icon: Target },
                  { label: "Deep dive into data", path: "/deep-dive", icon: Eye },
                  { label: "View all insights", path: "/ai-chat", icon: Sparkles },
                ].map((action, idx) => (
                  <button
                    key={idx}
                    onClick={() => navigate(action.path)}
                    className="w-full flex items-center gap-3 p-3 rounded-lg text-left hover:bg-slate-50 transition-colors group"
                  >
                    <action.icon size={18} className="text-slate-400 group-hover:text-blue-500 transition-colors" />
                    <span className="flex-1 text-sm text-slate-700">{action.label}</span>
                    <ChevronRight size={16} className="text-slate-300 group-hover:text-slate-500 group-hover:translate-x-0.5 transition-all" />
                  </button>
                ))}
              </div>
            </div>

            {/* Need Help Card */}
            <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-5 text-white">
              <div className="flex items-center gap-2 mb-2">
                <Brain size={18} />
                <h4 className="font-semibold">Need deeper analysis?</h4>
              </div>
              <p className="text-sm text-slate-300 mb-4">
                Ask me anything about your portfolio data
              </p>
              <button
                onClick={() => navigate('/ai-chat')}
                className="w-full py-2.5 bg-white text-slate-900 text-sm font-medium rounded-lg hover:bg-slate-100 transition-colors"
              >
                Chat with AI
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
