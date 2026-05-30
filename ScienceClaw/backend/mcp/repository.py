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
    cursor = db.get_collection(MCP_TOOLS_COLLECTION).find(
        {"server_id": server_id, "user_id": user_id}
    )
    return await cursor.to_list(length=None)


async def list_enabled_tools_by_user(user_id: str) -> list[dict[str, Any]]:
    raise NotImplementedError("list_enabled_tools_by_user is reserved for a later MCP batch")


async def upsert_tools_from_remote(
    server_id: str,
    user_id: str,
    tools: list[dict[str, Any]],
) -> dict[str, int]:
    added = 0
    updated = 0
    collection = db.get_collection(MCP_TOOLS_COLLECTION)
    for tool in tools:
        query = {
            "server_id": server_id,
            "user_id": user_id,
            "original_name": tool["original_name"],
        }
        existing = await collection.find_one(query)
        if existing is None:
            await collection.insert_one(tool)
            added += 1
        else:
            patch = dict(tool)
            patch.pop("_id", None)
            patch.pop("enabled", None)
            patch.pop("created_at", None)
            changed = _tool_has_material_changes(existing, patch)
            await collection.update_one(query, {"$set": patch})
            if changed:
                updated += 1
    return {"added": added, "updated": updated}


async def mark_removed_tools(
    server_id: str,
    user_id: str,
    missing_tool_names: list[str],
) -> int:
    if not missing_tool_names:
        return 0
    collection = db.get_collection(MCP_TOOLS_COLLECTION)
    removed = 0
    now_patch = {"removed": True}
    for original_name in missing_tool_names:
        query = {
            "server_id": server_id,
            "user_id": user_id,
            "original_name": original_name,
        }
        existing = await collection.find_one(query)
        if existing is None or existing.get("removed") is True:
            continue
        await collection.update_one(query, {"$set": now_patch})
        removed += 1
    return removed


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


def _tool_has_material_changes(
    existing: dict[str, Any],
    patch: dict[str, Any],
) -> bool:
    for key, value in patch.items():
        if key in {"last_seen_at", "updated_at"}:
            continue
        if existing.get(key) != value:
            return True
    return False
