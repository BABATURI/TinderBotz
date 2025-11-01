import os
from langchain_core.tools import tool


def _path_check(path: str) -> bool:
    safe_dir = os.path.realpath(".")
    if os.path.commonprefix((os.path.realpath(path),safe_dir)) != safe_dir:
        return False
    return True

# Tools
# @function_tool
@tool(description="Read the contents of a file.")
def read_file(filename: str) -> str:
    """
    Read the contents of a file.
    Args:
        filename: The path to the file to read.
    Returns:
        The contents of the file or an error message.
    """
    if not _path_check(filename):
        return "Error: Access to the specified path is not allowed."
    
    try:
        with open(filename, "r") as file:
            return file.read()
    except FileNotFoundError:
        return f"File '{filename}' not found."

# @function_tool
@tool(description="Write content to a file.")
def write_file(filename: str, content: str) -> str:
    """
    Write content to a file.
    Args:
        filename: The path to the file to write.
        content: The content to write to the file.
    Returns:
        A success message or an error message.
    """
    if not _path_check(filename):
        return "Error: Access to the specified path is not allowed."
    
    with open(filename, "w") as file:
        file.write(content)
    return f"File '{filename}' written successfully."

# @function_tool
@tool(description="List all files in a directory.")
def list_files(directory: str) -> str:
    """
    List all files in the specified directory.
    Args:
        directory: The path to the directory.
    Returns:
        A list of files in the directory or an error message.
    """
    try:
        files = os.listdir(directory)
        return "\n".join(files)
    except FileNotFoundError:
        return f"Directory '{directory}' not found."


def get_tools():
    return [read_file, write_file, list_files]


def get_dating_tools():
    return []


def find_tool_by_name(name: str):
    tools = get_tools()
    for tool in tools:
        if tool.name.lower() == name.lower():
            return tool
    return None