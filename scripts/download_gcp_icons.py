import os
import re
import urllib.request
import zipfile
import io
import datetime
import base64
import json

# Target file paths
GCP_FILE = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "src", "archDraw", "assets", "gcp_icons.py"
))
DATABRICKS_FILE = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "src", "archDraw", "assets", "databricks_icons.py"
))

# URLs of GCP SVG icons
URLS = [
    "https://services.google.com/fh/files/misc/category-icons.zip",
    "https://services.google.com/fh/files/misc/core-products-icons.zip"
]

DATABRICKS_URL = "https://raw.githubusercontent.com/Azure-Player/icons-and-symbols/master/DrawIO-icons-library/Databricks%20(orange).xml"

# Standard categories mapping based on spec
CATEGORIES = [
    "compute", "storage", "database", "analytics", "network", 
    "ai", "security", "management"
]

def sanitize_name(name):
    # Remove extension and normalize
    name = os.path.splitext(os.path.basename(name))[0]
    # Remove spaces, hyphens, underscores, and parentheses
    name = re.sub(r'[\s\-_()]+', '', name)
    return name

def parse_svg_content(content_bytes):
    try:
        content = content_bytes.decode("utf-8")
        # Strip XML declaration if present
        content = re.sub(r'<\?xml[^>]*\?>', '', content)
        # Strip doctype if present
        content = re.sub(r'<!DOCTYPE[^>]*>', '', content)
        return content.strip()
    except Exception:
        return ""

def main():
    # 1. Skip check if already downloaded
    gcp_downloaded = False
    databricks_downloaded = False

    if os.path.exists(GCP_FILE):
        with open(GCP_FILE, "r") as f:
            if "GCP_ICON_DOWNLOADED=true" in f.read():
                gcp_downloaded = True

    if os.path.exists(DATABRICKS_FILE):
        with open(DATABRICKS_FILE, "r") as f:
            if "DATABRICKS_ICON_DOWNLOADED=true" in f.read():
                databricks_downloaded = True

    if gcp_downloaded and databricks_downloaded:
        print("All icons already downloaded. Skipping build.")
        return

    os.makedirs(os.path.dirname(GCP_FILE), exist_ok=True)
    today = datetime.date.today().isoformat()

    # GCP Icons Ingestion
    if not gcp_downloaded:
        print("Downloading and compiling GCP SVG icons...")
        gcp_dict = {}
        for url in URLS:
            print(f"Downloading {url}...")
            try:
                req = urllib.request.Request(
                    url, 
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req) as response:
                    zip_data = response.read()
                    
                with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                    for file_info in zf.infolist():
                        if file_info.filename.endswith(".svg"):
                            path_parts = [p.lower() for p in file_info.filename.split('/')]
                            
                            category = "general"
                            for cat in CATEGORIES:
                                if cat in path_parts:
                                    category = cat
                                    break
                            
                            service_name = sanitize_name(file_info.filename)
                            svg_content = parse_svg_content(zf.read(file_info.filename))
                            
                            if svg_content:
                                key = f"gcp::{category}::{service_name}"
                                gcp_dict[key] = svg_content
                                gcp_dict[service_name.lower()] = svg_content
            except Exception as e:
                print(f"Failed to download/parse {url}: {e}")

        # Write gcp_icons.py
        with open(GCP_FILE, "w") as f:
            f.write("# GCP_ICON_DOWNLOADED=true\n")
            f.write(f"# Downloaded on: {today}\n")
            f.write("# Pre-compiled dictionary mapping component names to SVG strings\n\n")
            f.write("ICONS = {\n")
            for key, svg in sorted(gcp_dict.items()):
                escaped_svg = svg.replace('\\', '\\\\').replace('\'', '\\\'').replace('\n', '\\n')
                f.write(f"    '{key}': '{escaped_svg}',\n")
            f.write("}\n")
        print(f"Successfully compiled {len(gcp_dict)} GCP icons to {GCP_FILE}")

    # Databricks Icons Ingestion
    if not databricks_downloaded:
        print(f"Downloading Databricks icons from {DATABRICKS_URL}...")
        databricks_dict = {}
        try:
            req = urllib.request.Request(
                DATABRICKS_URL,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req) as response:
                xml_data = response.read().decode("utf-8")
                
            mxlib_match = re.search(r'<mxlibrary>(.*?)</mxlibrary>', xml_data, re.DOTALL)
            if mxlib_match:
                json_str = mxlib_match.group(1).strip()
                library_items = json.loads(json_str)
                for item in library_items:
                    data_uri = item.get("data", "")
                    if data_uri.startswith("data:image/svg+xml;base64,"):
                        b64_data = data_uri.split(",", 1)[1]
                        svg_bytes = base64.b64decode(b64_data)
                        svg_content = parse_svg_content(svg_bytes)
                        
                        title = item.get("title", "")
                        if svg_content and title:
                            service_name = sanitize_name(title)
                            key = f"databricks::{service_name}"
                            databricks_dict[key] = svg_content
                            databricks_dict[service_name.lower()] = svg_content
        except Exception as e:
            print(f"Failed to download/parse Databricks icons: {e}")

        # Write databricks_icons.py
        with open(DATABRICKS_FILE, "w") as f:
            f.write("# DATABRICKS_ICON_DOWNLOADED=true\n")
            f.write(f"# Downloaded on: {today}\n")
            f.write("# Pre-compiled dictionary mapping component names to SVG strings\n\n")
            f.write("ICONS = {\n")
            for key, svg in sorted(databricks_dict.items()):
                escaped_svg = svg.replace('\\', '\\\\').replace('\'', '\\\'').replace('\n', '\\n')
                f.write(f"    '{key}': '{escaped_svg}',\n")
            f.write("}\n")
        print(f"Successfully compiled {len(databricks_dict)} Databricks icons to {DATABRICKS_FILE}")

if __name__ == "__main__":
    main()
