import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { KPI } from '../../types';

interface KPICardProps {
  kpi: KPI;
  onClick?: () => void;
  compact?: boolean;
}

export function KPICard({ kpi, onClick, compact = false }: KPICardProps) {
  const isPositive = kpi.changeType === 'increase';
  const isNegative = kpi.changeType === 'decrease';

  // For cancellations, increasing is bad
  const isGoodChange = kpi.id === 'cancellations' ? !isPositive : isPositive;

  const TrendIcon = isPositive ? TrendingUp : isNegative ? TrendingDown : Minus;

  // Generate sparkline path from trend data
  const generateSparkline = () => {
    if (!kpi.trend || kpi.trend.length === 0) return '';

    const width = 60;
    const height = 24;
    const max = Math.max(...kpi.trend);
    const min = Math.min(...kpi.trend);
    const range = max - min || 1;

    const points = kpi.trend.map((value, index) => {
      const x = (index / (kpi.trend.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${x},${y}`;
    });

    return `M ${points.join(' L ')}`;
  };

  if (compact) {
    return (
      <div
        onClick={onClick}
        className={`card p-4 ${onClick ? 'card-hover cursor-pointer' : ''}`}
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="text-body-sm text-neutral-600 mb-1">{kpi.name}</p>
            <p className="text-heading-lg font-bold text-neutral-950">{kpi.formattedValue}</p>
          </div>
          <div className={`flex items-center gap-1 ${isGoodChange ? 'text-success-600' : isNegative || isPositive ? 'text-error-600' : 'text-neutral-500'}`}>
            <TrendIcon size={16} />
            <span className="text-caption font-semibold">
              {isPositive ? '+' : ''}{kpi.change}%
            </span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={onClick}
      className={`card p-5 ${onClick ? 'card-hover cursor-pointer' : ''}`}
    >
      <div className="flex items-start justify-between mb-3">
        <p className="text-body-sm text-neutral-600 font-medium">{kpi.name}</p>
        {/* Sparkline */}
        <svg width="60" height="24" className="text-neutral-300">
          <path
            d={generateSparkline()}
            fill="none"
            stroke={isGoodChange ? '#10B981' : '#EF4444'}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>

      <div className="flex items-end justify-between">
        <div>
          <p className="text-display-sm font-bold text-neutral-950 tracking-tight">
            {kpi.formattedValue}
          </p>
        </div>

        <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-caption font-semibold
          ${isGoodChange
            ? 'bg-success-50 text-success-600'
            : isNegative || isPositive
              ? 'bg-error-50 text-error-600'
              : 'bg-neutral-100 text-neutral-600'
          }`}
        >
          <TrendIcon size={14} />
          <span>{isPositive ? '+' : ''}{kpi.change}%</span>
        </div>
      </div>

      {kpi.description && (
        <p className="text-caption text-neutral-500 mt-3">{kpi.description}</p>
      )}
    </div>
  );
}
