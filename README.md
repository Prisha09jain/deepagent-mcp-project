# DeepAgent + MCP Tool Calling

A Python-based AI agent project that integrates DeepAgents with the Model Context Protocol (MCP), enabling an LLM to discover and invoke tools exposed by MCP servers.

## Key Features

- **Agent integration:** Uses DeepAgents to create an agent capable of working with external tools.
- **MCP connectivity:** Uses LangChain MCP Adapters to connect to MCP servers and retrieve available tools.
- **Custom MCP server:** Implements an example FastMCP server exposing mathematical tools through a Streamable HTTP endpoint.
- **LLM integration:** Uses Groq for model inference, configurable through environment variables.
- **Modular architecture:** Separates the MCP server, agent configuration, and command-line entry point.
- **Testing:** Includes a basic test suite for checking agent integration.

## Tech Stack

Python, DeepAgents, LangChain MCP Adapters, FastMCP, Model Context Protocol (MCP), and Groq.

## Objective

Explore how AI agents can use standardized tool interfaces to interact with external services, extending LLM applications beyond text generation.
