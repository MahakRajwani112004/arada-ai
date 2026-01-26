// Comprehensive EDA Data for Real Estate Analytics

// ============================================
// RAW TRANSACTION DATA (1000 records simulated)
// ============================================

export interface Transaction {
  id: string;
  date: string;
  project: string;
  unitType: string;
  sqft: number;
  price: number;
  dpTier: string;
  nationality: string;
  dealType: string;
  leadSource: string;
  status: 'Booked' | 'Cancelled';
  collectionRate: number;
  daysToClose: number;
}

// Generate realistic transaction data
const projects = ['Emaar Beachfront', 'Downtown Dubai', 'Dubai Hills', 'DAMAC Bay', 'DAMAC Hills', 'DAMAC Lagoons'];
const unitTypes = ['Studio', '1BR', '2BR', '3BR', 'Townhouse', 'Villa'];
const nationalities = ['India', 'UK', 'Russia', 'UAE', 'China', 'Pakistan'];
const dpTiers = ['10%', '20%', '30%', '40%'];
const dealTypes = ['Direct', 'Broker'];
const leadSources = ['Digital', 'Broker Network', 'Event', 'Referral'];

// Project-specific price ranges (in millions AED)
const projectPriceRanges: Record<string, { min: number; max: number; cancelRate: number }> = {
  'Emaar Beachfront': { min: 5.5, max: 9.5, cancelRate: 0.35 },
  'Downtown Dubai': { min: 5.0, max: 8.5, cancelRate: 0.42 },
  'Dubai Hills': { min: 4.2, max: 7.0, cancelRate: 0.48 },
  'DAMAC Bay': { min: 3.5, max: 6.0, cancelRate: 0.55 },
  'DAMAC Hills': { min: 3.0, max: 5.5, cancelRate: 0.58 },
  'DAMAC Lagoons': { min: 2.5, max: 5.0, cancelRate: 0.62 },
};

// Generate 1000 transactions
export const rawTransactions: Transaction[] = Array.from({ length: 1000 }, (_, i) => {
  const project = projects[Math.floor(Math.random() * projects.length)];
  const priceRange = projectPriceRanges[project];
  const price = priceRange.min + Math.random() * (priceRange.max - priceRange.min);
  const isCancelled = Math.random() < priceRange.cancelRate;

  return {
    id: `TXN-${String(i + 1).padStart(4, '0')}`,
    date: `2024-${String(Math.floor(Math.random() * 12) + 1).padStart(2, '0')}-${String(Math.floor(Math.random() * 28) + 1).padStart(2, '0')}`,
    project,
    unitType: unitTypes[Math.floor(Math.random() * unitTypes.length)],
    sqft: 800 + Math.floor(Math.random() * 3500),
    price: Math.round(price * 1000000),
    dpTier: dpTiers[Math.floor(Math.random() * dpTiers.length)],
    nationality: nationalities[Math.floor(Math.random() * nationalities.length)],
    dealType: dealTypes[Math.floor(Math.random() * dealTypes.length)],
    leadSource: leadSources[Math.floor(Math.random() * leadSources.length)],
    status: isCancelled ? 'Cancelled' : 'Booked',
    collectionRate: isCancelled ? 0 : 20 + Math.floor(Math.random() * 60),
    daysToClose: 15 + Math.floor(Math.random() * 90),
  };
});

// ============================================
// DISTRIBUTION DATA
// ============================================

// Price Distribution (histogram bins)
export const priceDistribution = [
  { range: '2-3M', count: 85, percentage: 8.5 },
  { range: '3-4M', count: 156, percentage: 15.6 },
  { range: '4-5M', count: 234, percentage: 23.4 },
  { range: '5-6M', count: 267, percentage: 26.7 },
  { range: '6-7M', count: 145, percentage: 14.5 },
  { range: '7-8M', count: 78, percentage: 7.8 },
  { range: '8-9M', count: 28, percentage: 2.8 },
  { range: '9M+', count: 7, percentage: 0.7 },
];

// SqFt Distribution
export const sqftDistribution = [
  { range: '500-1000', count: 145, percentage: 14.5 },
  { range: '1000-1500', count: 198, percentage: 19.8 },
  { range: '1500-2000', count: 234, percentage: 23.4 },
  { range: '2000-2500', count: 187, percentage: 18.7 },
  { range: '2500-3000', count: 134, percentage: 13.4 },
  { range: '3000-3500', count: 67, percentage: 6.7 },
  { range: '3500+', count: 35, percentage: 3.5 },
];

// Box Plot Data (Price by Project)
export const boxPlotData = [
  { project: 'Emaar Beachfront', min: 5.5, q1: 6.2, median: 7.2, q3: 8.1, max: 9.5, outliers: [9.8, 10.2] },
  { project: 'Downtown Dubai', min: 5.0, q1: 5.8, median: 6.6, q3: 7.4, max: 8.5, outliers: [8.9] },
  { project: 'Dubai Hills', min: 4.2, q1: 4.9, median: 5.5, q3: 6.2, max: 7.0, outliers: [] },
  { project: 'DAMAC Bay', min: 3.5, q1: 4.1, median: 4.8, q3: 5.4, max: 6.0, outliers: [6.3] },
  { project: 'DAMAC Hills', min: 3.0, q1: 3.6, median: 4.3, q3: 4.9, max: 5.5, outliers: [] },
  { project: 'DAMAC Lagoons', min: 2.5, q1: 3.1, median: 3.8, q3: 4.4, max: 5.0, outliers: [5.3] },
];

// Days to Close Distribution
export const daysToCloseDistribution = [
  { range: '0-15', count: 89, percentage: 8.9 },
  { range: '16-30', count: 234, percentage: 23.4 },
  { range: '31-45', count: 298, percentage: 29.8 },
  { range: '46-60', count: 187, percentage: 18.7 },
  { range: '61-75', count: 112, percentage: 11.2 },
  { range: '76-90', count: 56, percentage: 5.6 },
  { range: '90+', count: 24, percentage: 2.4 },
];

// ============================================
// CORRELATION MATRIX DATA
// ============================================

export const correlationMatrix = {
  variables: ['Price', 'SqFt', 'DP Tier', 'Collection Rate', 'Days to Close', 'Cancellation'],
  data: [
    // Price correlations
    [1.00, 0.72, 0.45, 0.38, -0.22, -0.34],
    // SqFt correlations
    [0.72, 1.00, 0.28, 0.31, -0.15, -0.28],
    // DP Tier correlations
    [0.45, 0.28, 1.00, 0.52, -0.38, -0.48],
    // Collection Rate correlations
    [0.38, 0.31, 0.52, 1.00, -0.45, -0.62],
    // Days to Close correlations
    [-0.22, -0.15, -0.38, -0.45, 1.00, 0.35],
    // Cancellation correlations
    [-0.34, -0.28, -0.48, -0.62, 0.35, 1.00],
  ],
};

// Cross-tabulation: Cancellation Rate by Project x DP Tier
export const cancellationCrossTab = {
  projects: ['Emaar Beachfront', 'Downtown Dubai', 'Dubai Hills', 'DAMAC Bay', 'DAMAC Hills', 'DAMAC Lagoons'],
  dpTiers: ['10%', '20%', '30%', '40%'],
  data: [
    // Emaar Beachfront
    [42, 35, 30, 28],
    // Downtown Dubai
    [48, 42, 38, 35],
    // Dubai Hills
    [55, 48, 42, 40],
    // DAMAC Bay
    [62, 55, 48, 45],
    // DAMAC Hills
    [65, 58, 52, 48],
    // DAMAC Lagoons
    [68, 62, 55, 52],
  ],
};

// Cancellation by Deal Type x Nationality
export const dealNationalityCrossTab = {
  nationalities: ['India', 'UK', 'Russia', 'UAE', 'China', 'Pakistan'],
  data: [
    { nationality: 'India', direct: 42, broker: 58, total: 51 },
    { nationality: 'UK', direct: 38, broker: 52, total: 46 },
    { nationality: 'Russia', direct: 35, broker: 48, total: 42 },
    { nationality: 'UAE', direct: 32, broker: 45, total: 39 },
    { nationality: 'China', direct: 48, broker: 62, total: 56 },
    { nationality: 'Pakistan', direct: 52, broker: 65, total: 59 },
  ],
};

// ============================================
// TREND ANALYSIS DATA
// ============================================

export const monthlyTrend = [
  { month: 'Jan 2024', bookings: 76, cancellations: 38, netSales: 420, collection: 156, cancelRate: 50.0 },
  { month: 'Feb 2024', bookings: 77, cancellations: 41, netSales: 435, collection: 162, cancelRate: 53.2 },
  { month: 'Mar 2024', bookings: 73, cancellations: 35, netSales: 410, collection: 152, cancelRate: 47.9 },
  { month: 'Apr 2024', bookings: 63, cancellations: 32, netSales: 365, collection: 136, cancelRate: 50.8 },
  { month: 'May 2024', bookings: 73, cancellations: 38, netSales: 425, collection: 158, cancelRate: 52.1 },
  { month: 'Jun 2024', bookings: 68, cancellations: 36, netSales: 395, collection: 147, cancelRate: 52.9 },
  { month: 'Jul 2024', bookings: 99, cancellations: 52, netSales: 545, collection: 203, cancelRate: 52.5 },
  { month: 'Aug 2024', bookings: 84, cancellations: 44, netSales: 480, collection: 178, cancelRate: 52.4 },
  { month: 'Sep 2024', bookings: 91, cancellations: 48, netSales: 515, collection: 191, cancelRate: 52.7 },
  { month: 'Oct 2024', bookings: 88, cancellations: 45, netSales: 498, collection: 185, cancelRate: 51.1 },
  { month: 'Nov 2024', bookings: 104, cancellations: 50, netSales: 580, collection: 216, cancelRate: 48.1 },
  { month: 'Dec 2024', bookings: 104, cancellations: 50, netSales: 590, collection: 219, cancelRate: 48.1 },
];

// Forecast data (next 6 months)
export const forecastTrend = [
  { month: 'Jan 2025', bookings: 98, bookingsLow: 85, bookingsHigh: 112, cancelRate: 47.5, cancelRateLow: 44, cancelRateHigh: 51 },
  { month: 'Feb 2025', bookings: 95, bookingsLow: 82, bookingsHigh: 108, cancelRate: 46.8, cancelRateLow: 43, cancelRateHigh: 50 },
  { month: 'Mar 2025', bookings: 102, bookingsLow: 88, bookingsHigh: 116, cancelRate: 45.5, cancelRateLow: 42, cancelRateHigh: 49 },
  { month: 'Apr 2025', bookings: 88, bookingsLow: 75, bookingsHigh: 101, cancelRate: 46.2, cancelRateLow: 43, cancelRateHigh: 50 },
  { month: 'May 2025', bookings: 94, bookingsLow: 80, bookingsHigh: 108, cancelRate: 45.0, cancelRateLow: 41, cancelRateHigh: 49 },
  { month: 'Jun 2025', bookings: 90, bookingsLow: 76, bookingsHigh: 104, cancelRate: 44.5, cancelRateLow: 40, cancelRateHigh: 48 },
];

// Weekly trend for recent 12 weeks
export const weeklyTrend = [
  { week: 'W40', bookings: 22, cancellations: 11, conversion: 50.0 },
  { week: 'W41', bookings: 24, cancellations: 12, conversion: 50.0 },
  { week: 'W42', bookings: 21, cancellations: 10, conversion: 52.4 },
  { week: 'W43', bookings: 21, cancellations: 12, conversion: 42.9 },
  { week: 'W44', bookings: 26, cancellations: 12, conversion: 53.8 },
  { week: 'W45', bookings: 25, cancellations: 13, conversion: 48.0 },
  { week: 'W46', bookings: 28, cancellations: 12, conversion: 57.1 },
  { week: 'W47', bookings: 25, cancellations: 13, conversion: 48.0 },
  { week: 'W48', bookings: 26, cancellations: 12, conversion: 53.8 },
  { week: 'W49', bookings: 27, cancellations: 14, conversion: 48.1 },
  { week: 'W50', bookings: 26, cancellations: 12, conversion: 53.8 },
  { week: 'W51', bookings: 25, cancellations: 12, conversion: 52.0 },
];

// ============================================
// DETAILED TABLE DATA
// ============================================

export const projectDetailedStats = [
  {
    project: 'Emaar Beachfront',
    totalUnits: 168,
    netSales: 1215,
    avgPrice: 7.23,
    cancelRate: 35.1,
    collectionRate: 52.3,
    avgDaysToClose: 28,
    topNationality: 'UK',
    topUnitType: '2BR',
    yoyChange: 12.5,
    status: 'outperforming',
  },
  {
    project: 'Downtown Dubai',
    totalUnits: 160,
    netSales: 1056,
    avgPrice: 6.60,
    cancelRate: 42.3,
    collectionRate: 45.8,
    avgDaysToClose: 32,
    topNationality: 'India',
    topUnitType: '1BR',
    yoyChange: 8.2,
    status: 'stable',
  },
  {
    project: 'Dubai Hills',
    totalUnits: 170,
    netSales: 940,
    avgPrice: 5.53,
    cancelRate: 48.5,
    collectionRate: 38.2,
    avgDaysToClose: 38,
    topNationality: 'India',
    topUnitType: 'Villa',
    yoyChange: 5.8,
    status: 'stable',
  },
  {
    project: 'DAMAC Bay',
    totalUnits: 172,
    netSales: 832,
    avgPrice: 4.83,
    cancelRate: 55.2,
    collectionRate: 32.5,
    avgDaysToClose: 42,
    topNationality: 'Russia',
    topUnitType: 'Studio',
    yoyChange: 3.2,
    status: 'at_risk',
  },
  {
    project: 'DAMAC Hills',
    totalUnits: 170,
    netSales: 728,
    avgPrice: 4.28,
    cancelRate: 58.1,
    collectionRate: 28.4,
    avgDaysToClose: 48,
    topNationality: 'Pakistan',
    topUnitType: 'Townhouse',
    yoyChange: -1.5,
    status: 'underperforming',
  },
  {
    project: 'DAMAC Lagoons',
    totalUnits: 160,
    netSales: 602,
    avgPrice: 3.76,
    cancelRate: 62.3,
    collectionRate: 25.2,
    avgDaysToClose: 55,
    topNationality: 'China',
    topUnitType: '3BR',
    yoyChange: -2.8,
    status: 'critical',
  },
];

export const unitTypeDetailedStats = [
  { unitType: 'Studio', count: 159, avgPrice: 5.68, avgSqft: 650, cancelRate: 45.2, collectionRate: 42.5, topProject: 'DAMAC Bay' },
  { unitType: '1BR', count: 172, avgPrice: 5.60, avgSqft: 950, cancelRate: 48.5, collectionRate: 40.2, topProject: 'Downtown Dubai' },
  { unitType: '2BR', count: 167, avgPrice: 5.71, avgSqft: 1450, cancelRate: 54.2, collectionRate: 38.5, topProject: 'Emaar Beachfront' },
  { unitType: '3BR', count: 164, avgPrice: 4.85, avgSqft: 2100, cancelRate: 52.8, collectionRate: 35.2, topProject: 'Dubai Hills' },
  { unitType: 'Townhouse', count: 173, avgPrice: 5.28, avgSqft: 2800, cancelRate: 50.5, collectionRate: 36.8, topProject: 'DAMAC Hills' },
  { unitType: 'Villa', count: 165, avgPrice: 5.11, avgSqft: 3500, cancelRate: 48.2, collectionRate: 38.5, topProject: 'Dubai Hills' },
];

export const nationalityDetailedStats = [
  { nationality: 'India', count: 189, percentage: 18.9, avgPrice: 5.2, cancelRate: 51.0, collectionRate: 38.5, topProject: 'Downtown Dubai', topUnitType: '1BR' },
  { nationality: 'UK', count: 187, percentage: 18.7, avgPrice: 6.8, cancelRate: 42.0, collectionRate: 48.2, topProject: 'Emaar Beachfront', topUnitType: '2BR' },
  { nationality: 'Russia', count: 172, percentage: 17.2, avgPrice: 5.8, cancelRate: 38.5, collectionRate: 52.5, topProject: 'Downtown Dubai', topUnitType: 'Studio' },
  { nationality: 'UAE', count: 157, percentage: 15.7, avgPrice: 6.2, cancelRate: 35.2, collectionRate: 55.8, topProject: 'Emaar Beachfront', topUnitType: 'Villa' },
  { nationality: 'China', count: 150, percentage: 15.0, avgPrice: 4.5, cancelRate: 58.5, collectionRate: 32.2, topProject: 'DAMAC Lagoons', topUnitType: '3BR' },
  { nationality: 'Pakistan', count: 145, percentage: 14.5, avgPrice: 4.2, cancelRate: 62.0, collectionRate: 28.5, topProject: 'DAMAC Hills', topUnitType: 'Townhouse' },
];

// ============================================
// STATISTICAL SUMMARY
// ============================================

export const statisticalSummary = {
  price: {
    mean: 5.37,
    median: 5.15,
    std: 1.42,
    min: 2.5,
    max: 10.2,
    q1: 4.2,
    q3: 6.4,
    skewness: 0.45,
    kurtosis: 2.8,
  },
  sqft: {
    mean: 1850,
    median: 1720,
    std: 820,
    min: 500,
    max: 4200,
    q1: 1200,
    q3: 2400,
  },
  daysToClose: {
    mean: 42,
    median: 38,
    std: 18,
    min: 7,
    max: 105,
    q1: 28,
    q3: 55,
  },
  collectionRate: {
    mean: 37.2,
    median: 35.5,
    std: 15.8,
    min: 0,
    max: 85,
    q1: 25,
    q3: 48,
  },
};

// ============================================
// ANOMALY DETECTION DATA
// ============================================

export const anomalies = [
  {
    id: 1,
    type: 'critical',
    metric: 'Cancellation Rate',
    value: 50.9,
    expected: 15,
    deviation: '+239%',
    description: 'Cancellation rate 3x industry average',
    affectedSegments: ['DAMAC Lagoons (62%)', 'DAMAC Hills (58%)', 'Broker Channel (54%)'],
    recommendedAction: 'Implement customer retention program immediately',
  },
  {
    id: 2,
    type: 'warning',
    metric: 'Collection Rate',
    value: 37.2,
    expected: 60,
    deviation: '-38%',
    description: 'Collection significantly below target',
    affectedSegments: ['DAMAC Lagoons (25%)', 'DAMAC Hills (28%)', 'Pakistan buyers (28%)'],
    recommendedAction: 'Accelerate collection on overdue accounts',
  },
  {
    id: 3,
    type: 'opportunity',
    metric: 'Premium Segment',
    value: 7.2,
    expected: 5.37,
    deviation: '+34%',
    description: 'Emaar Beachfront commanding significant premium',
    affectedSegments: ['UK buyers (+38%)', 'UAE buyers (+28%)', '2BR units (+24%)'],
    recommendedAction: 'Increase premium inventory allocation',
  },
  {
    id: 4,
    type: 'pattern',
    metric: 'Seasonal Spike',
    value: 104,
    expected: 82,
    deviation: '+27%',
    description: 'Q4 showing 27% higher bookings than average',
    affectedSegments: ['November (104)', 'December (104)', 'July (99)'],
    recommendedAction: 'Align marketing campaigns with Q4 seasonality',
  },
];

// ============================================
// KEY INSIGHTS FOR AI SUMMARY
// ============================================

export const keyInsights = [
  {
    category: 'Risk',
    title: 'DP Tier strongly predicts cancellation',
    insight: '10% DP tier shows 68% cancellation vs 28% for 40% tier. Each 10% DP increase reduces cancellation by ~12pp.',
    confidence: 94,
    actionable: true,
  },
  {
    category: 'Correlation',
    title: 'Broker deals have higher cancellation',
    insight: 'Broker deals show 54% cancellation vs 47% direct. Correlation of 0.48 between deal type and cancellation.',
    confidence: 91,
  },
  {
    category: 'Opportunity',
    title: 'Premium segment outperforms on all metrics',
    insight: 'Emaar Beachfront: 35% cancellation, 52% collection, AED 7.2M avg. Best performing across all KPIs.',
    confidence: 96,
    actionable: true,
  },
  {
    category: 'Pattern',
    title: 'Nationality impacts cancellation significantly',
    insight: 'UAE locals (35%), Russia (38%) vs China (58%), Pakistan (62%). Consider nationality-specific retention strategies.',
    confidence: 88,
  },
  {
    category: 'Trend',
    title: 'Q4 seasonality is predictable',
    insight: 'Oct-Dec accounts for 35% of annual bookings. Plan marketing budget and inventory accordingly.',
    confidence: 92,
  },
];
