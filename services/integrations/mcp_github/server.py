"""
GitHub MCP Server - Phase 8.

Built using the REAL MCP SDK (mcp package).
This implements the actual Model Context Protocol with proper handshake.
"""
import os
import json
import subprocess
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
from mcp.types import ListToolsResult, CallToolResult

# GitHub token from environment
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


async def list_tools_handler(ctx, params):
    """Handle list_tools request."""
    return ListToolsResult(
        tools=[
            Tool(
                name="list_repos",
                description="List GitHub repositories accessible to the authenticated user",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="get_repo",
                description="Get information about a specific GitHub repository",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"}
                    },
                    "required": ["owner", "repo"]
                }
            ),
            Tool(
                name="import_repo",
                description="Clone and import a GitHub repository for use in the build system",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "target_path": {"type": "string"}
                    },
                    "required": ["owner", "repo"]
                }
            )
        ]
    )


async def call_tool_handler(ctx, params):
    """Handle call_tool request."""
    name = params.name
    arguments = params.arguments or {}
    
    if name == "list_repos":
        result = list_repos()
    elif name == "get_repo":
        result = get_repo(arguments.get("owner"), arguments.get("repo"))
    elif name == "import_repo":
        result = import_repo(
            arguments.get("owner"),
            arguments.get("repo"),
            arguments.get("target_path")
        )
    else:
        result = {"error": f"Unknown tool: {name}"}
    
    return CallToolResult(
        content=[TextContent(type="text", text=str(result))]
    )


def list_repos() -> dict:
    """List repositories via gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "repo", "list", "--limit", "20", "--json", "name,owner,description,url"],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "GITHUB_TOKEN": GITHUB_TOKEN}
        )
        if result.returncode == 0:
            return {"status": "success", "repos": json.loads(result.stdout)}
        else:
            return {"status": "error", "message": result.stderr}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_repo(owner: str, repo: str) -> dict:
    """Get repository info via gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "repo", "view", f"{owner}/{repo}", "--json", "name,owner,description,url,defaultBranchRef"],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "GITHUB_TOKEN": GITHUB_TOKEN}
        )
        if result.returncode == 0:
            return {"status": "success", "repo": json.loads(result.stdout)}
        else:
            return {"status": "error", "message": result.stderr}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def import_repo(owner: str, repo: str, target_path: str = None) -> dict:
    """Clone and import a repository."""
    if target_path is None:
        target_path = f"/tmp/repos/{owner}/{repo}"
    
    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        clone_url = f"https://{GITHUB_TOKEN}@github.com/{owner}/{repo}.git"
        result = subprocess.run(
            ["git", "clone", "--depth", "1", clone_url, target_path],
            capture_output=True, text=True, timeout=60
        )
        
        if result.returncode == 0:
            info = get_repo(owner, repo)
            return {
                "status": "success",
                "message": f"Repository {owner}/{repo} imported to {target_path}",
                "path": target_path,
                "repo": info.get("repo")
            }
        else:
            return {"status": "error", "message": result.stderr}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Create the MCP server with handlers
server = Server(
    "github-mcp",
    version="1.0.0",
    on_list_tools=list_tools_handler,
    on_call_tool=call_tool_handler
)


async def main():
    """Run the MCP server using stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
