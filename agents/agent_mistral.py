#!/usr/bin/env python
import asyncio
import logging
import mistralai
import os
import readline

from contextlib import asynccontextmanager
from dataclasses import dataclass
from mcp import StdioServerParameters
from mistralai import Mistral
from mistralai.extra.run.context import RunContext
from mistralai.extra.mcp.stdio import MCPClientSTDIO
from mistralai.types import BaseModel
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("agent_mistral")

# Set the current working directory
cwd = Path(__file__).parent

# Define the expected output format for the results
@dataclass
class AgentOutput(BaseModel):
    result: str

# An agent with a running context for conversations and tools
@dataclass
class AgentContext:
    client: Mistral
    run_context: RunContext

    async def query(self, message):
        # Run the agent with a query added to the conversation in the context
        run_result = await self.client.beta.conversations.run_async(
            run_ctx=self.run_context,
            inputs=message,
        )
        print(f"🤖: {run_result.output_as_model}")

# An agency that can create agents with contexts
class Agency:
    def __init__(self):
        self.api_key = os.environ["MISTRAL_API_KEY"]
        self.model= "mistral-medium-latest"
        self.client = Mistral(self.api_key)

        # MCP server parameters for Kafka operations
        self.mcp_kafka_params = StdioServerParameters(
            command="python",
            args=[str((cwd / "../tools/mcp_kafka.py").resolve())],
            env=None,
        )

        # MCP server parameters for plotting
        self.mcp_plot_params = StdioServerParameters(
            command="python",
            args=[str((cwd / "../tools/mcp_plot.py").resolve())],
            env=None,
        )

        self.agent = self.client.beta.agents.create(
            model=self.model,
            name="Kafka operator with plotting",
            instructions="You are able to operate Kafka using the tools provided. "
                        "You can query Kafka topics and visualize the results with plots. "
                        "When asked to create plots, first use query_topic_table to get the data, "
                        "then use generate_plot to visualize it.",
            description="",
        )

    @asynccontextmanager
    async def agent_context(self) -> AgentContext:
        async with RunContext(
            agent_id=self.agent.id,
            output_format=AgentOutput,
            continue_on_fn_error=True,
        ) as run_ctx:
            # Create and register MCP clients for both Kafka and plotting
            mcp_kafka_client = MCPClientSTDIO(stdio_params=self.mcp_kafka_params)
            mcp_plot_client = MCPClientSTDIO(stdio_params=self.mcp_plot_params)

            await run_ctx.register_mcp_client(mcp_client=mcp_kafka_client)
            await run_ctx.register_mcp_client(mcp_client=mcp_plot_client)

            try:
                yield AgentContext(self.client, run_ctx)
            finally:
                log.info("Finishing agent context.")

def collect_user_input():
    print("")
    return input("😐: ")

async def main() -> None:
    agency = Agency()
    async with agency.agent_context() as agent:
        done = False
        while not done:
            try:
                message = collect_user_input()
                await agent.query(message)
            except (EOFError, KeyboardInterrupt) as e:
                log.info(f"Recieved {e.__class__.__name__}. Existing.")
                done = True
    print("\n🤖: 👋")

if __name__ == "__main__":
    asyncio.run(main())

