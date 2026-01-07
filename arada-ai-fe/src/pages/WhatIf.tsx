import { useState, useMemo } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Sparkles,
  RefreshCw,
  Download,
  AlertCircle,
  DollarSign,
  Users,
  Building2,
  Target,
  Percent,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
} from 'recharts';

// Current baseline values from the data
const BASELINE = {
  totalBookings: 1000,
  cancellationRate: 50.9,
  activeBookings: 491,
  netSales: 5372, // in millions AED
  collectionRate: 37.2,
  amountRealized: 2000, // in millions AED
  amountOutstanding: 3372, // in millions AED
  directSalesPercent: 48.7,
  brokerSalesPercent: 51.3,
  avgDealSize: 5.37, // in millions AED
  brokerCancellationRate: 54,
  directCancellationRate: 47,
};

interface SliderConfig {
  id: string;
  label: string;
  icon: React.ElementType;
  min: number;
  max: number;
  step: number;
  unit: string;
  baseline: number;
  color: string;
  description: string;
}

const sliderConfigs: SliderConfig[] = [
  {
    id: 'cancellationRate',
    label: 'Cancellation Rate',
    icon: AlertCircle,
    min: 10,
    max: 60,
    step: 1,
    unit: '%',
    baseline: BASELINE.cancellationRate,
    color: '#EF4444',
    description: 'What if we reduce cancellations?',
  },
  {
    id: 'collectionRate',
    label: 'Collection Rate',
    icon: DollarSign,
    min: 30,
    max: 80,
    step: 1,
    unit: '%',
    baseline: BASELINE.collectionRate,
    color: '#10B981',
    description: 'What if we improve collections?',
  },
  {
    id: 'directSalesPercent',
    label: 'Direct Sales Mix',
    icon: Users,
    min: 30,
    max: 80,
    step: 1,
    unit: '%',
    baseline: BASELINE.directSalesPercent,
    color: '#1E50A8',
    description: 'What if we shift from broker to direct?',
  },
  {
    id: 'avgDealSize',
    label: 'Avg Deal Size',
    icon: Building2,
    min: 4,
    max: 8,
    step: 0.1,
    unit: 'M',
    baseline: BASELINE.avgDealSize,
    color: '#8B5CF6',
    description: 'What if we focus on premium units?',
  },
];

export function WhatIf() {
  const [values, setValues] = useState({
    cancellationRate: BASELINE.cancellationRate,
    collectionRate: BASELINE.collectionRate,
    directSalesPercent: BASELINE.directSalesPercent,
    avgDealSize: BASELINE.avgDealSize,
  });

  // Calculate projected metrics based on slider values
  const projections = useMemo(() => {
    const newCancellationRate = values.cancellationRate;
    const newCollectionRate = values.collectionRate;
    const newDirectPercent = values.directSalesPercent;
    const newAvgDealSize = values.avgDealSize;

    // Active bookings based on cancellation rate
    const newActiveBookings = Math.round(BASELINE.totalBookings * (1 - newCancellationRate / 100));
    const activeBookingsChange = ((newActiveBookings - BASELINE.activeBookings) / BASELINE.activeBookings) * 100;

    // Net sales based on active bookings and deal size
    const newNetSales = newActiveBookings * newAvgDealSize;
    const netSalesChange = ((newNetSales - BASELINE.netSales) / BASELINE.netSales) * 100;

    // Amount realized based on collection rate
    const newAmountRealized = newNetSales * (newCollectionRate / 100);
    const amountRealizedChange = ((newAmountRealized - BASELINE.amountRealized) / BASELINE.amountRealized) * 100;

    // Outstanding amount
    const newOutstanding = newNetSales - newAmountRealized;
    const outstandingChange = ((newOutstanding - BASELINE.amountOutstanding) / BASELINE.amountOutstanding) * 100;

    // Broker vs Direct impact on cancellation (weighted average)
    const effectiveCancellation = (newDirectPercent / 100) * BASELINE.directCancellationRate +
      ((100 - newDirectPercent) / 100) * BASELINE.brokerCancellationRate;

    // Commission savings from direct sales (assuming 4% commission)
    const brokerSales = BASELINE.totalBookings * ((100 - newDirectPercent) / 100) * newAvgDealSize;
    const baselineBrokerSales = BASELINE.totalBookings * (BASELINE.brokerSalesPercent / 100) * BASELINE.avgDealSize;
    const commissionSavings = (baselineBrokerSales - brokerSales) * 0.04;

    return {
      activeBookings: { value: newActiveBookings, change: activeBookingsChange, baseline: BASELINE.activeBookings },
      netSales: { value: newNetSales, change: netSalesChange, baseline: BASELINE.netSales },
      amountRealized: { value: newAmountRealized, change: amountRealizedChange, baseline: BASELINE.amountRealized },
      outstanding: { value: newOutstanding, change: outstandingChange, baseline: BASELINE.amountOutstanding },
      effectiveCancellation: { value: effectiveCancellation, baseline: BASELINE.cancellationRate },
      commissionSavings: { value: commissionSavings },
    };
  }, [values]);

  // Generate projection chart data
  const projectionChartData = useMemo(() => {
    const months = ['Current', 'Month 1', 'Month 2', 'Month 3', 'Month 4', 'Month 5', 'Month 6'];
    return months.map((month, index) => {
      const progress = index / 6;
      return {
        month,
        baseline: BASELINE.netSales,
        projected: BASELINE.netSales + (projections.netSales.value - BASELINE.netSales) * progress,
        realized: BASELINE.amountRealized + (projections.amountRealized.value - BASELINE.amountRealized) * progress,
      };
    });
  }, [projections]);

  // Comparison data for bar chart
  const comparisonData = [
    {
      metric: 'Active Bookings',
      baseline: BASELINE.activeBookings,
      projected: projections.activeBookings.value,
    },
    {
      metric: 'Net Sales (M)',
      baseline: BASELINE.netSales,
      projected: projections.netSales.value,
    },
    {
      metric: 'Realized (M)',
      baseline: BASELINE.amountRealized,
      projected: projections.amountRealized.value,
    },
  ];

  const handleSliderChange = (id: string, value: number) => {
    setValues((prev) => ({ ...prev, [id]: value }));
  };

  const handleReset = () => {
    setValues({
      cancellationRate: BASELINE.cancellationRate,
      collectionRate: BASELINE.collectionRate,
      directSalesPercent: BASELINE.directSalesPercent,
      avgDealSize: BASELINE.avgDealSize,
    });
  };

  const hasChanges = Object.entries(values).some(
    ([key, value]) => value !== BASELINE[key as keyof typeof BASELINE]
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-heading-xl text-neutral-950">What-If Analysis</h1>
          <p className="text-body-md text-neutral-600 mt-1">
            Adjust the parameters below to see projected impact on your portfolio
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleReset}
            disabled={!hasChanges}
            className="btn-ghost flex items-center gap-2 disabled:opacity-50"
          >
            <RefreshCw size={16} />
            Reset
          </button>
          <button className="btn-primary flex items-center gap-2">
            <Download size={16} />
            Export Scenario
          </button>
        </div>
      </div>

      {/* Change Indicator */}
      {hasChanges && (
        <div className="p-4 bg-primary-50 border border-primary-200 rounded-xl flex items-center gap-3">
          <Sparkles size={20} className="text-primary-500" />
          <div className="flex-1">
            <p className="text-body-sm font-medium text-primary-700">
              Scenario Active: You're viewing projected outcomes based on your adjustments
            </p>
          </div>
          <div className="flex items-center gap-4 text-body-sm">
            <span className="text-primary-600">
              Net Sales: <strong>{projections.netSales.change >= 0 ? '+' : ''}{projections.netSales.change.toFixed(1)}%</strong>
            </span>
            <span className="text-primary-600">
              Cash Flow: <strong>{projections.amountRealized.change >= 0 ? '+' : ''}{projections.amountRealized.change.toFixed(1)}%</strong>
            </span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Sliders */}
        <div className="space-y-4">
          <h2 className="text-heading-md text-neutral-950">Adjust Parameters</h2>

          {sliderConfigs.map((config) => {
            const Icon = config.icon;
            const currentValue = values[config.id as keyof typeof values];
            const isChanged = currentValue !== config.baseline;
            const changePercent = ((currentValue - config.baseline) / config.baseline) * 100;

            return (
              <div
                key={config.id}
                className={`card p-4 transition-all ${isChanged ? 'ring-2 ring-primary-200 bg-primary-50/30' : ''}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div
                      className="p-2 rounded-lg"
                      style={{ backgroundColor: `${config.color}15` }}
                    >
                      <Icon size={18} style={{ color: config.color }} />
                    </div>
                    <div>
                      <h3 className="text-body-sm font-semibold text-neutral-950">{config.label}</h3>
                      <p className="text-caption text-neutral-500">{config.description}</p>
                    </div>
                  </div>
                  {isChanged && (
                    <span className={`text-caption font-medium ${changePercent > 0 ? 'text-error-600' : 'text-success-600'}`}>
                      {changePercent > 0 ? '+' : ''}{changePercent.toFixed(1)}%
                    </span>
                  )}
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-caption text-neutral-400">
                      Baseline: {config.baseline}{config.unit}
                    </span>
                    <span className="text-heading-sm font-bold" style={{ color: config.color }}>
                      {currentValue.toFixed(config.step < 1 ? 1 : 0)}{config.unit}
                    </span>
                  </div>

                  <input
                    type="range"
                    min={config.min}
                    max={config.max}
                    step={config.step}
                    value={currentValue}
                    onChange={(e) => handleSliderChange(config.id, parseFloat(e.target.value))}
                    className="w-full h-2 bg-neutral-200 rounded-lg appearance-none cursor-pointer accent-primary-500"
                    style={{
                      background: `linear-gradient(to right, ${config.color} 0%, ${config.color} ${((currentValue - config.min) / (config.max - config.min)) * 100}%, #E5E5E5 ${((currentValue - config.min) / (config.max - config.min)) * 100}%, #E5E5E5 100%)`,
                    }}
                  />

                  <div className="flex justify-between text-caption text-neutral-400">
                    <span>{config.min}{config.unit}</span>
                    <span>{config.max}{config.unit}</span>
                  </div>
                </div>
              </div>
            );
          })}

          {/* AI Recommendation */}
          <div className="card p-4 bg-gradient-to-br from-primary-50 to-white border-primary-100">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles size={16} className="text-primary-500" />
              <h3 className="text-body-sm font-semibold text-neutral-950">AI Recommendation</h3>
            </div>
            <p className="text-caption text-neutral-600 leading-relaxed">
              Based on your data, reducing cancellation rate to <strong>35%</strong> while improving collection to <strong>50%</strong> would yield the highest ROI. This combination could recover <strong>AED 1.8B</strong> in value.
            </p>
            <button
              onClick={() => {
                setValues({
                  cancellationRate: 35,
                  collectionRate: 50,
                  directSalesPercent: 60,
                  avgDealSize: 5.8,
                });
              }}
              className="mt-3 w-full btn-ghost text-body-sm text-primary-600 border border-primary-200"
            >
              Apply Recommended Settings
            </button>
          </div>
        </div>

        {/* Right Column - Results */}
        <div className="lg:col-span-2 space-y-6">
          {/* Impact Metrics */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="card p-4">
              <div className="flex items-center gap-2 mb-2">
                <Target size={16} className="text-neutral-400" />
                <span className="text-caption text-neutral-500">Active Bookings</span>
              </div>
              <p className="text-heading-lg font-bold text-neutral-950">
                {projections.activeBookings.value.toLocaleString()}
              </p>
              <div className="flex items-center gap-1 mt-1">
                <span className="text-caption text-neutral-400">
                  vs {projections.activeBookings.baseline}
                </span>
                {projections.activeBookings.change !== 0 && (
                  <span className={`flex items-center text-caption font-medium ${projections.activeBookings.change > 0 ? 'text-success-600' : 'text-error-600'}`}>
                    {projections.activeBookings.change > 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                    {projections.activeBookings.change > 0 ? '+' : ''}{projections.activeBookings.change.toFixed(1)}%
                  </span>
                )}
              </div>
            </div>

            <div className="card p-4">
              <div className="flex items-center gap-2 mb-2">
                <Building2 size={16} className="text-neutral-400" />
                <span className="text-caption text-neutral-500">Net Sales</span>
              </div>
              <p className="text-heading-lg font-bold text-neutral-950">
                AED {(projections.netSales.value / 1000).toFixed(2)}B
              </p>
              <div className="flex items-center gap-1 mt-1">
                <span className="text-caption text-neutral-400">
                  vs {(projections.netSales.baseline / 1000).toFixed(2)}B
                </span>
                {projections.netSales.change !== 0 && (
                  <span className={`flex items-center text-caption font-medium ${projections.netSales.change > 0 ? 'text-success-600' : 'text-error-600'}`}>
                    {projections.netSales.change > 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                    {projections.netSales.change > 0 ? '+' : ''}{projections.netSales.change.toFixed(1)}%
                  </span>
                )}
              </div>
            </div>

            <div className="card p-4">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign size={16} className="text-neutral-400" />
                <span className="text-caption text-neutral-500">Cash Realized</span>
              </div>
              <p className="text-heading-lg font-bold text-success-600">
                AED {(projections.amountRealized.value / 1000).toFixed(2)}B
              </p>
              <div className="flex items-center gap-1 mt-1">
                <span className="text-caption text-neutral-400">
                  vs {(projections.amountRealized.baseline / 1000).toFixed(2)}B
                </span>
                {projections.amountRealized.change !== 0 && (
                  <span className={`flex items-center text-caption font-medium ${projections.amountRealized.change > 0 ? 'text-success-600' : 'text-error-600'}`}>
                    {projections.amountRealized.change > 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                    {projections.amountRealized.change > 0 ? '+' : ''}{projections.amountRealized.change.toFixed(1)}%
                  </span>
                )}
              </div>
            </div>

            <div className="card p-4">
              <div className="flex items-center gap-2 mb-2">
                <Percent size={16} className="text-neutral-400" />
                <span className="text-caption text-neutral-500">Outstanding</span>
              </div>
              <p className="text-heading-lg font-bold text-warning-600">
                AED {(projections.outstanding.value / 1000).toFixed(2)}B
              </p>
              <div className="flex items-center gap-1 mt-1">
                <span className="text-caption text-neutral-400">
                  vs {(projections.outstanding.baseline / 1000).toFixed(2)}B
                </span>
                {projections.outstanding.change !== 0 && (
                  <span className={`flex items-center text-caption font-medium ${projections.outstanding.change < 0 ? 'text-success-600' : 'text-error-600'}`}>
                    {projections.outstanding.change < 0 ? <TrendingDown size={12} /> : <TrendingUp size={12} />}
                    {projections.outstanding.change > 0 ? '+' : ''}{projections.outstanding.change.toFixed(1)}%
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Projection Chart */}
          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-heading-md text-neutral-950">6-Month Projection</h3>
                <p className="text-caption text-neutral-500 mt-1">
                  Projected trajectory if changes are implemented progressively
                </p>
              </div>
              <div className="flex items-center gap-4 text-body-sm">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-0.5 bg-neutral-400 rounded"></span>
                  <span className="text-neutral-600">Baseline</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-0.5 bg-primary-500 rounded"></span>
                  <span className="text-neutral-600">Projected Net Sales</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-0.5 bg-success-500 rounded"></span>
                  <span className="text-neutral-600">Cash Realized</span>
                </div>
              </div>
            </div>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={projectionChartData}>
                  <defs>
                    <linearGradient id="projectedGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#1E50A8" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#1E50A8" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="realizedGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#EAEAEC" />
                  <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#82838D', fontSize: 12 }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: '#82838D', fontSize: 12 }} />
                  <Tooltip
                    formatter={(value: number) => [`AED ${(value / 1000).toFixed(2)}B`, '']}
                    contentStyle={{
                      background: '#fff',
                      border: '1px solid #EAEAEC',
                      borderRadius: '8px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="baseline"
                    stroke="#9698A0"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    fill="none"
                    name="Baseline"
                  />
                  <Area
                    type="monotone"
                    dataKey="projected"
                    stroke="#1E50A8"
                    strokeWidth={2}
                    fill="url(#projectedGradient)"
                    name="Projected Net Sales"
                  />
                  <Area
                    type="monotone"
                    dataKey="realized"
                    stroke="#10B981"
                    strokeWidth={2}
                    fill="url(#realizedGradient)"
                    name="Cash Realized"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Comparison Bar Chart */}
          <div className="card p-5">
            <h3 className="text-heading-md text-neutral-950 mb-4">Baseline vs Projected Comparison</h3>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={comparisonData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#EAEAEC" horizontal={false} />
                  <XAxis type="number" axisLine={false} tickLine={false} tick={{ fill: '#82838D', fontSize: 12 }} />
                  <YAxis type="category" dataKey="metric" axisLine={false} tickLine={false} tick={{ fill: '#82838D', fontSize: 12 }} width={110} />
                  <Tooltip
                    contentStyle={{
                      background: '#fff',
                      border: '1px solid #EAEAEC',
                      borderRadius: '8px',
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px' }} />
                  <Bar dataKey="baseline" fill="#D5D6D9" name="Baseline" radius={[0, 4, 4, 0]} />
                  <Bar dataKey="projected" fill="#1E50A8" name="Projected" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Additional Insights */}
          {hasChanges && (
            <div className="grid grid-cols-2 gap-4">
              <div className="card p-4 bg-success-50 border-success-200">
                <h4 className="text-body-sm font-semibold text-success-700 mb-2">Potential Value Recovery</h4>
                <p className="text-heading-lg font-bold text-success-600">
                  AED {((projections.netSales.value - BASELINE.netSales) / 1000).toFixed(2)}B
                </p>
                <p className="text-caption text-success-600 mt-1">
                  Additional net sales from scenario changes
                </p>
              </div>

              <div className="card p-4 bg-primary-50 border-primary-200">
                <h4 className="text-body-sm font-semibold text-primary-700 mb-2">Commission Savings</h4>
                <p className="text-heading-lg font-bold text-primary-600">
                  AED {projections.commissionSavings.value.toFixed(0)}M
                </p>
                <p className="text-caption text-primary-600 mt-1">
                  From shifting to direct sales channel
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
