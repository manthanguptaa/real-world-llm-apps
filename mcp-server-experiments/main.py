# server.py
from mcp.server.fastmcp import FastMCP
import os

# Create an MCP server
mcp = FastMCP("AI Sticky Notes")

NOTE_FILE = os.path.join(os.path.dirname(__file__), "notes.txt")

def ensure_file():
    if not os.path.exists(NOTE_FILE):
        with open(NOTE_FILE, "w") as f:
            f.write("")

@mcp.tool()
def add_note(note: str) -> str:
    """
    Append a note to the sticky notes file.

    Args:
        note (str): The note to add to the sticky notes file.

    Returns:
        str: A message indicating that the note was added.
    """
    ensure_file()
    with open(NOTE_FILE, "a") as f:
        f.write(note + "\n")
    return "Note added"


@mcp.tool()
def read_notes() -> str:
    """
    Read and return all notes from the sticky notes file.

    Returns:
        str: All notes from the sticky notes file.
    """
    ensure_file()
    with open(NOTE_FILE, "r") as f:
        content = f.read()
    return content or "No notes found"


@mcp.resource("notes://latest")
def get_latest_note() -> str:
    """
    Gets the latest note from the sticky notes file.
    Returns:
        str: The latest note from the sticky notes file.
    """
    ensure_file()
    with open(NOTE_FILE, "r") as f:
        lines = f.readlines()
    return lines[-1] if lines else "No notes found"

@mcp.prompt()
def note_summary_prompt() -> str:
    """
    Generate a prompt asking the AI to summarize the notes in the sticky notes file.
    Returns:
        str: A prompt asking the AI to summarize the notes in the sticky notes file.
    """
    ensure_file()
    with open(NOTE_FILE, "r") as f:
        content = f.read()
    if not content:
        return "No notes found"
    return f"""
    Summarize the following notes:
    {content}
    """