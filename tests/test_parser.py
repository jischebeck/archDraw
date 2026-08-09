import pytest
from archDraw import parse_dsl, Container, Node

def test_parse_simple_dsl():
    dsl = """
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
    """
    root, connections = parse_dsl(dsl)
    
    # 1. Assert root container
    assert isinstance(root, Container)
    assert root.name == "Simple Diagram"
    assert root.layout == "vertical"
    
    # 2. Check children of root
    assert len(root.children) == 2
    
    user = root.children[0]
    assert isinstance(user, Node)
    assert user.name == "User"
    assert user.node_type == "actor"
    
    vpc = root.children[1]
    assert isinstance(vpc, Container)
    assert vpc.name == "VPC Boundary"
    assert vpc.layout == "horizontal"
    assert len(vpc.children) == 2
    
    web = vpc.children[0]
    assert isinstance(web, Node)
    assert web.name == "Web server"
    assert web.node_type == "service"
    
    db = vpc.children[1]
    assert isinstance(db, Node)
    assert db.name == "DB server"
    assert db.node_type == "database"
    
    # 3. Assert connections
    assert len(connections) == 2
    c1 = connections[0]
    assert c1.source == "user"
    assert c1.target == "web"
    assert c1.arrow == "->"
    assert c1.label == "requests"
    assert c1.attributes == {}
    
    c2 = connections[1]
    assert c2.source == "web"
    assert c2.target == "db"
    assert c2.arrow == "->"
    assert c2.label == "queries"
    assert c2.attributes == {"color": "blue", "style": "dashed"}

def test_parse_specification_example():
    spec_dsl = """
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
    """
    root, connections = parse_dsl(spec_dsl)
    
    assert root.name == "Real-Time User Analytics Pipeline"
    
    # Verify the hierarchical nesting and directives:
    # root (vertical) -> [user, vpc, looker_box]
    assert len(root.children) == 3
    user_node = root.children[0]
    vpc_box = root.children[1]
    bi_box = root.children[2]
    
    assert user_node.node_type == "actor"
    assert vpc_box.name == "GCP Virtual Private Cloud (VPC)"
    assert vpc_box.layout == "vertical"
    
    # vpc_box -> [lb, compute_stack, data_stack]
    assert len(vpc_box.children) == 3
    lb_node = vpc_box.children[0]
    compute_stack = vpc_box.children[1]
    data_stack = vpc_box.children[2]
    
    assert lb_node.node_type == "gcp::network::CloudLoadBalancing"
    
    # stack "Compute & Ingestion" has direction: left-right -> layout="horizontal"
    assert compute_stack.layout == "horizontal"
    # compute_stack -> [api_gateway_layer, event_bus_layer]
    assert len(compute_stack.children) == 2
    api_layer = compute_stack.children[0]
    event_layer = compute_stack.children[1]
    
    assert api_layer.name == "API Gateway"
    assert len(api_layer.children) == 1
    assert api_layer.children[0].node_type == "gcp::compute::CloudRun"
    
    assert event_layer.name == "Event Bus"
    assert len(event_layer.children) == 1
    assert event_layer.children[0].node_type == "gcp::analytics::PubSub"

    # data_stack -> [stream_processing_layer, persistence_layer]
    assert len(data_stack.children) == 2
    stream_layer = data_stack.children[0]
    persistence_layer = data_stack.children[1]
    
    assert stream_layer.name == "Stream Processing"
    assert persistence_layer.name == "Persistence"
    assert persistence_layer.layout == "vertical" # directive layout: vertical
    
    # persistence_layer -> [gcs, bq]
    assert len(persistence_layer.children) == 2
    assert persistence_layer.children[0].node_type == "gcp::storage::CloudStorage"
    assert persistence_layer.children[1].node_type == "gcp::analytics::BigQuery"

    # BI Box
    assert bi_box.name == "Business Intelligence"
    assert len(bi_box.children) == 1
    assert bi_box.children[0].node_type == "gcp::analytics::Looker"

    # Verify connections list
    assert len(connections) == 7
    assert connections[0].source == "user"
    assert connections[0].target == "lb"
    assert connections[0].arrow == "->"
    assert connections[0].label == "HTTPS JSON Payload"
    
    assert connections[2].source == "api"
    assert connections[2].target == "pubsub"
    assert connections[2].arrow == "=>"
    assert connections[2].label == "Publish Event"

    assert connections[6].source == "looker"
    assert connections[6].target == "bq"
    assert connections[6].arrow == "->"
    assert connections[6].label == "Query Data"
    assert connections[6].attributes == {"color": "blue", "style": "dashed"}

def test_parse_syntax_error_missing_brace():
    from textx.exceptions import TextXSyntaxError
    dsl = """
    architecture "Missing Brace" {
        actor "User" as user
        box "VPC Boundary" as vpc {
            service "Web" as web
        // Missing closing brace for box and architecture
    """
    with pytest.raises(TextXSyntaxError):
        parse_dsl(dsl)

def test_parse_syntax_error_invalid_arrow():
    from textx.exceptions import TextXSyntaxError
    dsl = """
    architecture "Invalid Arrow" {
        actor "User" as user
        service "Web" as web
        user -?-> web : "requests"
    }
    """
    with pytest.raises(TextXSyntaxError):
        parse_dsl(dsl)

def test_parse_attributes_and_tags():
    dsl = """
    architecture "Attributes and Tags" {
        service "Secure Web" as web [color="red", tags="secure,frontend"]
        box "VPC Box" as vpc [fill="blue"] {
            database "DB" as db
        }
    }
    """
    root, _ = parse_dsl(dsl)
    
    web = root.children[0]
    assert web.attributes == {"color": "red", "tags": "secure,frontend"}
    assert web.tags == ["secure", "frontend"]

    vpc = root.children[1]
    assert vpc.attributes == {"fill": "blue"}

def test_parse_root_layout_directives():
    dsl = """
    architecture "Horizontal Diagram" {
        direction: left-right
        actor "User" as user
        service "Web" as web
    }
    """
    root, _ = parse_dsl(dsl)
    assert root.layout == "horizontal"


