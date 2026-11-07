import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_agent_demo():
    # Point the MCP Client at your server.py script using your current Python interpreter
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["server.py"],
    )

    print("1. [Agent] Connecting to MCP Server over stdio...")
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize MCP handshake
            await session.initialize()
            print("   -> Handshake complete!\n")

            # Discover registered tools dynamically
            tools_result = await session.list_tools()
            print(f"2. [Agent] Discovered {len(tools_result.tools)} MCP Tools:")
            for tool in tools_result.tools:
                print(f"   - {tool.name}: {tool.description.strip().splitlines()[0]}")
            print()

            # Step A: Agent inspects the database schema
            print("3. [Agent -> Tool: inspect_database_schema]")
            schema_res = await session.call_tool("inspect_database_schema", {})
            print(schema_res.content[0].text)
            print()

            # Step B: Agent executes a parameterized SQL query
            sql = "SELECT name, role, salary FROM employees WHERE department = 'AI Engineering' ORDER BY salary DESC"
            print(f"4. [Agent -> Tool: query_database] Executing: {sql}")
            db_res = await session.call_tool("query_database", {"sql_query": sql})
            print(db_res.content[0].text)
            print()

            # Step C: Agent tests the SQL security guardrail
            bad_sql = "DROP TABLE employees;"
            print(f"5. [Agent -> Tool: query_database] Testing Security Guardrail: {bad_sql}")
            guard_res = await session.call_tool("query_database", {"sql_query": bad_sql})
            print(guard_res.content[0].text)
            print()

            # Step D: Agent fetches live data from an external REST API
            api_url = "https://jsonplaceholder.typicode.com/users/1"
            print(f"6. [Agent -> Tool: fetch_external_api] GET {api_url}")
            api_res = await session.call_tool(
                "fetch_external_api",
                {"endpoint_url": api_url}
            )
            print(api_res.content[0].text)

if __name__ == "__main__":
    asyncio.run(run_agent_demo())