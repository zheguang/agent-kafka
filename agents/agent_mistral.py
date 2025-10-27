#!/usr/bin/env python
import asyncio
import os

from mcp import StdioServerParameters
from mistralai import Mistral
from mistralai.extra.run.context import RunContext
from mistralai.extra.mcp.stdio import MCPClientSTDIO
from mistralai.types import BaseModel
from pathlib import Path

# Set the current working directory and model to use
cwd = Path(__file__).parent
MODEL = "mistral-large-latest"

async def main() -> None:
    # Initialize the Mistral client with your API key
    api_key = os.environ["MISTRAL_API_KEY"]
    client = Mistral(api_key)

    # Define parameters for the local MCP server
    server_params = StdioServerParameters(
        command="python",
        args=[str((cwd / "../tools/mcp_kafka.py").resolve())],
        env=None,
    )

    # Create an agent 
    agent = client.beta.agents.create(
        model=MODEL,
        name="Kafka operator",
        instructions="You are able to operate Kakfa.",
        description="",
    )

    # Define the expected output format for the results
    class AgentOutput(BaseModel):
        result: str

    # Create a run context for the agent
    async with RunContext(
        agent_id=agent.id,
        output_format=AgentOutput,
        continue_on_fn_error=True,
    ) as run_ctx:

        # Create and register an MCP client with the run context
        mcp_client = MCPClientSTDIO(stdio_params=server_params)
        await run_ctx.register_mcp_client(mcp_client=mcp_client)

        # Run the agent with a query
        run_result = await client.beta.conversations.run_async(
            run_ctx=run_ctx,
            # inputs="Describe metadata of my cluster.",
            # inputs="Show me throughput related configruation parameters of my cluster.",
            # inputs="Can you propose new configuration values for my brokers for higher throughput?",
            inputs="Create a table for topic 'lineitem'. Then select from the topic table 'lineitem' for rows of order id 'o1'",
        )

        # Print the results
        print("All run entries:")
        for entry in run_result.output_entries:
            print(f"{entry}")
            print()
        print(f"Final model: {run_result.output_as_model}")

if __name__ == "__main__":
    asyncio.run(main())

