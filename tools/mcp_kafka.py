#!/usr/bin/env python
import asyncio
import base64
import duckdb
import io
import json
import logging
import os
import tempfile

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

from mcp.server.fastmcp import FastMCP
from kafka import KafkaAdminClient
from kafka.admin import ConfigResource, ConfigResourceType
from pydantic import BaseModel, Field
from typing import Annotated, Literal, Optional

# Try to import term-image for terminal display
try:
    from term_image.image import from_file
    TERM_IMAGE_AVAILABLE = True
except ImportError:
    TERM_IMAGE_AVAILABLE = False

MCP_SERVER_NAME="mcp_kafka"
DB_FILE="db-kafka.tmp"

KAFKA_BOOTSTRAP_SERVERS=["localhost:9092"]

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(MCP_SERVER_NAME)

# Initialize MCP server
mcp = FastMCP(MCP_SERVER_NAME)

def create_database() -> duckdb.DuckDBPyConnection:
    db = duckdb.connect(DB_FILE)
    db.execute("INSTALL tributary FROM community; LOAD tributary;")
    return db

# Initialize database for persistence
db = create_database()

def create_admin_client() -> KafkaAdminClient:
    log.info("Creating Kakfa client connection")

    try:
        admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, client_id="mcp-kafka")
        # Test the connection
        cluster_metadata = admin.describe_cluster()
        log.info(f"Successfully connected to Kafka server version {cluster_metadata}")
        return admin
    except Exception as e:
        log.error(f"Failed to connect to Kafka: {str(e)}")
        raise

# Initialize admin client
admin = create_admin_client()

# Initialize schema cache, hardcoded for now
schemas = { 
    "lineitem": {
        "timestamp": "varchar",
        "order_id": "varchar",
        "part_id": "varchar"
    }
}

class ConfigResourceInput(BaseModel):
    """Pydantic model representing a Kakfa ConfigResource"""
    resource_type: Annotated[
        Literal["BROKER", "TOPIC"], 
        Field(description="Type of resource: BROKER or TOPIC")
    ]

    broker_node_id_or_topic_name: Annotated[int | str, Field(description="Resource name (broker node ID integer or Kakfa topic name string)")]

    configs: Annotated[
        dict[str, str] | None,
        Field(default=None, description="Configuration key-value pairs")
    ] = None

    def to_config_resource(self) -> ConfigResource:
        """Convert to kafka.admin.ConfigResource"""
        resource_type_map = {
            "BROKER": ConfigResourceType.BROKER,
            "TOPIC": ConfigResourceType.TOPIC,
        }
        return ConfigResource(
            resource_type=resource_type_map[self.resource_type],
            name=self.broker_node_id_or_topic_name,
            configs=self.configs
        )

@mcp.tool()
async def list_topics() -> str:
    """List available Kafka topics"""
    result = await asyncio.get_event_loop().run_in_executor(None, admin.list_topics)
    return as_json(result)

@mcp.tool()
async def create_topics(new_topics: list[str]) -> str:
    """Create new Kafka topics"""
    result = await asyncio.get_event_loop().run_in_executor(None, admin.create_topics, new_topics)
    return as_json(result)

@mcp.tool()
async def describe_cluster() -> str:
    """Describe cluster-wide metadata such as the list of brokers, the controller ID, and the cluster ID."""
    result = await asyncio.get_event_loop().run_in_executor(None, admin.describe_cluster)
    return as_json(result)

@mcp.tool()
async def describe_configs(resource_input: list[ConfigResourceInput]) -> list[dict]:
    """Describe configuration for one or more Kafka resources."""
    config_resources = [r.to_config_resource() for r in resource_input]
    result = await asyncio.get_event_loop().run_in_executor(None, admin.describe_configs, config_resources)

    # convert result to list of dicts
    resources = [r.to_object()['resources'] for r in result]
    return resources

@mcp.tool()
def describe_topic_schema(topic: str) -> dict:
    """Describe the schema of a Kafka topic's messages."""
    return schemas[topic]

@mcp.tool()
async def create_topic_table(topic: str) -> bool:
    """Create a table view over the topic's messages."""
    with db.cursor() as cursor:
        cursor.execute(f"""
            CREATE VIEW IF NOT EXISTS {topic}_raw AS
                SELECT *
                EXCLUDE message,
                decode(message)::json AS message
                FROM tributary_scan_topic('{topic}', "bootstrap.servers" := '{",".join(KAFKA_BOOTSTRAP_SERVERS)}');
        """)

        schema = schemas[topic]
        projection = ','.join([f"(message ->> '$.{attr}'::{type_name}) AS {attr}" for attr, type_name in schema.items()])

        view = f"""
            CREATE VIEW IF NOT EXISTS {topic} AS
                SELECT {projection}
                FROM {topic}_raw
        """
        log.debug(view)
        cursor.execute(view)
        return True

@mcp.tool()
async def query_topic_table(query: str) -> str:
    """Query the topic table as SQL and return results as JSON.

    Returns a JSON array of query results that can be passed to generate_plot().
    Each row is represented as a list of values.

    Args:
        query: SQL query to execute against the topic table

    Returns:
        JSON string containing array of rows, where each row is a list of values
    """
    log.info(f"Running query: {query}")
    with db.cursor() as cursor:
        results = cursor.sql(query).fetchall()
        # Convert to JSON string for agent consumption
        return json.dumps([list(row) for row in results])

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
    log.info(f"Generating {plot_type} plot")

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

def as_json(result, transform=lambda x: x) -> str:
    # Convert newline-separated string to list and trim whitespace
    if isinstance(result, str):
        xs = [transform(x).strip() for x in result.strip().split("\n")]
    elif isinstance(result, list):
        xs = [transform(x) for x in result]
    else:
        xs = [result]
    return json.dumps(xs)

def run_stdio_server():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    run_stdio_server()
