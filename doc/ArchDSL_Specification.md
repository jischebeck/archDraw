# archDraw Language Specification

**Declarative Syntax for Rigid, Auto-Scaling Architecture Diagrams**
*Version 1.0 • Standard Library Reference Included*

---

## 1. Introduction

**archDraw** is a declarative Domain Specific Language (DSL) designed for software, data, and cloud architects. It addresses the common pain points of manual diagramming by providing a syntax that enforces structural rigidity, automatic layout distribution, and explicit dataflows, while maintaining human-readable source code.

The layout engine interprets nested blocks (`box`, `stack`, `layer`) and automatically calculates optimal bounds, distributing elements cleanly without the need for manual coordinate placement.

---

## 2. Core Primitives

### 2.1. Structural Containers
Containers group elements together and define the layout methodology for their children.

* `box "Name" as alias { ... }`: A standard container. Auto-sizes to fit its children based on its layout directive.
* `stack "Name" as alias { ... }`: A strict vertical or horizontal container designed specifically to hold `layer` elements. Used for reference architectures (e.g., OSI model, Data platforms).
* `layer "Name" as alias { ... }`: A semantic partition within a `stack`. Spans the full width (or height) of the parent stack.

### 2.2. Layout Directives
Layout directives instruct the rendering engine on how to position sibling nodes inside a container. They are declared at the top of a block using the `layout:` keyword.


```

```text
Markdown generated successfully: [file-tag: archDraw_Specification.md]

```dsl
box "Microservices" as ms {
    layout: grid          // Options: horizontal, vertical, grid
    direction: top-down   // Options: top-down, bottom-up, left-right, right-left
    
    service "Auth" as auth
    service "Cart" as cart
}

```

### 2.3. Generic Nodes

General-purpose architectural nodes mapped to standard shapes:

* `component`: A generic system component (Box with component icon).
* `service`: A microservice or background process (Gear/Hexagon).
* `database`: Relational or general databases (Cylinder).
* `storage`: Object storage, buckets, or file systems (Database symbol with file badge).
* `queue`: Message brokers, event buses (Pipe/Stack).
* `node`: A generic compute instance, VM, or physical hardware (3D Box).
* `actor`: A user, client, or external persona (Stick figure).

---

## 3. Connections and Dataflows

Connections should generally be defined outside of the structural blocks to keep the layout definitions clean. The engine routes connections optimally without breaking the rigid container constraints.

### 3.1. Syntax Types

Different arrow types carry distinct semantic meanings, which map to line styles (solid, dashed, thickened) in the rendered output.

| Syntax | Meaning | Visual Style |
| --- | --- | --- |
| `->` | Standard connection / Control Flow / API Call | Solid line, standard arrow |
| `-->` | Asynchronous or Weak connection | Dashed line, standard arrow |
| `=>` | Dataflow (High volume / ETL) | Thick solid line, block arrow |
| `~>` | Stream / Continuous connection | Wavy line, standard arrow |
| `<->` / `<=>` | Bidirectional flow | Double-headed arrows |

### 3.2. Connection Attributes

Attributes can be attached to connections using bracket notation `[...]`.

```dsl
// Syntax: source [arrow] target : "Label" [attributes]
api_gw -> auth_service : "Validate Token" [color="red", style="dotted"]
spark_node => datalake : "Daily Batch Write" [weight="bold"]

```

---

## 4. Google Cloud Platform (GCP) Component Library

archDraw natively supports cloud provider icons via namespaces. The Google Cloud standard library uses the `gcp::[category]::[Service]` namespace. When declared, the rendering engine automatically applies the official Google Cloud icon, standard GCP colors, and appropriate shape styling.

**Syntax Example:**

```dsl
gcp::database::CloudSQL "User DB" as sql_db
gcp::compute::GKE "Kubernetes Cluster" as k8s
gcp::analytics::BigQuery "Data Warehouse" as bq

```

### 4.1. Compute

| Identifier | Service Name | Description |
| --- | --- | --- |
| `gcp::compute::ComputeEngine` | Compute Engine | Virtual Machines, GPUs, TPUs |
| `gcp::compute::AppEngine` | App Engine | Fully managed serverless platform |
| `gcp::compute::CloudFunctions` | Cloud Functions | Event-driven serverless compute |
| `gcp::compute::CloudRun` | Cloud Run | Serverless containers |
| `gcp::compute::GKE` | Google Kubernetes Engine | Managed Kubernetes |
| `gcp::compute::BareMetalSolution` | Bare Metal Solution | Hardware for specialized workloads |

### 4.2. Storage

| Identifier | Service Name | Description |
| --- | --- | --- |
| `gcp::storage::CloudStorage` | Cloud Storage | Object storage (Buckets) |
| `gcp::storage::PersistentDisk` | Persistent Disk | Block storage for VMs |
| `gcp::storage::Filestore` | Filestore | High-performance file storage |
| `gcp::storage::LocalSSD` | Local SSD | Locally attached block storage |

### 4.3. Databases

| Identifier | Service Name | Description |
| --- | --- | --- |
| `gcp::database::CloudSQL` | Cloud SQL | Managed MySQL, PostgreSQL, SQL Server |
| `gcp::database::CloudSpanner` | Cloud Spanner | Globally distributed relational DB |
| `gcp::database::Bigtable` | Cloud Bigtable | NoSQL wide-column store |
| `gcp::database::Firestore` | Firestore | NoSQL document database |
| `gcp::database::Memorystore` | Memorystore | Managed Redis and Memcached |
| `gcp::database::AlloyDB` | AlloyDB | PostgreSQL-compatible database |

### 4.4. Data Analytics & Streaming

| Identifier | Service Name | Description |
| --- | --- | --- |
| `gcp::analytics::BigQuery` | BigQuery | Serverless data warehouse |
| `gcp::analytics::Dataflow` | Dataflow | Stream and batch data processing |
| `gcp::analytics::Dataproc` | Dataproc | Managed Hadoop and Spark |
| `gcp::analytics::PubSub` | Pub/Sub | Messaging and event ingestion |
| `gcp::analytics::Looker` | Looker | Enterprise BI and analytics |
| `gcp::analytics::DataCatalog` | Data Catalog | Data discovery and metadata |
| `gcp::analytics::Composer` | Cloud Composer | Managed Apache Airflow workflow orchestration |

### 4.5. Networking

| Identifier | Service Name | Description |
| --- | --- | --- |
| `gcp::network::VPC` | Virtual Private Cloud | Global virtual network |
| `gcp::network::CloudLoadBalancing` | Cloud Load Balancing | Global/Regional load balancing |
| `gcp::network::CloudCDN` | Cloud CDN | Content delivery network |
| `gcp::network::CloudDNS` | Cloud DNS | Domain name system |
| `gcp::network::CloudInterconnect` | Cloud Interconnect | Dedicated hybrid connectivity |
| `gcp::network::CloudRouter` | Cloud Router | Dynamic routing (BGP) |
| `gcp::network::CloudNAT` | Cloud NAT | Network address translation |

### 4.6. AI & Machine Learning

| Identifier | Service Name | Description |
| --- | --- | --- |
| `gcp::ai::VertexAI` | Vertex AI | Unified ML platform |
| `gcp::ai::VisionAPI` | Cloud Vision API | Image analysis |
| `gcp::ai::SpeechToText` | Speech-to-Text | Audio transcription |
| `gcp::ai::TranslationAPI` | Translation API | Language translation |
| `gcp::ai::NaturalLanguage` | Natural Language API | Text parsing and analysis |

### 4.7. Security, Identity & Management

| Identifier | Service Name | Description |
| --- | --- | --- |
| `gcp::security::IAM` | IAM | Identity and Access Management |
| `gcp::security::KMS` | Cloud KMS | Key Management Service |
| `gcp::security::CloudArmor` | Cloud Armor | DDoS and WAF protection |
| `gcp::security::IAP` | Identity-Aware Proxy | Zero-trust application access |
| `gcp::management::CloudMonitoring` | Cloud Monitoring | Infrastructure monitoring |
| `gcp::management::CloudLogging` | Cloud Logging | Log management |

---

## 5. Comprehensive Example: GCP Serverless Data Pipeline

Below is a full example illustrating the structural rules, dataflows, and GCP components working together.

```dsl
architecture "Real-Time User Analytics Pipeline" {

    actor "Mobile User" as user

    // VPC Boundary
    box "GCP Virtual Private Cloud (VPC)" as vpc {
        layout: vertical
        
        // Load Balancing Layer
        gcp::network::CloudLoadBalancing "Global HTTPs LB" as lb
        
        // Processing Layer
        stack "Compute & Ingestion" {
            direction: left-right
            
            layer "API Gateway" {
                gcp::compute::CloudRun "Ingestion API" as api
            }
            
            layer "Event Bus" {
                gcp::analytics::PubSub "Events Topic" as pubsub
            }
        }
        
        // Analytics Layer
        stack "Data Processing & Storage" {
            direction: left-right
            
            layer "Stream Processing" {
                gcp::analytics::Dataflow "Streaming ETL Job" as dataflow
            }
            
            layer "Persistence" {
                layout: vertical
                gcp::storage::CloudStorage "Raw Data Lake" as gcs
                gcp::analytics::BigQuery "Analytics DWH" as bq
            }
        }
    }

    // External BI Tool
    box "Business Intelligence" {
        gcp::analytics::Looker "Looker Dashboards" as looker
    }

    // -----------------------------------------------------
    // Connections & Flows
    // -----------------------------------------------------
    
    // User flow
    user -> lb : "HTTPS JSON Payload"
    lb -> api : "Route traffic"
    
    // Core Dataflow (Thick arrows)
    api => pubsub : "Publish Event"
    pubsub => dataflow : "Subscribe / Stream"
    
    // Forked writes
    dataflow => gcs : "Backup Raw Events"
    dataflow => bq : "Write Aggregated Metrics"
    
    // Analytical reads
    looker -> bq : "Query Data" [color="blue", style="dashed"]
}

```

