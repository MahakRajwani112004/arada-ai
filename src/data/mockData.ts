import type { KPI, Insight, ChatMessage } from '../types';

export const mockKPIs: KPI[] = [
  {
    id: 'net-sales',
    name: 'Net Sales',
    value: 5372431018,
    formattedValue: 'AED 5.37B',
    change: 18.2,
    changeType: 'increase',
    trend: [4.2, 4.5, 4.8, 5.0, 5.1, 5.2, 5.37],
    unit: 'AED',
    description: 'Total net sales across all developments',
  },
  {
    id: 'bookings',
    name: 'Active Bookings',
    value: 491,
    formattedValue: '491',
    change: -3.2,
    changeType: 'decrease',
    trend: [520, 515, 508, 502, 498, 495, 491],
    description: 'Total active bookings (excludes cancelled)',
  },
  {
    id: 'cancellations',
    name: 'Cancellations',
    value: 509,
    formattedValue: '509',
    change: 50.9,
    changeType: 'increase',
    trend: [380, 410, 440, 465, 485, 498, 509],
    description: '50.9% cancellation rate - Critical!',
  },
  {
    id: 'collection-rate',
    name: 'Collection Rate',
    value: 37.2,
    formattedValue: '37.2%',
    change: 2.8,
    changeType: 'increase',
    trend: [32, 33, 34, 35, 36, 36.5, 37.2],
    unit: '%',
    description: 'Amount realized vs net sales value',
  },
  {
    id: 'realized',
    name: 'Amount Realized',
    value: 1999850860,
    formattedValue: 'AED 2.0B',
    change: 8.5,
    changeType: 'increase',
    trend: [1.6, 1.7, 1.75, 1.82, 1.88, 1.94, 2.0],
    unit: 'AED',
    description: 'Total cash collected from customers',
  },
  {
    id: 'avg-deal-size',
    name: 'Avg Deal Size',
    value: 5372431,
    formattedValue: 'AED 5.37M',
    change: 4.2,
    changeType: 'increase',
    trend: [4.9, 5.0, 5.1, 5.2, 5.25, 5.3, 5.37],
    unit: 'AED',
    description: 'Average transaction value per unit',
  },
];

export const mockInsights: Insight[] = [
  {
    id: 'insight-1',
    type: 'alert',
    priority: 'high',
    title: 'Critical: 50.9% Cancellation Rate',
    summary: '509 of 1,000 bookings cancelled. This is severely impacting net sales realization.',
    description: 'The cancellation rate has reached a critical level at 50.9%. Analysis indicates this may be driven by market volatility, customer financing challenges, and changing buyer sentiment. Immediate action required to understand root causes and implement retention strategies.',
    relatedKPIs: ['cancellations', 'net-sales', 'bookings'],
    keyFactors: [
      '509 cancellations out of 1,000 total bookings',
      'Broker deals (51.3%) showing higher cancellation tendency',
      'Need urgent customer retention program',
    ],
    timestamp: new Date(),
    actionLabel: 'View Cancellation Analysis',
  },
  {
    id: 'insight-2',
    type: 'opportunity',
    priority: 'high',
    title: 'Emaar Beachfront Premium Performance',
    summary: 'Highest avg price at AED 7.2M with strong demand. 168 units contributing AED 1.2B.',
    description: 'Emaar Beachfront commands premium pricing at AED 7.2M average, significantly higher than other developments. This waterfront location shows strong investor confidence despite market challenges.',
    relatedKPIs: ['net-sales', 'avg-deal-size'],
    keyFactors: [
      'Premium waterfront location driving value',
      'AED 1.2B from 168 units (22% of total sales)',
      'International buyer preference for beachfront',
    ],
    timestamp: new Date(),
    actionLabel: 'Explore Opportunity',
  },
  {
    id: 'insight-3',
    type: 'trend',
    priority: 'medium',
    title: 'Q4 Booking Surge Pattern',
    summary: 'November-December showing strongest bookings (104 each). Plan campaigns accordingly.',
    description: 'Historical booking data shows clear seasonality with Q4 (Oct-Dec) being the strongest period. November and December each recorded 104 bookings. This correlates with year-end investment decisions and Dubai property expos.',
    relatedKPIs: ['bookings', 'net-sales'],
    keyFactors: [
      'Q4 accounts for 35% of annual bookings',
      'Year-end investment cycle driving demand',
      'Property expo season correlation',
    ],
    timestamp: new Date(),
    actionLabel: 'View Seasonal Analysis',
  },
  {
    id: 'insight-4',
    type: 'info',
    priority: 'medium',
    title: 'Indian & UK Buyers Dominate',
    summary: 'India (18.9%) and UK (18.7%) are top buyer nationalities. Tailor marketing accordingly.',
    description: 'Buyer nationality analysis reveals strong international demand, with Indian nationals leading at 18.9%, followed by UK (18.7%), Russia (17.2%), UAE locals (15.7%), and China (15%). This diversity requires multi-market marketing strategies.',
    relatedKPIs: ['bookings', 'net-sales'],
    keyFactors: [
      'South Asian market (India + Pakistan) = 33.4%',
      'European market (UK + Russia) = 35.9%',
      'UAE local market only 15.7%',
    ],
    timestamp: new Date(),
    actionLabel: 'Buyer Demographics',
  },
];

export const mockChatMessages: ChatMessage[] = [
  {
    id: '1',
    role: 'assistant',
    content: 'Hello! I\'m your AI analytics assistant for Dubai real estate portfolio. I can help you analyze DAMAC and Emaar properties, understand buyer trends, and track sales performance. What would you like to explore?',
    timestamp: new Date(Date.now() - 60000),
    followUpQuestions: [
      'Why is the cancellation rate so high?',
      'Which development is performing best?',
      'Show buyer nationality breakdown',
    ],
  },
];

export const suggestedQuestions = [
  'Why is the 50.9% cancellation rate so high?',
  'Compare DAMAC vs Emaar performance',
  'Which nationality buys the most?',
  'Show me collection rate by project',
  'What-if: Reduce cancellation by 20%',
  'Which unit types sell fastest?',
];

export const projectsData = [
  { name: 'Emaar Beachfront', sales: 168, netSales: 1215, avgPrice: 7.23, change: 12.5 },
  { name: 'Downtown Dubai', sales: 160, netSales: 1056, avgPrice: 6.60, change: 8.2 },
  { name: 'Dubai Hills Estate', sales: 170, netSales: 940, avgPrice: 5.53, change: 5.8 },
  { name: 'DAMAC Bay', sales: 172, netSales: 832, avgPrice: 4.83, change: 3.2 },
  { name: 'DAMAC Hills', sales: 170, netSales: 728, avgPrice: 4.28, change: -1.5 },
  { name: 'DAMAC Lagoons', sales: 160, netSales: 602, avgPrice: 3.76, change: -2.8 },
];

export const monthlyTrendData = [
  { month: 'Jan', netSales: 420, bookings: 76, cancellations: 38 },
  { month: 'Feb', netSales: 435, bookings: 77, cancellations: 41 },
  { month: 'Mar', netSales: 410, bookings: 73, cancellations: 35 },
  { month: 'Apr', netSales: 365, bookings: 63, cancellations: 32 },
  { month: 'May', netSales: 425, bookings: 73, cancellations: 38 },
  { month: 'Jun', netSales: 395, bookings: 68, cancellations: 36 },
  { month: 'Jul', netSales: 545, bookings: 99, cancellations: 52 },
  { month: 'Aug', netSales: 480, bookings: 84, cancellations: 44 },
  { month: 'Sep', netSales: 515, bookings: 91, cancellations: 48 },
  { month: 'Oct', netSales: 498, bookings: 88, cancellations: 45 },
  { month: 'Nov', netSales: 580, bookings: 104, cancellations: 50 },
  { month: 'Dec', netSales: 590, bookings: 104, cancellations: 50 },
];

export const nationalityData = [
  { name: 'India', count: 189, percentage: 18.9 },
  { name: 'UK', count: 187, percentage: 18.7 },
  { name: 'Russia', count: 172, percentage: 17.2 },
  { name: 'UAE', count: 157, percentage: 15.7 },
  { name: 'China', count: 150, percentage: 15.0 },
  { name: 'Pakistan', count: 145, percentage: 14.5 },
];

export const unitTypeData = [
  { name: '1BR', units: 172, avgSqft: 2768, totalSales: 963, avgPrice: 5.60 },
  { name: '2BR', units: 167, avgSqft: 2937, totalSales: 954, avgPrice: 5.71 },
  { name: 'Townhouse', units: 173, avgSqft: 2704, totalSales: 913, avgPrice: 5.28 },
  { name: 'Studio', units: 159, avgSqft: 2827, totalSales: 903, avgPrice: 5.68 },
  { name: 'Villa', units: 165, avgSqft: 2470, totalSales: 844, avgPrice: 5.11 },
  { name: '3BR', units: 164, avgSqft: 2518, totalSales: 795, avgPrice: 4.85 },
];

export const leadSourceData = [
  { name: 'Broker Network', count: 338, percentage: 33.8 },
  { name: 'Digital', count: 332, percentage: 33.2 },
  { name: 'Event', count: 330, percentage: 33.0 },
];

export const dealTypeData = [
  { name: 'Broker', count: 513, percentage: 51.3 },
  { name: 'Direct', count: 487, percentage: 48.7 },
];

export const statusData = {
  booking: [
    { name: 'Cancelled', count: 509, percentage: 50.9 },
    { name: 'Booked', count: 491, percentage: 49.1 },
  ],
  unit: [
    { name: 'Available', count: 363, percentage: 36.3 },
    { name: 'Blocked', count: 324, percentage: 32.4 },
    { name: 'Sold', count: 313, percentage: 31.3 },
  ],
};
