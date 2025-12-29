# HubSpot CRM MCP Server

   ![Python](https://img.shields.io/badge/python-3.11-blue)
   ![MCP](https://img.shields.io/badge/MCP-1.25.0-green)
   ![Tests](https://img.shields.io/badge/tests-5%2F5%20passing-brightgreen)
   ![License](https://img.shields.io/badge/license-MIT-blue)
   
## 1. Project Overview
A production-ready MCP server that exposes 5 essential HubSpot CRM tools for automation, integration, and AI workflows. Built for Claude Desktop and portfolio demonstration.

## 2. Features
- **create_contact**: Add new contacts to HubSpot
- **search_contacts**: Find contacts by email or name
- **get_contact**: Retrieve full contact details by ID
- **update_contact**: Update contact properties
- **create_deal**: Create new sales opportunities (deals)

## 3. Tech Stack
- Python 3.11
- MCP 1.25.0
- httpx (async)
- HubSpot API v3
- dotenv, pydantic, aiosqlite

## 4. Setup Instructions
### HubSpot Account & Private App
1. Sign up at [HubSpot Developer Portal](https://app.hubspot.com/signup-hubspot/developers)
2. Create a private app with these scopes:
   - crm.objects.contacts.read/write
   - crm.objects.deals.read/write
   - crm.schemas.contacts.read
   - crm.schemas.deals.read
3. Copy your private app token (starts with `pat-...`)

### Install & Configure
```powershell
cd C:\Users\nyala\OneDrive\RAG\week2-mcp\day11-hubspot-mcp
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Configure .env
Copy `.env.example` to `.env` and paste your HubSpot token:
```
HUBSPOT_ACCESS_TOKEN=pat-...
SERVER_PORT=8001
LOG_LEVEL=INFO
MAX_REQUESTS_PER_SECOND=10
```

## 5. Testing
Run the test suite to verify all 5 tools:
```powershell
python test_hubspot.py
```
**Expected:** All API calls succeed, 5/5 tests passing, output includes contact and deal creation, search, update, and retrieval.

## 6. Claude Desktop Integration
- Add this server to your Claude config as an MCP tool provider.
- Example config:
```json
{
  "name": "HubSpot CRM",
  "executable": "python hubspot_mcp_server.py",
  "tools": ["create_contact", "search_contacts", "get_contact", "update_contact", "create_deal"]
}
```

## 7. Usage Examples
- **Create Contact:**
  > "Add a new contact: John Doe, john@example.com, 555-1234, Acme Corp."
- **Search Contacts:**
  > "Find all contacts with email containing 'test'"
- **Get Contact:**
  > "Show details for contact ID 123456"
- **Update Contact:**
  > "Update phone for contact 123456 to 555-9999"
- **Create Deal:**
  > "Create a deal: 'Big Sale', $5000, stage: appointmentscheduled, pipeline: default"

## 8. Troubleshooting
- 401 Unauthorized: Check your HubSpot token in `.env`
- 429 Rate Limit: Wait and retry, or lower request frequency
- Validation errors: Ensure all required fields are provided

## 9. Author
Rithwik Nyalam, December 28, 2025

## 10. License
MIT License
