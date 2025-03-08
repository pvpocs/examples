import os
import sys
import re
from typing import List, Dict
import yaml


def check_header_fields(front_matter: Dict, file) -> List[str]:
    errors = []

    # required fields
    required_fields = {"draft", "title", "date", "description", "tags"}

    # Check if all required fields are present
    for field in required_fields:
        if field not in front_matter:
            errors.append(f"Missing required field '{field}' in front matter")

    # Check if all required fields except 'draft' are not empty
    for field in required_fields - {"draft"}:
        if not front_matter.get(field):
            errors.append(f"Field '{field}' cannot be empty")

    return errors


def transform_image_links(content: str, file) -> List[str]:
    """
    Transform the images url by adding `../` at the beginning of the image url.

    For example, change this:
    ![](images/image1.png)

    to this:
    ![](../images/image1.png)
    """
    changes = []
    pattern = r"(!\[.*?\]\()(.+?)(\))"
    matches = re.findall(pattern, content)

    # If no image links found, return empty changes list
    if not matches:
        return changes

    for prefix, path, suffix in matches:
        # Skip if path already starts with '../' or is a URL
        if (
            path.startswith("../")
            or path.startswith("http://")
            or path.startswith("https://")
        ):
            continue

        # Record the change
        changes.append(
            {
                "old": f"{prefix}{path}{suffix}",
                "new": f"{prefix}../{path}{suffix}",
            }
        )

    update_file_in_place(changes, content, file)

    return changes


def update_file_in_place(changes, content: str, source_file) -> None:
    """
    Update the file content in place.
    """

    for change in changes:
        print(f"Change: {change['old']} -> {change['new']}")
        content = content.replace(change["old"], change["new"])

    with open(source_file, "w", encoding="utf-8") as file:
        file.write(content)


def check_header(content: str, file) -> List[str]:
    """
    Check if the markdown file has a valid Hugo front matter at the very
    beginning. For example:

    ---
    date: "2025-03-01"
    draft: false
    title: 'AI and Machine Learning'
    description: 'An introduction to AI and Machine Learning'
    tags:
        - AI
        - Machine Learning
    ---

    Args:
        content: String content of the markdown file
        file: File name for error reporting

    Returns:
        List of error messages
    """
    errors = []

    # Check if the file starts with a front matter pattern
    front_matter_pattern = r"^---\r?\n(.*?)\r?\n---\r?\n"
    match = re.match(front_matter_pattern, content, re.DOTALL)

    if not match:
        errors.append("Header is missing or invalid")
        return errors

    # Extract and validate its content
    yaml_content = match.group(1)

    # Try to parse the YAML content
    try:
        front_matter = yaml.safe_load(yaml_content)

        # Check if front_matter is a dictionary (should be for valid YAML)
        if not isinstance(front_matter, dict):
            errors.append("Front matter doesn't contain valid YAML content")
            return errors

        # Check front matter fields
        errors.extend(check_header_fields(front_matter, file))
    except yaml.YAMLError:
        errors.append("Invalid YAML in Hugo front matter")

    return errors


def get_all_markdown_files(path):
    """Get all markdown files recursively"""

    markdown_files = []
    for root, _, files in os.walk(path, topdown=False):
        for name in files:
            if name.endswith(".md"):
                markdown_files.append(os.path.join(root, name))
    return markdown_files


def process_files(markdown_files) -> List[Dict]:
    output = []
    for file in markdown_files:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
        output_file = {"file": file, "errors": [], "messages": []}

        output_file["errors"].extend(check_header(content, file))
        output_file["messages"].extend(transform_image_links(content, file))

        output.append(output_file)

    return output


if __name__ == "__main__":
    # Run the script with the path to the directory as an argument.
    # Example: python check_markdown.py /path/to/directory
    # If no argument is provided, the current directory is used.
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = os.getcwd()

    markdown_files = get_all_markdown_files(path)

    if not markdown_files:
        print("No markdown files found.")
        sys.exit(0)

    print(f"Processing markdown files in {path} ...")
    output = process_files(markdown_files)

    has_errors = any(file["errors"] for file in output)
    has_messages = any(file["messages"] for file in output)

    if not has_errors and not has_messages:
        print("No errors or messages found.")
        sys.exit(0)

    for file in output:
        print("-" * 50)
        print(file["file"])
        if file["errors"]:
            print("Errors:")
            for error in file["errors"]:
                print(error)
        if file["messages"]:
            print("Messages:")
            for message in file["messages"]:
                print(message)

    if has_errors:
        sys.exit(1)
