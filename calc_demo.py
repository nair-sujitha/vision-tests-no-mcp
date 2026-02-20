import asyncio
from minitap.mobile_use.sdk import Agent
from minitap.mobile_use.sdk.types import AgentProfile
from minitap.mobile_use.sdk.builders import Builders

async def main():
    # Create an agent profile
    default_profile = AgentProfile(
        name="default",
        from_file="llm-config.override.jsonc"
    )

    # Configure the agent
    agent_config = Builders.AgentConfig.with_default_profile(default_profile).build()
    agent = Agent(config=agent_config)

    try:
        # Initialize the agent (connect to the first available device)
        await agent.init()

        # Define a simple task goal
        result = await agent.run_task(
            goal="Open the home depot app and tell me if you can see the search bar on the home page",
            name="calculator_demo"
        )

        # Print the result
        print(f"Result: {result}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Always clean up when finished
        await agent.clean()

if __name__ == "__main__":
    asyncio.run(main())