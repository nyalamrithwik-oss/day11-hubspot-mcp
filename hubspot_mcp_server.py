"""
HubSpot CRM MCP Server
Day 11: HubSpot MCP integration

Provides 5 tools to manage HubSpot contacts and deals via MCP.
"""

import asyncio
import logging
import os
import json
import sys
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Windows asyncio fix - CRITICAL!
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Load environment
load_dotenv()

# Logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("hubspot-mcp")

# MCP app
app = Server("hubspot-mcp-server")

# HubSpot configuration
HUBSPOT_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN", "")
HUBSPOT_BASE = "https://api.hubapi.com"
HEADERS_TEMPLATE = {
    "Content-Type": "application/json"
}

# Rate limit config (basic client-side throttle)
MAX_RPS = int(os.getenv("MAX_REQUESTS_PER_SECOND", "10"))


@app.list_tools()
async def list_tools() -> List[Tool]:
    """Register HubSpot tools."""
    return [
        Tool(
            name="create_contact",
            description="Create a new contact in HubSpot",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "firstname": {"type": "string"},
                    "lastname": {"type": "string"},
                    "phone": {"type": "string"},
                    "company": {"type": "string"}
                },
                "required": ["email"]
            }
        ),
        Tool(
            name="search_contacts",
            description="Search contacts by query term",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_contact",
            description="Get full contact details by ID",
            inputSchema={
                "type": "object",
                "properties": {"contact_id": {"type": "string"}},
                "required": ["contact_id"]
            }
        ),
        Tool(
            name="update_contact",
            description="Update a contact's properties",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string"},
                    "properties": {"type": "object"}
                },
                "required": ["contact_id", "properties"]
            }
        ),
        Tool(
            name="create_deal",
            description="Create a new deal",
            inputSchema={
                "type": "object",
                "properties": {
                    "dealname": {"type": "string"},
                    "amount": {"type": "number"},
                    "dealstage": {"type": "string"},
                    "pipeline": {"type": "string"}
                },
                "required": ["dealname"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Dispatch MCP tool calls to handlers."""
    try:
        if not HUBSPOT_TOKEN:
            return [TextContent(type="text", text="Error: HUBSPOT_ACCESS_TOKEN not configured.")]

        if name == "create_contact":
            return await handle_create_contact(arguments)
        if name == "search_contacts":
            return await handle_search_contacts(arguments)
        if name == "get_contact":
            return await handle_get_contact(arguments)
        if name == "update_contact":
            return await handle_update_contact(arguments)
        if name == "create_deal":
            return await handle_create_deal(arguments)

        return [TextContent(type="text", text=f"Unknown tool: {name}" )]

    except Exception as e:
        logger.exception("Unexpected error in call_tool")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _request(method: str, path: str, json_data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
    """Helper for HTTP requests with common headers and error handling."""
    headers = {**HEADERS_TEMPLATE, "Authorization": f"Bearer {HUBSPOT_TOKEN}"}
    url = f"{HUBSPOT_BASE}{path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(method, url, headers=headers, json=json_data, params=params)
        except httpx.RequestError as e:
            logger.error("Request error: %s", e)
            raise

    if response.status_code >= 400:
        logger.error("HubSpot API error %s: %s", response.status_code, response.text)
        raise Exception(f"HubSpot API {response.status_code}: {response.text}")

    return response.json()


async def handle_create_contact(arguments: Dict[str, Any]) -> List[TextContent]:
    """Create a HubSpot contact and return ID and message."""
    email = arguments.get("email")
    if not email:
        return [TextContent(type="text", text="Missing required parameter: email")]

    properties = {
        "email": email,
        "firstname": arguments.get("firstname"),
        "lastname": arguments.get("lastname"),
        "phone": arguments.get("phone"),
        "company": arguments.get("company")
    }
    # remove None values
    properties = {k: v for k, v in properties.items() if v is not None}

    body = {"properties": properties}

    try:
        data = await _request("POST", "/crm/v3/objects/contacts", json_data=body)
        contact_id = data.get("id")
        text = f"Contact created: id={contact_id} | email={email}"
        return [TextContent(type="text", text=text)]
    except Exception as e:
        logger.error("create_contact failed: %s", e)
        return [TextContent(type="text", text=f"create_contact error: {str(e)}")]


async def handle_search_contacts(arguments: Dict[str, Any]) -> List[TextContent]:
    """Search contacts using HubSpot search endpoint."""
    query = arguments.get("query")
    limit = int(arguments.get("limit", 10))
    if not query:
        return [TextContent(type="text", text="Missing required parameter: query")]

    body = {
        "filterGroups": [
            {
                "filters": [
                    {"value": query, "propertyName": "email", "operator": "CONTAINS_TOKEN"}
                ]
            }
        ],
        "properties": ["email", "firstname", "lastname"],
        "limit": limit
    }

    try:
        data = await _request("POST", "/crm/v3/objects/contacts/search", json_data=body)
        results = data.get("results", [])
        items = []
        for r in results:
            pid = r.get("id")
            props = r.get("properties", {})
            name = f"{props.get('firstname','')} {props.get('lastname','')}".strip()
            items.append({"id": pid, "email": props.get("email"), "name": name})

        text = f"Found {len(items)} contacts for query '{query}':\n" + json.dumps(items, indent=2)
        return [TextContent(type="text", text=text)]
    except Exception as e:
        logger.error("search_contacts failed: %s", e)
        return [TextContent(type="text", text=f"search_contacts error: {str(e)}")]


async def handle_get_contact(arguments: Dict[str, Any]) -> List[TextContent]:
    """Retrieve full contact details by id."""
    contact_id = arguments.get("contact_id")
    if not contact_id:
        return [TextContent(type="text", text="Missing required parameter: contact_id")]

    try:
        data = await _request("GET", f"/crm/v3/objects/contacts/{contact_id}")
        text = f"Contact {contact_id}:\n" + json.dumps(data, indent=2)
        return [TextContent(type="text", text=text)]
    except Exception as e:
        logger.error("get_contact failed: %s", e)
        return [TextContent(type="text", text=f"get_contact error: {str(e)}")]


async def handle_update_contact(arguments: Dict[str, Any]) -> List[TextContent]:
    """Update contact properties by id."""
    contact_id = arguments.get("contact_id")
    properties = arguments.get("properties")
    if not contact_id or not properties:
        return [TextContent(type="text", text="Missing required parameters: contact_id and properties")]

    body = {"properties": properties}
    try:
        data = await _request("PATCH", f"/crm/v3/objects/contacts/{contact_id}", json_data=body)
        text = f"Contact updated: id={contact_id}\n" + json.dumps(data.get('properties', {}), indent=2)
        return [TextContent(type="text", text=text)]
    except Exception as e:
        logger.error("update_contact failed: %s", e)
        return [TextContent(type="text", text=f"update_contact error: {str(e)}")]


async def handle_create_deal(arguments: Dict[str, Any]) -> List[TextContent]:
    """Create a deal and return id and confirmation."""
    dealname = arguments.get("dealname")
    if not dealname:
        return [TextContent(type="text", text="Missing required parameter: dealname")]

    properties = {"dealname": dealname}
    if arguments.get("amount") is not None:
        properties["amount"] = str(arguments.get("amount"))
    if arguments.get("dealstage"):
        properties["dealstage"] = arguments.get("dealstage")
    if arguments.get("pipeline"):
        properties["pipeline"] = arguments.get("pipeline")

    body = {"properties": properties}
    try:
        data = await _request("POST", "/crm/v3/objects/deals", json_data=body)
        deal_id = data.get("id")
        text = f"Deal created: id={deal_id} | name={dealname}"
        return [TextContent(type="text", text=text)]
    except Exception as e:
        logger.error("create_deal failed: %s", e)
        return [TextContent(type="text", text=f"create_deal error: {str(e)}")]


async def main():
    logger.info("Starting HubSpot MCP Server...")
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
