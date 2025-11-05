-- ============================================================================
-- Supabase Database Setup for Parking Features Transformation
-- ============================================================================
-- This script creates a dedicated schema and table for storing
-- transformed parking data from the collector-service
-- ============================================================================

-- Create dedicated schema for parking data
CREATE SCHEMA IF NOT EXISTS parking;

-- Drop existing table if present (for clean setup)
DROP TABLE IF EXISTS parking.transformed_parking_features CASCADE;

-- ============================================================================
-- Main Table: transformed_parking_features
-- ============================================================================
-- Stores transformed parking data with time-based features and duration estimates

CREATE TABLE parking.transformed_parking_features (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Record Identification
    "ID" INTEGER,
    "SystemCodeNumber" VARCHAR(100),
    
    -- Location Information
    "Latitude" DECIMAL(10, 8) NOT NULL,
    "Longitude" DECIMAL(11, 8) NOT NULL,
    
    -- Parking Capacity & Occupancy
    "Capacity" INTEGER,
    "Occupancy" INTEGER,
    "QueueLength" INTEGER,
    
    -- Vehicle & Context
    "VehicleType" VARCHAR(50),
    "TrafficConditionNearby" VARCHAR(50),
    "IsSpecialDay" BOOLEAN DEFAULT FALSE,
    
    -- Timestamps (UTC and IST)
    "Timestamp" TIMESTAMP NOT NULL,
    "Timestamp_WIB" TIMESTAMP,  -- India Standard Time (IST)
    
    -- Time Features
    "Hour" INTEGER CHECK ("Hour" BETWEEN 0 AND 23),
    "DayOfWeek" INTEGER CHECK ("DayOfWeek" BETWEEN 0 AND 6),  -- 0=Monday, 6=Sunday
    "DayName" VARCHAR(20),
    "IsWeekend" INTEGER CHECK ("IsWeekend" IN (0, 1)),
    "IsHoliday" INTEGER CHECK ("IsHoliday" IN (0, 1)),
    "TimeCategory" VARCHAR(20) CHECK ("TimeCategory" IN ('Morning', 'Afternoon', 'Evening', 'Night')),
    
    -- Duration Features (in minutes)
    "Duration_Minutes" INTEGER,
    "EstimatedDuration_Minutes" INTEGER,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
-- ============================================================================
-- Trigger for Automatic Updated_at Timestamp
-- ============================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION parking.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to call the function before each update
CREATE TRIGGER update_parking_features_updated_at
    BEFORE UPDATE ON parking.transformed_parking_features
    FOR EACH ROW
    EXECUTE FUNCTION parking.update_updated_at_column();
