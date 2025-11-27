#!/usr/bin/env python
"""
MCP Plotting Tools

Provides plotting functionality for visualizing query results.
Can display plots in the terminal (if supported) or save to files.
"""
import json
import logging
import os
import tempfile

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

from mcp.server.fastmcp import FastMCP
from typing import Literal

# Try to import term-image for terminal display
try:
    from term_image.image import from_file
    TERM_IMAGE_AVAILABLE = True
except ImportError:
    TERM_IMAGE_AVAILABLE = False

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("mcp_plot")

# Initialize MCP server
mcp = FastMCP("mcp_plot")


@mcp.tool()
async def generate_plot(
    query_result_json: str,
    plot_type: Literal["line", "bar", "scatter", "histogram"] = "line",
    title: str = "Query Results",
    xlabel: str = "X",
    ylabel: str = "Y"
) -> str:
    """Generate a plot from query results returned by query_topic_table().

    This tool displays the plot directly in the terminal (if supported) and also
    saves it to a file for backup.

    Args:
        query_result_json: JSON string from query_topic_table() containing data to plot.
                          Expected format: [[x1, y1], [x2, y2], ...] for 2D data
                          or [[value1], [value2], ...] for 1D data
        plot_type: Type of plot - "line", "bar", "scatter", or "histogram"
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label

    Returns:
        JSON string containing the plot file path and status message
    """
    log.info(f"Generating {plot_type} plot: {title}")

    # Parse the JSON data
    try:
        data = json.loads(query_result_json)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON data: {str(e)}"})

    if not data:
        return json.dumps({"error": "No data to plot"})

    # Create the plot
    plt.figure(figsize=(10, 6))

    # Assuming first column is X, second is Y (or just values for 1D)
    if len(data[0]) >= 2:
        x_data = [row[0] for row in data]
        y_data = [row[1] for row in data]

        if plot_type == "line":
            plt.plot(x_data, y_data, marker='o', linewidth=2, markersize=6)
        elif plot_type == "bar":
            plt.bar(x_data, y_data)
        elif plot_type == "scatter":
            plt.scatter(x_data, y_data, s=100, alpha=0.6)
        elif plot_type == "histogram":
            plt.hist(y_data, bins=20, edgecolor='black')
    else:
        # Single column - just plot values
        values = [row[0] for row in data]
        if plot_type == "histogram":
            plt.hist(values, bins=20, edgecolor='black')
        else:
            plt.plot(range(len(values)), values, marker='o', linewidth=2, markersize=6)

    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    temp_path = temp_file.name
    temp_file.close()

    plt.savefig(temp_path, format='png', dpi=100, bbox_inches='tight')
    plt.close()

    log.info(f"Plot saved to {temp_path}")

    # Try to display in terminal
    display_status = "not displayed"
    if TERM_IMAGE_AVAILABLE:
        try:
            img = from_file(temp_path)
            print("\n" + "="*60)
            print(f"  {title}")
            print("="*60)
            img.draw()
            print("="*60 + "\n")
            display_status = "displayed in terminal"
            log.info("Plot displayed in terminal")
        except Exception as e:
            log.warning(f"Could not display plot in terminal: {e}")
            display_status = f"terminal display failed: {str(e)}"
    else:
        log.warning("term-image not available. Install with: pip install term-image")
        display_status = "term-image library not installed"

    return json.dumps({
        "file_path": temp_path,
        "plot_type": plot_type,
        "data_points": len(data),
        "display_status": display_status,
        "message": f"Generated {plot_type} plot with {len(data)} data points. File: {temp_path}"
    })


def run_stdio_server():
    """Run the MCP server over stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_stdio_server()
