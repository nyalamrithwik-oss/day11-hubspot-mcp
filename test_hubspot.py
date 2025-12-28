"""
Simple test runner for HubSpot API calls used in Day 11 exercises.
This script calls HubSpot REST endpoints directly using httpx and the token in .env.
"""
import asyncio
import os
import time
import uuid
import json
from dotenv import load_dotenv
import httpx

load_dotenv()
TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")
BASE = "https://api.hubapi.com"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

async def create_contact(email: str):
    body = {"properties": {"email": email, "firstname": "Test", "lastname": "Runner"}}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{BASE}/crm/v3/objects/contacts", headers=HEADERS, json=body)
        return r

async def search_contacts(query: str):
    body = {"filterGroups": [{"filters": [{"value": query, "propertyName": "email", "operator": "CONTAINS_TOKEN"}]}], "properties": ["email","firstname","lastname"], "limit": 10}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{BASE}/crm/v3/objects/contacts/search", headers=HEADERS, json=body)
        return r

async def get_contact(cid: str):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{BASE}/crm/v3/objects/contacts/{cid}", headers=HEADERS)
        return r

async def update_contact(cid: str):
    body = {"properties": {"phone": "+15555550123"}}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.patch(f"{BASE}/crm/v3/objects/contacts/{cid}", headers=HEADERS, json=body)
        return r

async def create_deal():
    body = {"properties": {"dealname": "Test Deal via script", "amount": "1000"}}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{BASE}/crm/v3/objects/deals", headers=HEADERS, json=body)
        return r

async def run_all():
    if not TOKEN:
        print("HUBSPOT_ACCESS_TOKEN not set in .env. Abort.")
        return 1

    timestamp = int(time.time())
    test_email = f"test_{timestamp}_{uuid.uuid4().hex[:6]}@example.com"

    print(f"Creating contact {test_email}...")
    r1 = await create_contact(test_email)
    print(r1.status_code, r1.text)
    if r1.status_code != 201:
        print("create_contact failed")
        return 1
    cid = r1.json().get("id")

    print("Searching for contacts with 'test'...")
    r2 = await search_contacts("test")
    print(r2.status_code)
    try:
        print(json.dumps(r2.json(), indent=2))
    except Exception:
        print(r2.text)

    print(f"Getting contact {cid}...")
    r3 = await get_contact(cid)
    print(r3.status_code)
    print(r3.text)

    print(f"Updating contact {cid}...")
    r4 = await update_contact(cid)
    print(r4.status_code)
    print(r4.text)

    print("Creating deal...")
    r5 = await create_deal()
    print(r5.status_code)
    print(r5.text)

    print("Tests complete. Consider deleting test data manually if desired.")
    return 0

if __name__ == "__main__":
    code = asyncio.run(run_all())
    exit(code)
