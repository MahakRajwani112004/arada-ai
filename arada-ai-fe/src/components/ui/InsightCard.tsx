import { AlertTriangle, TrendingUp, Lightbulb, Info, ChevronRight, Bookmark } from 'lucide-react';
import type { Insight, InsightType } from '../../types';

interface InsightCardProps {
  insight: Insight;
  onClick?: () => void;
  onAskAI?: () => void;
  variant?: 'default' | 'compact' | 'featured';
}

const insightConfig: Record<InsightType, {
  icon: typeof AlertTriangle;
  bgColor: string;
  borderColor: string;
  iconColor: string;
  label: string;
}> = {
  alert: {
    icon: AlertTriangle,
    bgColor: 'bg-warning-50',
    borderColor: 'border-l-warning-500',
    iconColor: 'text-warning-600',
    label: 'Alert',
  },
  opportunity: {
    icon: TrendingUp,
    bgColor: 'bg-success-50',
    borderColor: 'border-l-success-500',
    iconColor: 'text-success-600',
    label: 'Opportunity',
  },
  trend: {
    icon: Lightbulb,
    bgColor: 'bg-primary-50',
    borderColor: 'border-l-primary-400',
    iconColor: 'text-primary-500',
    label: 'Trend',
  },
  info: {
    icon: Info,
    bgColor: 'bg-neutral-100',
    borderColor: 'border-l-neutral-400',
    iconColor: 'text-neutral-600',
    label: 'Info',
  },
};

export function InsightCard({ insight, onClick, onAskAI, variant = 'default' }: InsightCardProps) {
  const config = insightConfig[insight.type];
  const Icon = config.icon;

  if (variant === 'compact') {
    return (
      <div
        onClick={onClick}
        className={`card p-4 border-l-4 ${config.borderColor} card-hover cursor-pointer`}
      >
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-lg ${config.bgColor}`}>
            <Icon size={16} className={config.iconColor} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-body-sm font-semibold text-neutral-950 truncate">
              {insight.title}
            </p>
            <p className="text-caption text-neutral-600 mt-1 line-clamp-1">
              {insight.summary}
            </p>
          </div>
          <ChevronRight size={16} className="text-neutral-400 flex-shrink-0" />
        </div>
      </div>
    );
  }

  if (variant === 'featured') {
    return (
      <div className={`card overflow-hidden border-l-4 ${config.borderColor}`}>
        {/* Header */}
        <div className="p-6 pb-4">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-xl ${config.bgColor}`}>
                <Icon size={20} className={config.iconColor} />
              </div>
              <div>
                <span className={`text-caption font-semibold uppercase tracking-wide ${config.iconColor}`}>
                  {config.label}
                </span>
                <h3 className="text-heading-md text-neutral-950 mt-0.5">
                  {insight.title}
                </h3>
              </div>
            </div>
            <button className="p-2 hover:bg-neutral-100 rounded-lg transition-colors">
              <Bookmark size={18} className="text-neutral-400" />
            </button>
          </div>

          <p className="text-body-md text-neutral-700 leading-relaxed">
            {insight.description}
          </p>
        </div>

        {/* Key Factors */}
        {insight.keyFactors.length > 0 && (
          <div className="px-6 pb-4">
            <p className="text-caption font-semibold text-neutral-600 uppercase tracking-wide mb-3">
              Key Factors
            </p>
            <ul className="space-y-2">
              {insight.keyFactors.map((factor, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-neutral-400 mt-2 flex-shrink-0" />
                  <span className="text-body-sm text-neutral-700">{factor}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Actions */}
        <div className="px-6 py-4 bg-neutral-50 border-t border-neutral-100 flex items-center gap-3">
          <button
            onClick={onClick}
            className="btn-secondary text-body-sm"
          >
            {insight.actionLabel || 'See Details'}
            <ChevronRight size={16} className="ml-1" />
          </button>
          {onAskAI && (
            <button
              onClick={onAskAI}
              className="btn-ghost text-body-sm text-primary-500"
            >
              Ask AI about this
            </button>
          )}
        </div>
      </div>
    );
  }

  // Default variant
  return (
    <div
      onClick={onClick}
      className={`card p-5 border-l-4 ${config.borderColor} ${onClick ? 'card-hover cursor-pointer' : ''}`}
    >
      <div className="flex items-start gap-4">
        <div className={`p-2.5 rounded-xl ${config.bgColor} flex-shrink-0`}>
          <Icon size={20} className={config.iconColor} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4">
            <div>
              <span className={`text-caption font-semibold uppercase tracking-wide ${config.iconColor}`}>
                {config.label}
              </span>
              <h4 className="text-heading-sm text-neutral-950 mt-1">
                {insight.title}
              </h4>
            </div>
            <ChevronRight size={18} className="text-neutral-400 flex-shrink-0 mt-1" />
          </div>
          <p className="text-body-sm text-neutral-600 mt-2 line-clamp-2">
            {insight.summary}
          </p>
          {insight.keyFactors.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {insight.keyFactors.slice(0, 2).map((factor, index) => (
                <span
                  key={index}
                  className="text-caption text-neutral-600 bg-neutral-100 px-2 py-1 rounded-md"
                >
                  {factor.length > 40 ? factor.substring(0, 40) + '...' : factor}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
