-- Same four tables as the capstone (building -> zone -> meter -> reading)
-- To run once inside the MySQL shell:  SOURCE <path>/schema.sql;
CREATE DATABASE IF NOT EXISTS energy_hometask;
USE energy_hometask;
 
DROP TABLE IF EXISTS reading;
DROP TABLE IF EXISTS meter;
DROP TABLE IF EXISTS zone;
DROP TABLE IF EXISTS building;
 
CREATE TABLE building (
    id            INT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL UNIQUE,
    type          VARCHAR(20)  NOT NULL,
    floor_area_m2 DOUBLE       NOT NULL CHECK (floor_area_m2 > 0)
);
 
CREATE TABLE zone (
    id          INT PRIMARY KEY,
    building_id INT          NOT NULL,
    name        VARCHAR(100) NOT NULL,
    FOREIGN KEY (building_id) REFERENCES building(id),
    UNIQUE (building_id, name)
);
 
CREATE TABLE meter (
    id      INT PRIMARY KEY,
    zone_id INT          NOT NULL,
    kind    VARCHAR(30)  NOT NULL,
    unit    VARCHAR(10)  NOT NULL,
    source  VARCHAR(100) NOT NULL DEFAULT '',
    FOREIGN KEY (zone_id) REFERENCES zone(id)
);
 
CREATE TABLE reading (
    meter_id INT      NOT NULL,
    ts_utc   DATETIME NOT NULL,
    value    DOUBLE   NOT NULL,
    PRIMARY KEY (meter_id, ts_utc),        -- one value per meter per time: no duplicates
    FOREIGN KEY (meter_id) REFERENCES meter(id)
);
 
-- the six buildings from config.toml (floor areas are our assumptions, as in the capstone)
INSERT INTO building VALUES
    (1, 'Home 1', 'home', 140), (2, 'Home 3', 'home', 120), (3, 'Home 4', 'home', 160),
    (4, 'Business 1', 'business', 2500), (5, 'Business 3', 'business', 6000),
    (6, 'Public 1', 'public', 800);
 
-- one zone "Whole building" and one electricity meter per building
INSERT INTO zone VALUES
    (1, 1, 'Whole building'), (2, 2, 'Whole building'), (3, 3, 'Whole building'),
    (4, 4, 'Whole building'), (5, 5, 'Whole building'), (6, 6, 'Whole building');
 
INSERT INTO meter VALUES
    (1, 1, 'electricity', 'kWh', 'DE_KN_residential1_grid_import'),
    (2, 2, 'electricity', 'kWh', 'DE_KN_residential3_grid_import'),
    (3, 3, 'electricity', 'kWh', 'DE_KN_residential4_grid_import'),
    (4, 4, 'electricity', 'kWh', 'DE_KN_industrial1_grid_import'),
    (5, 5, 'electricity', 'kWh', 'DE_KN_industrial3_grid_import'),
    (6, 6, 'electricity', 'kWh', 'DE_KN_public1_grid_import');
 
-- a handful of 15-min values (kWh), times in UTC
INSERT INTO reading VALUES
    (1, '2016-12-01 07:00:00', 0.42), (1, '2016-12-01 07:15:00', 0.38),
    (1, '2016-12-01 07:30:00', 0.51),
    (4, '2016-12-01 07:00:00', 12.50), (4, '2016-12-01 07:15:00', 14.10),
    (6, '2016-12-01 07:00:00', 3.20);