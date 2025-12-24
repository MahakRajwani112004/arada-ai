-- Arada Real Estate Analytics Database Schema
-- This table stores booking records for real estate analytics

-- Drop table if exists (for clean setup)
DROP TABLE IF EXISTS bookings;

-- Create bookings table with key columns for analytics
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,

    -- Location hierarchy
    development VARCHAR(100) NOT NULL,          -- Master Development (DAMAC Bay, Downtown Dubai, etc.)
    cluster VARCHAR(100),                       -- Cluster Name (Waterfront, Venice, etc.)
    building VARCHAR(100),                      -- Building Name

    -- Unit details
    unit_id VARCHAR(50),                        -- Unit identifier
    unit_type VARCHAR(50),                      -- Studio, 1BR, 2BR, 3BR, Townhouse, Villa
    area_sqft DECIMAL(10, 2),                   -- Total Saleable Area (Sqft)

    -- Pricing
    selling_price DECIMAL(15, 2),               -- Original Selling Price (AED)
    discount_amount DECIMAL(15, 2),             -- Discount Amount
    discount_percent DECIMAL(5, 2),             -- Discount %
    net_sale_value DECIMAL(15, 2),              -- Net Sale Value (AED) = Selling Price - Discount

    -- Payment terms
    dp_percent VARCHAR(10),                     -- Down Payment % (10%, 20%, 30%)
    dp_balance DECIMAL(15, 2),                  -- DP Balance remaining
    dp_received DECIMAL(15, 2),                 -- DP Received

    -- Collections
    total_received DECIMAL(15, 2),              -- Total Received (Realized + PDC)
    total_realized DECIMAL(15, 2),              -- Total Amount Realized
    realization_percent DECIMAL(5, 2),          -- Total Realized %
    pdcs_total DECIMAL(15, 2),                  -- PDCs Total Amount

    -- Dates
    booking_date DATE,                          -- Booking Date
    booking_month VARCHAR(20),                  -- Booking Month name
    ageing_days INTEGER,                        -- Days since booking
    handover_date DATE,                         -- Expected handover

    -- Status
    booking_status VARCHAR(50),                 -- Booked, Cancelled
    unit_status VARCHAR(50),                    -- Available, Blocked, etc.
    stage VARCHAR(50),                          -- Booked, Registered, Opportunity, etc.

    -- Sales attribution
    deal_type VARCHAR(50),                      -- Direct, Broker
    lead_source VARCHAR(50),                    -- Event, Digital, Broker Network, Direct
    lead_sub_source VARCHAR(100),               -- Sub-source details
    sales_executive VARCHAR(100),               -- Sales Executive name
    sales_manager VARCHAR(100),                 -- Sales Manager name
    sales_vp VARCHAR(100),                      -- Sales VP name
    broker_name VARCHAR(200),                   -- Broker company name

    -- Customer
    customer_code VARCHAR(50),                  -- Customer identifier
    nationality VARCHAR(100),                   -- P1 Nationality
    nationality_2 VARCHAR(100),                 -- P2 Nationality

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common query patterns
CREATE INDEX idx_bookings_development ON bookings(development);
CREATE INDEX idx_bookings_cluster ON bookings(cluster);
CREATE INDEX idx_bookings_unit_type ON bookings(unit_type);
CREATE INDEX idx_bookings_booking_date ON bookings(booking_date);
CREATE INDEX idx_bookings_booking_status ON bookings(booking_status);
CREATE INDEX idx_bookings_lead_source ON bookings(lead_source);
CREATE INDEX idx_bookings_nationality ON bookings(nationality);
CREATE INDEX idx_bookings_sales_vp ON bookings(sales_vp);
CREATE INDEX idx_bookings_dp_percent ON bookings(dp_percent);

-- Add comments for documentation
COMMENT ON TABLE bookings IS 'Real estate booking records for Arada analytics (1000 records, Aug 2021 - Dec 2025)';
COMMENT ON COLUMN bookings.development IS 'Master development: DAMAC Bay, DAMAC Hills, DAMAC Lagoons, Downtown Dubai, Dubai Hills Estate, Emaar Beachfront';
COMMENT ON COLUMN bookings.realization_percent IS 'Percentage of total value collected so far';
COMMENT ON COLUMN bookings.dp_percent IS 'Down payment tier: 10%, 20%, or 30%';
