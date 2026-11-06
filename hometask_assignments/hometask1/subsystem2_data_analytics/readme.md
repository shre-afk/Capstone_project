# Smart Energy Management System · Hometask 1 (OOP classes)
 
Group 30 · M1-05 Compact Programming Course (Python) · FH Dortmund
 
## Team overview
 
| Member        | Matr. no. | Subsystem                                 | Folder                       |
|---------------|-----------|-------------------------------------------|------------------------------|
| Shreya Patil  | 7226047   | 1 · Energy Dashboard & Reporting          | `subsystem1_dashboard/`      |
| Ourvish Lofur | 7226994   | 2 · Data Management & Energy Analytics    | `subsystem2_data_analytics/` |
| Joywin Bennis | 7225872   | 3 · AI Analyzer & Integration             | `subsystem3_ai/`             |
 
## System design
 
### Subsystem 2 · Data Management & Energy Analytics
 
A building has zones, a zone has meters. Today every building has one zone
("Whole building") with one electricity meter; the classes already allow more.
 
```mermaid
classDiagram
    Building "1" *-- "*" Zone : has
    Zone "1" o-- "*" Meter : has
    Meter <|-- EnergyMeter
    Building <|-- Home
    Building <|-- Business
    Building <|-- PublicBuilding
    class Building {
        <<abstract>>
        -str _name
        -float _floor_area_m2
        -list _zones
        +setup_whole_building(csv_column, max_kwh)
        +add_zone(zone)
        +meters(kind)
        +total_kwh()
        +kwh_per_m2()
        +is_open(ts)*
        +get/set_name()
        +get/set_floor_area_m2()
    }
    class Zone {
        -str _name
        -list _meters
        +add_meter(meter)
        +total(kind)
        +get/set_name()
    }
    class Meter {
        -str _kind
        -str _unit
        -str _source
        -dict _readings
        -float _max_per_interval
        +configure(max_per_interval)
        +add_reading(ts, value) bool
        +total()
        +get/set_kind()
        +get/set_unit()
        +get/set_source()
    }
```
 
Run it:
 
```
cd subsystem2_data_analytics
python demo.py
```
 
## Presentation
 
Team video (3 to 5 min): TO-PASTE-THE-LINK-HERE