#!/usr/bin/env python3
import os
import sys
import glob

# Add src to sys.path so we can import archDraw modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, "src"))

from archDraw import parse_dsl, parse_dsl_file, LayoutEngine, SVGRenderer

TEST_CASES = {
    "simple_diagram": """
    architecture "Simple Diagram" {
        actor "User" as user
        
        box "VPC Boundary" as vpc {
            layout: horizontal
            service "Web server" as web
            database "DB server" as db
        }
        
        user -> web : "requests"
        web -> db : "queries" [color="blue", style="dashed"]
    }
    """,
    "realtime_analytics_pipeline": """
    architecture "Real-Time User Analytics Pipeline" {
        actor "Mobile User" as user

        box "GCP Virtual Private Cloud (VPC)" as vpc {
            layout: vertical
            
            gcp::network::CloudLoadBalancing "Global HTTPs LB" as lb
            
            stack "Compute & Ingestion" {
                direction: left-right
                
                layer "API Gateway" {
                    gcp::compute::CloudRun "Ingestion API" as api
                }
                
                layer "Event Bus" {
                    gcp::analytics::PubSub "Events Topic" as pubsub
                }
            }
            
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

        box "Business Intelligence" {
            gcp::analytics::Looker "Looker Dashboards" as looker
        }

        user -> lb : "HTTPS JSON Payload"
        lb -> api : "Route traffic"
        
        api => pubsub : "Publish Event"
        pubsub => dataflow : "Subscribe / Stream"
        
        dataflow => gcs : "Backup Raw Events"
        dataflow => bq : "Write Aggregated Metrics"
        
        looker -> bq : "Query Data" [color="blue", style="dashed"]
    }
    """,
    "attributes_and_tags": """
    architecture "Attributes and Tags" {
        service "Secure Web" as web [color="red", tags="secure,frontend"]
        box "VPC Box" as vpc [fill="blue"] {
            database "DB" as db
        }
    }
    """,
    "horizontal_diagram": """
    architecture "Horizontal Diagram" {
        direction: left-right
        actor "User" as user
        service "Web" as web
    }
    """,
    "platform_architecture": """
    architecture "Platform Architecture" {
        box "Ingestion Layer" {
            layout: horizontal
            service "Web Frontend"
            service "Mobile Gateway"
        }
        box "Processing Core" {
            layout: horizontal
            box "Stream Processing" {
                layout: vertical
                service "Kafka Topic"
                service "Flink Job"
            }
            box "Batch Processing" {
                layout: vertical
                service "Airflow Scheduler"
                service "Hadoop Cluster"
            }
        }
    }
    """
}

def render_dsl_to_svg(dsl_content: str, output_svg_path: str):
    root, connections = parse_dsl(dsl_content)
    renderer = SVGRenderer()
    LayoutEngine.calculate_bounds(root, renderer)
    LayoutEngine.apply_offset(root, dx=50, dy=50)
    renderer.export(root, output_svg_path, connections)
    print(f"Rendered SVG to {output_svg_path}")

def main():
    demo_dir = os.path.join(project_root, "doc", "demo")
    os.makedirs(demo_dir, exist_ok=True)

    items = []

    # 1. Process examples
    examples_glob = os.path.join(project_root, "examples", "*.archDraw")
    for filepath in sorted(glob.glob(examples_glob)):
        name = os.path.basename(filepath).replace(".archDraw", "")
        output_path = os.path.join(demo_dir, f"{name}.svg")
        
        with open(filepath, "r") as f:
            content = f.read()
        
        render_dsl_to_svg(content, output_path)
        items.append({
            "name": name.replace("_", " ").title() + " (Example)",
            "filename": f"demo/{name}.svg",
            "type": "Example"
        })

    # 2. Process test cases
    for name, content in TEST_CASES.items():
        output_path = os.path.join(demo_dir, f"{name}.svg")
        render_dsl_to_svg(content, output_path)
        items.append({
            "name": name.replace("_", " ").title() + " (Test Case)",
            "filename": f"demo/{name}.svg",
            "type": "Test Case"
        })

    # 3. Generate demo.html
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>archDraw Showcase & Demo</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #38bdf8;
            --border: #334155;
            --card-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
        }

        body {
            margin: 0;
            padding: 0;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: 'Outfit', sans-serif;
            line-height: 1.6;
        }

        header {
            text-align: center;
            padding: 4rem 2rem;
            background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
            border-bottom: 1px solid var(--border);
            position: relative;
            overflow: hidden;
        }

        header h1 {
            margin: 0 0 1rem 0;
            font-size: 3rem;
            font-weight: 700;
            letter-spacing: -0.05em;
            background: linear-gradient(to right, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        header p {
            margin: 0;
            font-size: 1.2rem;
            color: var(--text-secondary);
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 3rem 1.5rem;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2.5rem;
        }

        .card {
            background-color: var(--bg-secondary);
            border-radius: 12px;
            border: 1px solid var(--border);
            overflow: hidden;
            box-shadow: var(--card-shadow);
            transition: transform 0.3s ease, border-color 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
            border-color: var(--accent);
        }

        .card-header {
            padding: 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-title {
            margin: 0;
            font-size: 1.25rem;
            font-weight: 600;
        }

        .badge {
            font-size: 0.75rem;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .badge-example {
            background-color: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }

        .badge-test {
            background-color: rgba(168, 85, 247, 0.15);
            color: #c084fc;
            border: 1px solid rgba(168, 85, 247, 0.3);
        }

        .card-body {
            padding: 1.5rem;
            background-color: #ffffff;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 250px;
            overflow: auto;
        }

        .card-body img {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }

        footer {
            text-align: center;
            padding: 3rem 1.5rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
            border-top: 1px solid var(--border);
            background-color: #0b0f19;
        }
    </style>
</head>
<body>

<header>
    <h1>archDraw Showcase & Demo</h1>
    <p>A gallery of architectural diagrams automatically generated from DSL files and test cases using archDraw.</p>
</header>

<div class="container">
    <div class="grid">
"""

    for item in items:
        badge_class = "badge-example" if item["type"] == "Example" else "badge-test"
        html_content += f"""
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">{item["name"]}</h3>
                <span class="badge {badge_class}">{item["type"]}</span>
            </div>
            <div class="card-body">
                <img src="{item["filename"]}" alt="{item["name"]}">
            </div>
        </div>
"""

    html_content += """
    </div>
</div>

<footer>
    <p>&copy; 2026 archDraw. Generated automatically.</p>
</footer>

</body>
</html>
"""

    html_path = os.path.join(project_root, "doc", "demo.html")
    with open(html_path, "w") as f:
        f.write(html_content)
    print(f"Generated showcase page: {html_path}")

if __name__ == "__main__":
    main()
