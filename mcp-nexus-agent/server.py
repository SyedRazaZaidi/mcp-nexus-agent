import os
import sqlite3
import json
import urllib.request
import urllib.parse
from typing import Any

# Universal import compatibility for MCP SDK v1.x (FastMCP) and v2.x (MCPServer)
try:
    from mcp.server import MCPServer as HighLevelMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP as HighLevelMCP

mcp = HighLevelMCP("enterprise-data-server")

# Ensure DB is always created in the same folder as server.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "enterprise.db")

def init_and_seed_db():
    """Creates and seeds a local SQLite database for immediate demonstration."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            role TEXT NOT NULL,
            salary REAL NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_metrics (
            metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_name TEXT NOT NULL,
            status TEXT NOT NULL,
            latency_ms INTEGER NOT NULL
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO employees (name, department, role, salary) VALUES (?, ?, ?, ?)",
            [
                ("Ali Khan", "AI Engineering", "Lead ML Architect", 185000),
                ("Sara Ahmed", "Data Science", "NLP Engineer", 145000),
                ("Usman Tariq", "Cloud Ops", "DevOps Specialist", 130000),
                ("Zainab Raza", "AI Engineering", "Computer Vision Engineer", 155000),
            ]
        )
        cursor.executemany(
            "INSERT INTO system_metrics (service_name, status, latency_ms) VALUES (?, ?, ?)",
            [
                ("Auth-Gateway", "HEALTHY", 24),
                ("Vector-DB-Cluster", "HEALTHY", 48),
                ("Inference-Engine-v2", "DEGRADED", 310),
            ]
        )
        conn.commit()
    conn.close()

init_and_seed_db()


# --- TOOL 1: Database Schema Inspector ---
@mcp.tool()
def inspect_database_schema() -> str:
    """List all tables and their column schemas in the enterprise SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
    tables = [{"table": row[0], "ddl": row[1]} for row in cursor.fetchall()]
    conn.close()
    return json.dumps(tables, indent=2)


# --- TOOL 2: Read-Only SQL Query Executor ---
@mcp.tool()
def query_database(sql_query: str) -> str:
    """
    Execute a read-only SQL SELECT query against the enterprise SQLite database.
    Returns rows as a JSON-formatted list of objects.
    """
    cleaned = sql_query.strip().lower()
    if not cleaned.startswith("select"):
        return json.dumps({"error": "Security Policy Violation: Only SELECT statements are permitted."})

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return json.dumps({"row_count": len(rows), "data": rows}, indent=2)
    except Exception as e:
        return json.dumps({"database_error": str(e)})


# --- TOOL 3: External REST API Connector ---
@mcp.tool()
def fetch_external_api(endpoint_url: str, query_params: dict[str, Any] | None = None) -> str:
    """
    Fetch live JSON/text data from an external REST API endpoint via HTTP GET.
    """
    try:
        url = endpoint_url
        if query_params:
            query_string = urllib.parse.urlencode(query_params)
            url = f"{endpoint_url}?{query_string}"
            
        req = urllib.request.Request(url, headers={"User-Agent": "MCP-Enterprise-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=10.0) as response:
            raw_text = response.read().decode("utf-8")
            try:
                parsed = json.loads(raw_text)
                return json.dumps(parsed, indent=2)
            except Exception:
                return raw_text
    except Exception as e:
        return json.dumps({"api_error": str(e)})


if __name__ == "__main__":
    mcp.run()