// KPI Types
export interface KPI {
  id: string;
  name: string;
  value: number;
  formattedValue: string;
  change: number;
  changeType: 'increase' | 'decrease' | 'neutral';
  trend: number[];
  unit?: string;
  description?: string;
}

// Insight Types
export type InsightType = 'alert' | 'opportunity' | 'info' | 'trend';
export type InsightPriority = 'high' | 'medium' | 'low';

export interface Insight {
  id: string;
  type: InsightType;
  priority: InsightPriority;
  title: string;
  summary: string;
  description: string;
  relatedKPIs: string[];
  keyFactors: string[];
  timestamp: Date;
  actionLabel?: string;
}

// Chart Types
export interface ChartDataPoint {
  label: string;
  value: number;
  category?: string;
}

export interface TimeSeriesData {
  date: string;
  value: number;
  category?: string;
}

// Chat Types
export type MessageRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  chart?: ChartConfig;
  insights?: string[];
  followUpQuestions?: string[];
}

export interface ChartConfig {
  type: 'line' | 'bar' | 'pie' | 'area';
  title: string;
  data: ChartDataPoint[] | TimeSeriesData[];
}

// Navigation Types
export interface NavItem {
  id: string;
  label: string;
  icon: string;
  path: string;
  badge?: number;
}

// Filter Types
export interface DateRange {
  start: Date;
  end: Date;
}

export interface FilterState {
  dateRange: DateRange;
  regions: string[];
  projects: string[];
  kpis: string[];
}
