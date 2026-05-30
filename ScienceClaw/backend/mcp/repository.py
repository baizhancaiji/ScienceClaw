from typing import Any

from backend.mongodb.db import db


MCP_SERVERS_COLLECTION = "mcp_servers"
MCP_TOOLS_COLLECTION = "mcp_tools"


async def create_server(doc: dict[str, Any]) -> dict[str, Any]:
    await db.get_collection(MCP_SERVERS_COLLECTION).insert_one(doc)
    return dict(doc)


async def get_server(server_id: str, user_id: str) -> dict[str, Any] | None:
    return await db.get_collection(MCP_SERVERS_COLLECTION).find_one(
        {"_id": server_id, "user_id": user_id}
    )


async def list_servers(user_id: str) -> list[dict[str, Any]]:
    cursor = db.get_collection(MCP_SERVERS_COLLECTION).find({"user_id": user_id})
    return await cursor.to_list(length=None)


async def update_server(
    server_id: str,
    user_id: str,
    patch: dict[str, Any],
) -> dict[str, Any] | None:
    if patch:
        await db.get_collection(MCP_SERVERS_COLLECTION).update_one(
            {"_id": server_id, "user_id": user_id},
            {"$set": patch},
        )
    return await get_server(server_id, user_id)


async def delete_server(server_id: str, user_id: str) -> None:
    await db.get_collection(MCP_SERVERS_COLLECTION).delete_one(
        {"_id": server_id, "user_id": user_id}
    )
    await db.get_collection(MCP_TOOLS_COLLECTION).delete_many(
        {"server_id": server_id, "user_id": user_id}
    )


async def list_tools_by_server(server_id: str, user_id: str) -> list[dict[str, Any]]:
    raise NotImplementedError("list_tools_by_server is reserved for a later MCP batch")


async def list_enabled_tools_by_user(user_id: str) -> list[dict[str, Any]]:
    raise NotImplementedError("list_enabled_tools_by_user is reserved for a later MCP batch")


async def upsert_tools_from_remote(
    server_id: str,
    user_id: str,
    tools: list[dict[str, Any]],
) -> None:
    raise NotImplementedError("upsert_tools_from_remote is reserved for a later MCP batch")


async def mark_removed_tools(
    server_id: str,
    user_id: str,
    missing_tool_names: list[str],
) -> None:
    raise NotImplementedError("mark_removed_tools is reserved for a later MCP batch")


async def toggle_server_enabled(server_id: str, user_id: str, enabled: bool) -> None:
    raise NotImplementedError("toggle_server_enabled is reserved for a later MCP batch")


async def toggle_tool_enabled(tool_id: str, user_id: str, enabled: bool) -> None:
    raise NotImplementedError("toggle_tool_enabled is reserved for a later MCP batch")


async def touch_verify_result(
    server_id: str,
    user_id: str,
    result: dict[str, Any],
) -> None:
    raise NotImplementedError("touch_verify_result is reserved for a later MCP batch")
