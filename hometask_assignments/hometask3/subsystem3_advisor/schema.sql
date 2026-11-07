CREATE DATABASE IF NOT EXISTS energy_advisor;
USE energy_advisor;

CREATE TABLE IF NOT EXISTS energy_summary (
    building_id     INT PRIMARY KEY,
    building        VARCHAR(100) NOT NULL,
    report_date     DATE NOT NULL,
    energy_kwh      DOUBLE NOT NULL CHECK (energy_kwh >= 0),
    cost_eur        DOUBLE NOT NULL CHECK (cost_eur >= 0),
    co2_kg          DOUBLE NOT NULL CHECK (co2_kg >= 0),
    after_hours_kwh DOUBLE NOT NULL,
    CHECK (after_hours_kwh >= 0 AND after_hours_kwh <= energy_kwh)
);

-- Synthetic daily summaries. Tariff: 0.30 EUR/kWh; emissions: 0.38 kg/kWh.
-- Existing records are preserved when this script is run again.
INSERT INTO energy_summary
    (building_id, building, report_date, energy_kwh, cost_eur, co2_kg, after_hours_kwh)
VALUES
    (1, 'Demo Home', '2016-12-01', 48.0, 14.40, 18.24, 0.0),
    (2, 'Demo Office', '2016-12-01', 192.0, 57.60, 72.96, 48.0)
ON DUPLICATE KEY UPDATE building_id = energy_summary.building_id;
