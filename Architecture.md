# Architecture Documentation

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     DRONE SECURITY ANALYST AGENT                         │
│                          (Main Orchestrator)                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
        ┌───────────▼──────────┐      ┌────────────▼────────────┐
        │   INPUT LAYER        │      │   EXTERNAL SERVICES     │
        └──────────────────────┘      └─────────────────────────┘
                    │                               │
        ┌───────────┴───────────┐      ┌────────────▼────────────┐
        │                       │      │   Google Gemini API     │
┌───────▼──────┐    ┌──────────▼──────┤   • Frame Analysis      │
│  Telemetry   │    │     Video       ││   • Object Detection   │
│  Simulator   │    │   Simulator     ││   • Security Assessment│
│              │    │                 ││   • NL Query Response  │
│• GPS Data    │    │• 70+ Scenarios  │└─────────────────────────┘
│• Altitude    │    │• Vehicle DB     │
│• Battery     │    │• Time-Aware Gen │
│• Location    │    │• Recurring Track│
└───────┬──────┘    └──────────┬──────┘
        │                      │
        └───────────┬──────────┘
                    │
        ┌───────────▼──────────────────┐
        │   PROCESSING LAYER            │
        └───────────────────────────────┘
                    │
        ┌───────────┴───────────────────────────────────┐
        │                                               │
┌───────▼─────────┐                         ┌──────────▼──────────┐
│  AI Analyzer    │                         │   Alert System      │
│  (ai_analyzer)  │                         │  (alert_system)     │
│                 │                         │                     │
│• analyze_frame()│                         │• evaluate_frame()   │
│• detect_objects│                          │• Rule Engine        │
│• generate_alert│                          │  - Midnight         │
│• answer_query() │                         │  - Suspicious       │
│• summarize()    │                         │  - Restricted Zone  │
│                 │                         │  - Vehicle Repeat   │
│• Fallback Logic │                         │  - AI Assessment    │
└─────────────────┘                         └─────────────────────┘
                    │
        ┌───────────▼──────────────────┐
        │   STORAGE LAYER               │
        └───────────────────────────────┘
                    │
        ┌───────────▼──────────────────┐
        │   Frame Indexer               │
        │   (database.py)               │
        │                               │
        │  ┌─────────────────────────┐ │
        │  │  SQLite Database        │ │
        │  │                         │ │
        │  │  ┌──────────────────┐  │ │
        │  │  │   Frames Table   │  │ │
        │  │  │  • timestamp     │  │ │
        │  │  │  • telemetry     │  │ │
        │  │  │  • description   │  │ │
        │  │  │  • objects       │  │ │
        │  │  └──────────────────┘  │ │
        │  │                         │ │
        │  │  ┌──────────────────┐  │ │
        │  │  │  Objects Table   │  │ │
        │  │  │  • type          │  │ │
        │  │  │  • details       │  │ │
        │  │  │  • confidence    │  │ │
        │  │  │  • frame_id (FK) │  │ │
        │  │  └──────────────────┘  │ │
        │  │                         │ │
        │  │  ┌──────────────────┐  │ │
        │  │  │  Alerts Table    │  │ │
        │  │  │  • alert_type    │  │ │
        │  │  │  • severity      │  │ │
        │  │  │  • description   │  │ │
        │  │  │  • frame_id (FK) │  │ │
        │  │  └──────────────────┘  │ │
        │  │                         │ │
        │  │  ┌──────────────────┐  │ │
        │  │  │  Events Table    │  │ │
        │  │  │  • event_type    │  │ │
        │  │  │  • occurrences   │  │ │
        │  │  │  • patterns      │  │ │
        │  │  └──────────────────┘  │ │
        │  │                         │ │
        │  │  Indexes:               │ │
        │  │  • idx_frames_timestamp│ │
        │  │  • idx_objects_type    │ │
        │  │  • idx_alerts_timestamp│ │
        │  └─────────────────────────┘ │
        │                               │
        │  Query Functions:             │
        │  • query_by_time()            │
        │  • query_by_object()          │
        │  • search_frames()            │
        │  • get_statistics()           │
        └───────────────────────────────┘
                    │
        ┌───────────▼──────────────────┐
        │   OUTPUT LAYER                │
        └───────────────────────────────┘
                    │
        ┌───────────┴───────────────────────────────┐
        │                                           │
┌───────▼──────────┐                   ┌───────────▼──────────┐
│  Real-time Logs  │                   │   Exported Files     │
│                  │                   │                      │
│• Frame Details   │                   │• processed_frames.json
│• Object Detections│                  │• alerts.json         │
│• Alert Messages  │                   │• recurring_vehicles.json
│• Query Results   │                   │• statistics.json     │
└──────────────────┘                   └──────────────────────┘
```

## Data Flow Diagram

```
┌─────────────┐
│  Frame N    │
│  Request    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  1. Generate Telemetry                      │
│     • Position (lat, lon)                   │
│     • Altitude, Battery, Signal             │
│     • Location zone, Timestamp              │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  2. Generate Video Frame Description        │
│     • Select scenario (weighted random)     │
│     • Generate description with objects     │
│     • Track recurring vehicles              │
│     • Add environmental conditions          │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  3. Combine Frame Data                      │
│     frame_data = {                          │
│       timestamp, frame_number,              │
│       description, objects,                 │
│       telemetry, location                   │
│     }                                       │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  4. AI Analysis (Gemini API)                │
│     • Parse description + telemetry         │
│     • Extract objects with confidence       │
│     • Assess activity type                  │
│     • Determine security level              │
│     • Generate recommendations              │
│     [Fallback to rules if API fails]        │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  5. Store in Database                       │
│     • Insert frame (get frame_id)           │
│     • Insert each object (link to frame_id) │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  6. Evaluate Alert Rules                    │
│     • Check midnight activity               │
│     • Check suspicious keywords             │
│     • Check vehicle repetition              │
│     • Check restricted zones                │
│     • Check AI security assessment          │
│     → Generate alerts list                  │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  7. Store Alerts                            │
│     • Insert each alert (link to frame_id)  │
│     • Track in alerts table                 │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  8. Output Results                          │
│     • Print frame summary                   │
│     • Print alerts (color-coded)            │
│     • Append to processed_frames list       │
│     • Append to all_alerts list             │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│  Frame N+1  │
│  Request    │
└─────────────┘
```

## Component Interaction Diagram

```
┌────────────────┐
│     Agent      │ Main orchestrator
│   (agent.py)   │
└────────┬───────┘
         │
         │ coordinates
         │
    ┌────┴────────────────────────────────────┐
    │                                         │
    │  process_frame(n):                      │
    │    1. telemetry ← TelemetrySim          │
    │    2. video ← VideoSim                  │
    │    3. analysis ← AIAnalyzer             │
    │    4. frame_id ← Database.insert        │
    │    5. alerts ← AlertSystem              │
    │    6. alert_ids ← Database.insert       │
    │    7. return combined_result            │
    │                                         │
    └─────────────────────────────────────────┘
         │
         ├─────→ TelemetrySim ──→ generate_telemetry()
         │
         ├─────→ VideoSim ──────→ generate_frame_description()
         │
         ├─────→ AIAnalyzer ────→ analyze_frame()
         │                         ↓
         │                    [Gemini API]
         │                         ↓
         │                    parse_response()
         │
         ├─────→ Database ───────→ insert_frame()
         │                    ├──→ insert_object()
         │                    └──→ insert_alert()
         │
         └─────→ AlertSystem ────→ evaluate_frame()
                                   ├─→ check_midnight()
                                   ├─→ check_suspicious()
                                   ├─→ check_vehicles()
                                   └─→ check_zones()
```

## Database Schema Diagram

```
┌─────────────────────────────────────────┐
│              FRAMES                     │
├─────────────────────────────────────────┤
│ PK  id                  INTEGER         │
│     timestamp           TEXT    ◄───────┼─── Index
│     frame_number        INTEGER         │
│     telemetry_data      TEXT (JSON)     │
│     description         TEXT            │
│     objects_detected    TEXT (JSON)     │
│     location            TEXT            │
│     altitude            REAL            │
│     created_at          TEXT            │
└──────────────┬──────────────────────────┘
               │
               │ 1:N
               │
┌──────────────▼──────────────────────────┐
│              OBJECTS                    │
├─────────────────────────────────────────┤
│ PK  id                  INTEGER         │
│ FK  frame_id            INTEGER         │
│     object_type         TEXT    ◄───────┼─── Index
│     object_details      TEXT (JSON)     │
│     confidence          REAL            │
│     location            TEXT            │
│     timestamp           TEXT    ◄───────┼─── Index
└─────────────────────────────────────────┘

┌──────────────┬──────────────────────────┐
│              │                          │
┌──────────────▼──────────────────────────┐
│              ALERTS                     │
├─────────────────────────────────────────┤
│ PK  id                  INTEGER         │
│ FK  frame_id            INTEGER         │
│     alert_type          TEXT    ◄───────┼─── Index
│     severity            TEXT            │
│     description         TEXT            │
│     timestamp           TEXT    ◄───────┼─── Index
│     resolved            BOOLEAN         │
│     created_at          TEXT            │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│              EVENTS                     │
├─────────────────────────────────────────┤
│ PK  id                  INTEGER         │
│     event_type          TEXT            │
│     first_occurrence    TEXT            │
│     last_occurrence     TEXT            │
│     occurrence_count    INTEGER         │
│     related_objects     TEXT (JSON)     │
│     created_at          TEXT            │
└─────────────────────────────────────────┘
```

## Alert Rule Evaluation Flow

```
┌─────────────────────┐
│   Frame + Telemetry │
│   + AI Analysis     │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Rule 1: Midnight Activity           │
│  ────────────────────────────        │
│  hour = extract_hour(timestamp)      │
│  if hour >= 22 or hour < 6:          │
│    → ALERT: "midnight_activity"      │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Rule 2: Suspicious Behavior         │
│  ────────────────────────────        │
│  keywords = ["running", "loitering", │
│              "climbing", "breaking"] │
│  if any(kw in description):          │
│    → ALERT: "suspicious_behavior"    │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Rule 3: Vehicle Repetition          │
│  ────────────────────────────        │
│  for obj in objects:                 │
│    if obj.type == "vehicle":         │
│      history[identifier].append()    │
│      if count >= threshold:          │
│        → ALERT: "vehicle_repeat"     │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Rule 4: Restricted Zone             │
│  ────────────────────────────        │
│  zones = ["main_gate", "warehouse"]  │
│  if location in zones:               │
│    → ALERT: "restricted_zone"        │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Rule 5: AI Security Assessment      │
│  ────────────────────────────        │
│  if ai_analysis.security_level       │
│     in ["high", "critical"]:         │
│    → ALERT: "ai_security_assessment" │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────┐
│  Collected Alerts    │
│  [alert1, alert2...] │
└──────────────────────┘
```

## Scalability Architecture (Future)

```
┌─────────────────────────────────────────────────────────────┐
│                      CLOUD DEPLOYMENT                        │
└─────────────────────────────────────────────────────────────┘

                     ┌──────────────┐
                     │ Load Balancer│
                     └──────┬───────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐   ┌────────▼─────┐   ┌────────▼─────┐
│ Agent Pod 1  │   │ Agent Pod 2  │   │ Agent Pod N  │
│ (Kubernetes) │   │ (Kubernetes) │   │ (Kubernetes) │
└───────┬──────┘   └────────┬─────┘   └────────┬─────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                    ┌───────▼────────┐
                    │  Message Queue │
                    │   (Kafka/SQS)  │
                    └───────┬────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐   ┌────────▼─────┐   ┌────────▼─────┐
│  AI Workers  │   │Alert Workers │   │ DB Writers   │
└───────┬──────┘   └────────┬─────┘   └────────┬─────┘
        │                   │                   │
        │                   │                   │
   ┌────▼────┐        ┌─────▼──────┐    ┌──────▼──────┐
   │ Gemini  │        │Notification│    │ PostgreSQL  │
   │   API   │        │  Service   │    │  + TimescaleDB
   └─────────┘        └────────────┘    └──────┬──────┘
                                               │
                                        ┌──────▼──────┐
                                        │  S3/Blob    │
                                        │  Storage    │
                                        └─────────────┘
```

## Technology Stack

```
┌─────────────────────────────────────────┐
│          APPLICATION LAYER              │
├─────────────────────────────────────────┤
│  Python 3.8+                            │
│  • agent.py (Main orchestrator)         │
│  • Modular components                   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│          AI/ML LAYER                    │
├─────────────────────────────────────────┤
│  Google Gemini 1.5 Flash                │
│  • Object detection                     │
│  • Frame analysis                       │
│  • NL query interface                   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│          DATA LAYER                     │
├─────────────────────────────────────────┤
│  SQLite 3                               │
│  • Normalized schema                    │
│  • Strategic indexes                    │
│  • ACID compliance                      │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│          TESTING LAYER                  │
├─────────────────────────────────────────┤
│  unittest (built-in)                    │
│  • 17 test cases                        │
│  • Unit + Integration tests             │
└─────────────────────────────────────────┘
```

## Design Patterns Used

1. **Singleton Pattern:** Database connection management
2. **Factory Pattern:** Frame and telemetry generation
3. **Strategy Pattern:** Alert rule evaluation
4. **Observer Pattern:** Alert notification (future)
5. **Repository Pattern:** Database abstraction layer

## Security Considerations

```
┌─────────────────────────────────────────┐
│          SECURITY LAYERS                │
├─────────────────────────────────────────┤
│                                         │
│  1. API Key Management                  │
│     • Environment variables             │
│     • No hardcoded keys                 │
│     • .env file (git-ignored)           │
│                                         │
│  2. Data Storage                        │
│     • Local SQLite (no cloud exposure)  │
│     • File permissions                  │
│     • Database encryption (future)      │
│                                         │
│  3. Input Validation                    │
│     • Type checking                     │
│     • Range validation                  │
│     • SQL injection prevention          │
│                                         │
│  4. Error Handling                      │
│     • Try-except blocks                 │
│     • Graceful degradation              │
│     • No sensitive data in logs         │
│                                         │
└─────────────────────────────────────────┘
```

---

*Architecture documentation created for FlytBase AI Engineer Assignment*