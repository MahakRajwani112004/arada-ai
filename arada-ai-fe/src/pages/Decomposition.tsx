import { useState } from 'react';
import {
  ChevronRight,
  ChevronDown,
  TrendingUp,
  TrendingDown,
  GitBranch,
  Layers,
  Sparkles,
  Filter,
} from 'lucide-react';
import {
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  FunnelChart,
  Funnel,
  LabelList,
  Cell,
} from 'recharts';

// Decomposition tree data
interface TreeNode {
  id: string;
  name: string;
  value: string;
  percentage?: number;
  change?: number;
  children?: TreeNode[];
  expanded?: boolean;
}

const netSalesTree: TreeNode = {
  id: 'root',
  name: 'Net Sales',
  value: 'AED 2.4B',
  change: 12.4,
  expanded: true,
  children: [
    {
      id: 'aljada',
      name: 'Aljada',
      value: 'AED 1.2B',
      percentage: 50,
      change: 15.2,
      expanded: true,
      children: [
        { id: 'aljada-studio', name: 'Studio', value: 'AED 240M', percentage: 20, change: 8.5 },
        { id: 'aljada-1br', name: '1BR', value: 'AED 360M', percentage: 30, change: 12.1 },
        { id: 'aljada-2br', name: '2BR', value: 'AED 420M', percentage: 35, change: 18.3 },
        { id: 'aljada-3br', name: '3BR+', value: 'AED 180M', percentage: 15, change: 22.0 },
      ],
    },
    {
      id: 'masaar',
      name: 'Masaar',
      value: 'AED 720M',
      percentage: 30,
      change: 8.2,
      expanded: false,
      children: [
        { id: 'masaar-studio', name: 'Studio', value: 'AED 108M', percentage: 15, change: 5.2 },
        { id: 'masaar-1br', name: '1BR', value: 'AED 180M', percentage: 25, change: 7.8 },
        { id: 'masaar-2br', name: '2BR', value: 'AED 252M', percentage: 35, change: 9.1 },
        { id: 'masaar-3br', name: '3BR+', value: 'AED 180M', percentage: 25, change: 11.5 },
      ],
    },
    {
      id: 'nasma',
      name: 'Nasma',
      value: 'AED 360M',
      percentage: 15,
      change: -2.1,
      expanded: false,
      children: [
        { id: 'nasma-villa', name: 'Villas', value: 'AED 216M', percentage: 60, change: -3.2 },
        { id: 'nasma-townhouse', name: 'Townhouses', value: 'AED 144M', percentage: 40, change: -0.5 },
      ],
    },
    {
      id: 'others',
      name: 'Others',
      value: 'AED 120M',
      percentage: 5,
      change: 6.8,
    },
  ],
};

const cancellationDrivers = [
  { name: 'Financing Issues', value: 45, color: '#EF4444' },
  { name: 'Timeline Concerns', value: 30, color: '#F59E0B' },
  { name: 'Price Negotiations', value: 15, color: '#3077F3' },
  { name: 'Personal Reasons', value: 10, color: '#10B981' },
];

const funnelData = [
  { name: 'Leads', value: 12450, fill: '#3077F3' },
  { name: 'Qualified', value: 6225, fill: '#1E50A8' },
  { name: 'Site Visits', value: 3112, fill: '#B96AF7' },
  { name: 'Negotiations', value: 1867, fill: '#FDA052' },
  { name: 'Booked', value: 1247, fill: '#10B981' },
  { name: 'Paid', value: 1122, fill: '#059669' },
];

const waterfallData = [
  { name: 'Opening', value: 2100, total: 2100 },
  { name: 'New Bookings', value: 450, total: 2550 },
  { name: 'Price Increase', value: 120, total: 2670 },
  { name: 'Cancellations', value: -180, total: 2490 },
  { name: 'Refunds', value: -90, total: 2400 },
  { name: 'Closing', value: 2400, total: 2400 },
];

function TreeNodeComponent({
  node,
  depth = 0,
  onToggle,
}: {
  node: TreeNode;
  depth?: number;
  onToggle: (id: string) => void;
}) {
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div className={`${depth > 0 ? 'ml-6 border-l-2 border-neutral-200 pl-4' : ''}`}>
      <div
        className={`
          flex items-center gap-3 p-3 rounded-lg transition-colors cursor-pointer
          ${depth === 0 ? 'bg-primary-50 border border-primary-200' : 'hover:bg-neutral-50'}
        `}
        onClick={() => hasChildren && onToggle(node.id)}
      >
        {hasChildren ? (
          <button className="p-1 hover:bg-neutral-200 rounded">
            {node.expanded ? (
              <ChevronDown size={16} className="text-neutral-500" />
            ) : (
              <ChevronRight size={16} className="text-neutral-500" />
            )}
          </button>
        ) : (
          <div className="w-6" />
        )}

        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className={`font-medium ${depth === 0 ? 'text-heading-sm' : 'text-body-sm'} text-neutral-950`}>
              {node.name}
            </span>
            {node.percentage && (
              <span className="text-caption text-neutral-500">({node.percentage}%)</span>
            )}
          </div>
        </div>

        <div className="text-right">
          <p className={`font-bold ${depth === 0 ? 'text-heading-md' : 'text-body-sm'} text-neutral-950`}>
            {node.value}
          </p>
          {node.change !== undefined && (
            <div className={`flex items-center justify-end gap-1 text-caption ${
              node.change >= 0 ? 'text-success-600' : 'text-error-600'
            }`}>
              {node.change >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              <span>{node.change >= 0 ? '+' : ''}{node.change}%</span>
            </div>
          )}
        </div>
      </div>

      {hasChildren && node.expanded && (
        <div className="mt-2 space-y-2">
          {node.children!.map((child) => (
            <TreeNodeComponent key={child.id} node={child} depth={depth + 1} onToggle={onToggle} />
          ))}
        </div>
      )}
    </div>
  );
}

export function Decomposition() {
  const [treeData, setTreeData] = useState(netSalesTree);
  const [selectedView, setSelectedView] = useState<'tree' | 'funnel' | 'waterfall'>('tree');
  const [selectedMetric, setSelectedMetric] = useState('net-sales');

  const toggleNode = (id: string) => {
    const toggleInTree = (node: TreeNode): TreeNode => {
      if (node.id === id) {
        return { ...node, expanded: !node.expanded };
      }
      if (node.children) {
        return { ...node, children: node.children.map(toggleInTree) };
      }
      return node;
    };
    setTreeData(toggleInTree(treeData));
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-heading-xl text-neutral-950">Decomposition Analysis</h1>
          <p className="text-body-md text-neutral-600 mt-1">
            Understand the "why" behind your metrics with hierarchical breakdowns
          </p>
        </div>
        <button className="flex items-center gap-2 px-3 py-2 rounded-lg border border-neutral-200 text-body-sm text-neutral-600 hover:bg-neutral-50">
          <Filter size={14} />
          Filters
        </button>
      </div>

      {/* View Selector */}
      <div className="flex items-center gap-4">
        <div className="flex gap-1 p-1 bg-neutral-100 rounded-lg">
          {[
            { id: 'tree', label: 'Tree View', icon: GitBranch },
            { id: 'funnel', label: 'Funnel', icon: Layers },
            { id: 'waterfall', label: 'Waterfall', icon: TrendingUp },
          ].map((view) => (
            <button
              key={view.id}
              onClick={() => setSelectedView(view.id as typeof selectedView)}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg text-body-sm transition-colors
                ${selectedView === view.id
                  ? 'bg-white text-neutral-950 shadow-sm'
                  : 'text-neutral-600 hover:text-neutral-950'
                }
              `}
            >
              <view.icon size={16} />
              {view.label}
            </button>
          ))}
        </div>

        {selectedView === 'tree' && (
          <div className="flex gap-2">
            {[
              { id: 'net-sales', label: 'Net Sales' },
              { id: 'bookings', label: 'Bookings' },
              { id: 'cancellations', label: 'Cancellations' },
            ].map((metric) => (
              <button
                key={metric.id}
                onClick={() => setSelectedMetric(metric.id)}
                className={`
                  px-3 py-1.5 rounded-full text-caption transition-colors
                  ${selectedMetric === metric.id
                    ? 'bg-primary-500 text-white'
                    : 'bg-white border border-neutral-200 text-neutral-600 hover:border-neutral-300'
                  }
                `}
              >
                {metric.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Tree View */}
      {selectedView === 'tree' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 card p-5">
            <h3 className="text-heading-md text-neutral-950 mb-4">Metric Hierarchy</h3>
            <TreeNodeComponent node={treeData} onToggle={toggleNode} />
          </div>

          {/* Driver Analysis */}
          <div className="space-y-6">
            <div className="card p-5">
              <h3 className="text-heading-sm text-neutral-950 mb-4">Top Drivers</h3>
              <div className="space-y-4">
                {[
                  { label: 'Aljada 2BR Units', impact: '+AED 420M', percentage: 35, positive: true },
                  { label: 'Marketing Campaign', impact: '+AED 180M', percentage: 15, positive: true },
                  { label: 'Nasma Slowdown', impact: '-AED 45M', percentage: -4, positive: false },
                ].map((driver, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${driver.positive ? 'bg-success-500' : 'bg-error-500'}`} />
                    <div className="flex-1">
                      <p className="text-body-sm text-neutral-700">{driver.label}</p>
                    </div>
                    <div className="text-right">
                      <p className={`text-body-sm font-semibold ${driver.positive ? 'text-success-600' : 'text-error-600'}`}>
                        {driver.impact}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="card p-5">
              <h3 className="text-heading-sm text-neutral-950 mb-4">Cancellation Reasons</h3>
              <div className="space-y-3">
                {cancellationDrivers.map((driver) => (
                  <div key={driver.name} className="space-y-1">
                    <div className="flex items-center justify-between text-body-sm">
                      <span className="text-neutral-700">{driver.name}</span>
                      <span className="font-semibold text-neutral-950">{driver.value}%</span>
                    </div>
                    <div className="h-2 bg-neutral-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${driver.value}%`, backgroundColor: driver.color }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Funnel View */}
      {selectedView === 'funnel' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 card p-5">
            <h3 className="text-heading-md text-neutral-950 mb-4">Sales Funnel</h3>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <FunnelChart>
                  <Tooltip
                    formatter={(value: number) => value.toLocaleString()}
                    contentStyle={{
                      background: '#fff',
                      border: '1px solid #EAEAEC',
                      borderRadius: '8px',
                    }}
                  />
                  <Funnel dataKey="value" data={funnelData} isAnimationActive>
                    {funnelData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                    <LabelList
                      position="right"
                      content={({ x, y, width, height, value, name }: any) => (
                        <g>
                          <text x={x + width + 10} y={y + height / 2} fill="#2E3141" fontSize={14} fontWeight={600}>
                            {name}
                          </text>
                          <text x={x + width + 10} y={y + height / 2 + 18} fill="#82838D" fontSize={12}>
                            {value?.toLocaleString()}
                          </text>
                        </g>
                      )}
                    />
                  </Funnel>
                </FunnelChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="card p-5">
            <h3 className="text-heading-sm text-neutral-950 mb-4">Conversion Rates</h3>
            <div className="space-y-4">
              {funnelData.slice(0, -1).map((stage, index) => {
                const nextStage = funnelData[index + 1];
                const conversionRate = ((nextStage.value / stage.value) * 100).toFixed(1);
                return (
                  <div key={stage.name} className="flex items-center gap-3">
                    <div className="flex-1">
                      <p className="text-body-sm text-neutral-700">
                        {stage.name} → {nextStage.name}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-body-sm font-semibold text-neutral-950">{conversionRate}%</p>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-6 p-4 bg-success-50 rounded-lg">
              <p className="text-caption text-success-700 font-medium">Overall Conversion</p>
              <p className="text-heading-lg font-bold text-success-600">
                {((funnelData[funnelData.length - 1].value / funnelData[0].value) * 100).toFixed(1)}%
              </p>
              <p className="text-caption text-success-600 mt-1">Leads → Paid</p>
            </div>
          </div>
        </div>
      )}

      {/* Waterfall View */}
      {selectedView === 'waterfall' && (
        <div className="card p-5">
          <h3 className="text-heading-md text-neutral-950 mb-4">Net Sales Waterfall (AED M)</h3>
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={waterfallData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#EAEAEC" />
                <XAxis type="number" axisLine={false} tickLine={false} tick={{ fill: '#82838D', fontSize: 12 }} />
                <YAxis
                  type="category"
                  dataKey="name"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#82838D', fontSize: 12 }}
                  width={100}
                />
                <Tooltip
                  formatter={(value: number) => `AED ${Math.abs(value)}M`}
                  contentStyle={{
                    background: '#fff',
                    border: '1px solid #EAEAEC',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {waterfallData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={
                        entry.name === 'Opening' || entry.name === 'Closing'
                          ? '#1E50A8'
                          : entry.value >= 0
                          ? '#10B981'
                          : '#EF4444'
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-6 grid grid-cols-4 gap-4">
            {[
              { label: 'Opening Balance', value: 'AED 2.1B', color: 'primary' },
              { label: 'Additions', value: '+AED 570M', color: 'success' },
              { label: 'Deductions', value: '-AED 270M', color: 'error' },
              { label: 'Closing Balance', value: 'AED 2.4B', color: 'primary' },
            ].map((item) => (
              <div key={item.label} className={`p-4 rounded-lg bg-${item.color}-50`}>
                <p className={`text-caption text-${item.color}-600`}>{item.label}</p>
                <p className={`text-heading-sm font-bold text-${item.color}-700 mt-1`}>{item.value}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Insight */}
      <div className="card p-5 bg-gradient-to-r from-primary-50 to-white border-primary-100">
        <div className="flex items-start gap-4">
          <div className="p-2.5 rounded-xl bg-white shadow-sm">
            <Sparkles size={20} className="text-primary-500" />
          </div>
          <div className="flex-1">
            <h4 className="text-heading-sm text-neutral-950">Key Insight</h4>
            <p className="text-body-sm text-neutral-700 mt-2 leading-relaxed">
              Your funnel shows a significant drop at the <strong>Qualified → Site Visits</strong> stage
              (50% conversion). This is 15% below industry benchmark. Consider implementing
              virtual tours and enhanced follow-up sequences. The Aljada 2BR segment shows
              the highest potential - contributing 35% of Aljada sales with 18.3% growth.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
