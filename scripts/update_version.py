#!/usr/bin/env python3
import sys
import os
import re
from datetime import datetime
import subprocess

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/update_version.py <new_version> [changelog_message]")
        sys.exit(1)

    new_version = sys.argv[1]
    changelog_message = sys.argv[2] if len(sys.argv) > 2 else "Update components and features."

    # Validate version format (e.g. 0.2.0)
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print(f"Error: Version '{new_version}' must be in major.minor.patch format.")
        sys.exit(1)

    # Paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pyproject_path = os.path.join(project_root, "pyproject.toml")
    init_path = os.path.join(project_root, "src", "archDraw", "__init__.py")
    changelog_path = os.path.join(project_root, "CHANGELOG.md")

    # 1. Update pyproject.toml
    with open(pyproject_path, "r") as f:
        pyproject_content = f.read()
    updated_pyproject = re.sub(
        r'^version\s*=\s*".*?"',
        f'version = "{new_version}"',
        pyproject_content,
        flags=re.MULTILINE
    )
    with open(pyproject_path, "w") as f:
        f.write(updated_pyproject)
    print(f"Updated {pyproject_path} to version {new_version}")

    # 2. Update __init__.py
    with open(init_path, "r") as f:
        init_content = f.read()
    updated_init = re.sub(
        r'^__version__\s*=\s*".*?"',
        f'__version__ = "{new_version}"',
        init_content,
        flags=re.MULTILINE
    )
    with open(init_path, "w") as f:
        f.write(updated_init)
    print(f"Updated {init_path} to version {new_version}")

    # 3. Update CHANGELOG.md
    today = datetime.today().strftime('%Y-%m-%d')
    new_entry = f"## [{new_version}] - {today}\n- {changelog_message}\n"
    
    with open(changelog_path, "r") as f:
        changelog_content = f.read()

    # Insert after "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"
    header_pattern = r'(# Changelog\n\nAll notable changes to this project will be documented in this file\.\n\n)'
    if re.search(header_pattern, changelog_content):
        updated_changelog = re.sub(header_pattern, f'\\1{new_entry}\n', changelog_content, count=1)
    else:
        # Fallback to inserting after first line
        lines = changelog_content.splitlines()
        if lines:
            lines.insert(2, new_entry)
            updated_changelog = "\n".join(lines) + "\n"
        else:
            updated_changelog = new_entry

    with open(changelog_path, "w") as f:
        f.write(updated_changelog)
    print(f"Updated {changelog_path} with entry for {new_version}")

    # 3.5 Update README.md version pill/badge
    readme_path = os.path.join(project_root, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r") as f:
            readme_content = f.read()
        updated_readme = re.sub(
            r'https://img.shields.io/badge/version-.*?-blue',
            f'https://img.shields.io/badge/version-{new_version}-blue',
            readme_content
        )
        with open(readme_path, "w") as f:
            f.write(updated_readme)
        print(f"Updated {readme_path} version badge to {new_version}")

    # 4. Git operations
    try:
        git_add_files = [pyproject_path, init_path, changelog_path]
        if os.path.exists(readme_path):
            git_add_files.append(readme_path)
        subprocess.run(["git", "add"] + git_add_files, check=True)
        # Check if uv.lock exists and update it too
        uv_lock_path = os.path.join(project_root, "uv.lock")
        if os.path.exists(uv_lock_path):
            subprocess.run(["uv", "lock"], check=True)
            subprocess.run(["git", "add", uv_lock_path], check=True)

        commit_msg = f"Bump version to {new_version}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        print(f"Committed changes with message: '{commit_msg}'")

        tag_name = f"v{new_version}"
        subprocess.run(["git", "tag", "-a", tag_name, "-m", f"Version {new_version}"], check=True)
        print(f"Created git tag: {tag_name}")
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
