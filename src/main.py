"""
CLI entry point for the DeepAgent + MCP project.

Supports two modes:
  1. Single-shot:   python src/main.py "What is 12 times 7?"
  2. Interactive:    python src/main.py
     (starts a REPL loop with multi-turn memory via the harness checkpointer)

Make sure the MCP server is running first:
    python src/mcp_server.py
"""

import asyncio
import sys

from agent import build_agent


async def single_shot(prompt: str):
    """Build the agent and run a single prompt."""
    from agent import run_agent

    print(f"Prompt: {prompt}\n")
    answer = await run_agent(prompt)
    print("Agent response:")
    print(answer)


async def interactive():
    """Multi-turn REPL — conversation state is kept across turns."""
    from langgraph.checkpoint.memory import InMemorySaver

    checkpointer = InMemorySaver()
    agent = await build_agent(checkpointer=checkpointer)
    thread_id = "interactive-session"
    config = {"configurable": {"thread_id": thread_id}}

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  DeepAgent + MCP — Interactive Mode                        ║")
    print("║  Type your prompt and press Enter. Type 'quit' to exit.    ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    while True:
        try:
            prompt = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not prompt:
            continue
        if prompt.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config=config,
        )
        answer = result["messages"][-1].content
        print(f"\nAgent> {answer}\n")


async def main():
    if len(sys.argv) >= 2:
        prompt = " ".join(sys.argv[1:])
        await single_shot(prompt)
    else:
        await interactive()


if __name__ == "__main__":
    asyncio.run(main())
