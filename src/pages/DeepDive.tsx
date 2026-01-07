import { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Calendar,
  Filter,
  Download,
  Share2,
  ChevronRight,
  AlertTriangle,
  Sparkles,
  AlertCircle,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import { mockKPIs, nationalityData, unitTypeData, projectsData } from '../data/mockData';

const COLORS = ['#1E50A8', '#3077F3', '#B96AF7', '#FDA052', '#41E6F8', '#10B981'];

// Monthly booking trend data based on real data
const monthlyTrendData = [
  { date: 'Jan', value: 76, baseline: 82 },
  { date: 'Feb', value: 77, baseline: 82 },
  { date: 'Mar', value: 73, baseline: 82 },
  { date: 'Apr', value: 63, baseline: 82 },
  { date: 'May', value: 73, baseline: 82 },
  { date: 'Jun', value: 68, baseline: 82 },
  { date: 'Jul', value: 99, baseline: 82 },
  { date: 'Aug', value: 84, baseline: 82 },
  { date: 'Sep', value: 91, baseline: 82 },
  { date: 'Oct', value: 88, baseline: 82 },
  { date: 'Nov', value: 104, baseline: 82 },
  { date: 'Dec', value: 104, baseline: 82 },
];

// Real project breakdown from data
const projectBreakdown = projectsData.map(p => ({
  name: p.name,
  value: p.netSales,
  percentage: Math.round((p.netSales / 5372) * 100),
  change: p.change,
}));

// Real unit type breakdown
const unitTypeBreakdown = unitTypeData.map(u => ({
  name: u.name,
  value: u.units,
  percentage: Math.round((u.totalSales / 5372) * 100),
}));

// Real buyer nationality breakdown
const buyerTypeBreakdown = nationalityData.map(n => ({
  name: n.name,
  value: n.count,
  percentage: n.percentage,
}));

// Deal type breakdown
const dealTypeBreakdown = [
  { name: 'Broker', value: 513, percentage: 51.3, change: 2.1 },
  { name: 'Direct', value: 487, percentage: 48.7, change: -2.1 },
];

// Lead source breakdown
const leadSourceBreakdown = [
  { name: 'Broker Network', value: 338, percentage: 33.8 },
  { name: 'Digital', value: 332, percentage: 33.2 },
  { name: 'Event', value: 330, percentage: 33.0 },
];

const anomalies = [
  {
    id: 1,
    date: 'Ongoing',
    type: 'critical',
    description: 'Cancellation rate at 50.9% - Half of all bookings cancelled',
    reason: 'Market volatility, financing issues, and buyer sentiment changes',
  },
  {
    id: 2,
    date: 'Collection',
    type: 'warning',
    description: 'Only 37.2% of net sales value collected',
    reason: 'Many units on payment plans with future installments pending',
  },
  {
    id: 3,
    date: 'Jul Peak',
    type: 'spike',
    description: 'July bookings 21% above monthly average (99 vs 82)',
    reason: 'Summer promotions and mid-year investor activity',
  },
];

export function DeepDive() {
  const [selectedKPI, setSelectedKPI] = useState(mockKPIs[0]);
  const [timeRange, setTimeRange] = useState('YTD');
  const [selectedDimension, setSelectedDimension] = useState('project');

  const getBreakdownData = () => {
    switch (selectedDimension) {
      case 'project':
        return projectBreakdown;
      case 'unit':
        return unitTypeBreakdown;
      case 'nationality':
        return buyerTypeBreakdown;
      case 'deal':
        return dealTypeBreakdown;
      case 'lead':
        return leadSourceBreakdown;
      default:
        return projectBreakdown;
    }
  };

  const getAIAnalysis = () => {
    if (selectedKPI.id === 'cancellations') {
      return `The cancellation rate of 50.9% is a critical concern. Analysis shows broker deals (51.3% of total)
      may have higher cancellation rates. Key affected segments: DAMAC Lagoons (-2.8%) and DAMAC Hills (-1.5%)
      are underperforming. Recommend immediate customer retention program and review of broker commission structures.`;
    }
    if (selectedKPI.id === 'collection-rate') {
      return `Collection rate at 37.2% indicates AED 3.37B outstanding. Most units are on payment plans
      with future installments. Emaar Beachfront shows better collection due to premium buyer profiles.
      Consider accelerated collection programs for high-risk accounts.`;
    }
    return `${selectedKPI.name} analysis shows Emaar Beachfront leading with AED 1.2B (22.6% of portfolio)
    at premium AED 7.2M average. Downtown Dubai follows at AED 1.1B. DAMAC properties show mixed performance
    with Bay and Hills stable, but Lagoons underperforming. International buyers (India 18.9%, UK 18.7%)
    dominate purchases, suggesting focus on overseas marketing.`;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-heading-xl text-neutral-950">Deep Dive Analysis</h1>
          <p className="text-body-md text-neutral-600 mt-1">
            Analyze DAMAC & Emaar portfolio performance across 1,000 transactions
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button className="btn-ghost text-body-sm flex items-center gap-2">
            <Download size={16} />
            Export
          </button>
          <button className="btn-ghost text-body-sm flex items-center gap-2">
            <Share2 size={16} />
            Share
          </button>
        </div>
      </div>

      {/* Critical Alert Banner */}
      <div className="card p-4 bg-error-50 border-error-200 border-l-4 border-l-error-500">
        <div className="flex items-center gap-3">
          <AlertCircle size={20} className="text-error-600" />
          <div className="flex-1">
            <p className="text-body-sm font-semibold text-error-700">
              Critical: 50.9% Cancellation Rate Detected
            </p>
            <p className="text-caption text-error-600">
              509 of 1,000 bookings have been cancelled. This requires immediate attention.
            </p>
          </div>
          <button className="btn-primary text-caption bg-error-600 hover:bg-error-700">
            View Analysis
          </button>
        </div>
      </div>

      {/* KPI Selector */}
      <div className="card p-4">
        <p className="text-caption text-neutral-500 font-medium mb-3">Select Metric to Analyze</p>
        <div className="flex gap-2 overflow-x-auto pb-2">
          {mockKPIs.map((kpi) => (
            <button
              key={kpi.id}
              onClick={() => setSelectedKPI(kpi)}
              className={`
                flex-shrink-0 px-4 py-3 rounded-xl border transition-all
                ${selectedKPI.id === kpi.id
                  ? 'bg-primary-50 border-primary-300 text-primary-600'
                  : 'bg-white border-neutral-200 text-neutral-700 hover:border-neutral-300'
                }
                ${kpi.id === 'cancellations' ? 'border-error-200' : ''}
              `}
            >
              <p className="text-caption text-neutral-500">{kpi.name}</p>
              <p className="text-heading-sm font-bold mt-1">{kpi.formattedValue}</p>
              <div className={`flex items-center gap-1 mt-1 text-caption ${
                kpi.changeType === 'increase'
                  ? (kpi.id === 'cancellations' ? 'text-error-600' : 'text-success-600')
                  : (kpi.id === 'cancellations' ? 'text-success-600' : 'text-error-600')
              }`}>
                {kpi.changeType === 'increase' ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                <span>{kpi.changeType === 'increase' ? '+' : ''}{kpi.change}%</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Time Range & Filters */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {['7d', '30d', '90d', 'YTD', 'All'].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`
                px-3 py-1.5 rounded-lg text-body-sm transition-colors
                ${timeRange === range
                  ? 'bg-primary-500 text-white'
                  : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'
                }
              `}
            >
              {range}
            </button>
          ))}
          <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-neutral-200 text-body-sm text-neutral-600 hover:bg-neutral-50">
            <Calendar size={14} />
            Custom
          </button>
        </div>
        <button className="flex items-center gap-2 px-3 py-2 rounded-lg border border-neutral-200 text-body-sm text-neutral-600 hover:bg-neutral-50">
          <Filter size={14} />
          Filters
        </button>
      </div>

      {/* Main Chart */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-heading-md text-neutral-950">Monthly Booking Trend</h3>
            <p className="text-caption text-neutral-500 mt-1">Bookings per month vs average baseline (82)</p>
          </div>
          <div className="flex items-center gap-4 text-body-sm">
            <div className="flex items-center gap-2">
              <span className="w-3 h-0.5 bg-primary-500 rounded"></span>
              <span className="text-neutral-600">Actual Bookings</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-0.5 bg-neutral-300 rounded"></span>
              <span className="text-neutral-600">Avg Baseline</span>
            </div>
          </div>
        </div>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={monthlyTrendData}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#1E50A8" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#1E50A8" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#EAEAEC" />
              <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#82838D', fontSize: 12 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: '#82838D', fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  background: '#fff',
                  border: '1px solid #EAEAEC',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.04)',
                }}
              />
              <Area
                type="monotone"
                dataKey="baseline"
                stroke="#C0C1C6"
                strokeWidth={2}
                strokeDasharray="5 5"
                fill="none"
                name="Baseline"
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#1E50A8"
                strokeWidth={2}
                fill="url(#colorValue)"
                name="Actual"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Anomaly Detection */}
      <div className="card p-5 border-l-4 border-l-error-500">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle size={18} className="text-error-600" />
          <h3 className="text-heading-sm text-neutral-950">Critical Issues & Anomalies</h3>
        </div>
        <div className="space-y-3">
          {anomalies.map((anomaly) => (
            <div key={anomaly.id} className={`flex items-start gap-4 p-3 rounded-lg ${
              anomaly.type === 'critical' ? 'bg-error-50' :
              anomaly.type === 'warning' ? 'bg-warning-50' : 'bg-primary-50'
            }`}>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-body-sm font-semibold text-neutral-950">{anomaly.date}</span>
                  <span className={`text-caption px-2 py-0.5 rounded-full ${
                    anomaly.type === 'critical' ? 'bg-error-100 text-error-700' :
                    anomaly.type === 'warning' ? 'bg-warning-100 text-warning-700' :
                    anomaly.type === 'spike' ? 'bg-success-100 text-success-700' :
                    'bg-primary-100 text-primary-700'
                  }`}>
                    {anomaly.type}
                  </span>
                </div>
                <p className="text-body-sm text-neutral-700 mt-1">{anomaly.description}</p>
                <p className="text-caption text-neutral-500 mt-1">
                  <span className="font-medium">Analysis:</span> {anomaly.reason}
                </p>
              </div>
              <button className="btn-ghost text-caption text-primary-500">
                Investigate
                <ChevronRight size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Dimension Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Breakdown Selection */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-heading-sm text-neutral-950">Breakdown by Dimension</h3>
            <div className="flex gap-1 flex-wrap">
              {[
                { id: 'project', label: 'Development' },
                { id: 'unit', label: 'Unit Type' },
                { id: 'nationality', label: 'Nationality' },
                { id: 'deal', label: 'Deal Type' },
                { id: 'lead', label: 'Lead Source' },
              ].map((dim) => (
                <button
                  key={dim.id}
                  onClick={() => setSelectedDimension(dim.id)}
                  className={`
                    px-2 py-1 rounded-lg text-caption transition-colors
                    ${selectedDimension === dim.id
                      ? 'bg-primary-500 text-white'
                      : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'
                    }
                  `}
                >
                  {dim.label}
                </button>
              ))}
            </div>
          </div>
          <div className="space-y-3">
            {getBreakdownData().map((item, index) => (
              <div key={item.name} className="flex items-center gap-4">
                <div className="w-28 text-body-sm text-neutral-700 font-medium truncate">{item.name}</div>
                <div className="flex-1">
                  <div className="h-8 bg-neutral-100 rounded-lg overflow-hidden">
                    <div
                      className="h-full rounded-lg transition-all"
                      style={{
                        width: `${item.percentage}%`,
                        backgroundColor: COLORS[index % COLORS.length],
                      }}
                    />
                  </div>
                </div>
                <div className="w-14 text-right text-body-sm font-semibold text-neutral-950">
                  {item.percentage}%
                </div>
                {'change' in item && typeof item.change === 'number' && (
                  <div className={`w-14 text-right text-caption ${
                    item.change >= 0 ? 'text-success-600' : 'text-error-600'
                  }`}>
                    {item.change >= 0 ? '+' : ''}{item.change}%
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Pie Chart */}
        <div className="card p-5">
          <h3 className="text-heading-sm text-neutral-950 mb-4">Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={getBreakdownData()}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="percentage"
                  nameKey="name"
                >
                  {getBreakdownData().map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => `${value}%`} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* AI Insight */}
      <div className="card p-5 bg-gradient-to-r from-primary-50 to-white border-primary-100">
        <div className="flex items-start gap-4">
          <div className="p-2.5 rounded-xl bg-white shadow-sm">
            <Sparkles size={20} className="text-primary-500" />
          </div>
          <div className="flex-1">
            <h4 className="text-heading-sm text-neutral-950">AI Analysis Summary</h4>
            <p className="text-body-sm text-neutral-700 mt-2 leading-relaxed">
              {getAIAnalysis()}
            </p>
            <div className="flex items-center gap-3 mt-4">
              <button className="btn-primary text-body-sm">
                Generate Full Report
              </button>
              <button className="btn-ghost text-body-sm text-primary-500">
                Ask follow-up question
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
