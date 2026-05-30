import { apiClient, type ApiResponse } from './client';

export type MCPAuthMode = 'none' | 'bearer' | 'headers';
export type MCPVerifyStatus = 'unknown' | 'healthy' | 'error';

export interface MCPMaskedHeader {
  name: string;
  masked_value: string;
}

export interface MCPServer {
  id: string;
  name: string;
  slug: string;
  transport: 'https';
  endpoint_url: string;
  auth_mode: MCPAuthMode;
  enabled: boolean;
  verify_status: MCPVerifyStatus;
  verify_error: string;
  tool_count: number;
  last_verified_at: number | null;
  last_synced_at: number | null;
  has_bearer_token: boolean;
  masked_headers: MCPMaskedHeader[];
  created_at?: number | null;
  updated_at?: number | null;
}

export interface MCPTool {
  id: string;
  server_id: string;
  original_name: string;
  tool_slug: string;
  canonical_name: string;
  display_name: string;
  description: string;
  input_schema_raw: Record<string, unknown>;
  input_schema_normalized: Record<string, unknown>;
  enabled: boolean;
  removed: boolean;
  last_seen_at: number | null;
  created_at?: number | null;
  updated_at?: number | null;
}

export interface MCPVerifyResult extends MCPServer {
  duration_ms: number;
}

export interface MCPRefreshResult extends MCPServer {
  inserted: number;
  updated: number;
  removed: number;
  duration_ms: number;
}

export interface MCPHeaderSecret {
  name: string;
  value: string;
}

export interface CreateMCPServerRequest {
  name: string;
  endpoint_url: string;
  auth_mode: MCPAuthMode;
  bearer_token?: string;
  headers?: MCPHeaderSecret[];
  enabled?: boolean;
  verify_now?: boolean;
}

export interface UpdateMCPServerRequest {
  name?: string;
  endpoint_url?: string;
  auth_mode?: MCPAuthMode;
  bearer_token?: string;
  headers?: MCPHeaderSecret[];
  enabled?: boolean;
}

export async function listMCPServers(): Promise<MCPServer[]> {
  const response = await apiClient.get<ApiResponse<MCPServer[]>>('/mcp/servers');
  return response.data.data;
}

export async function createMCPServer(payload: CreateMCPServerRequest): Promise<MCPServer> {
  const response = await apiClient.post<ApiResponse<MCPServer>>('/mcp/servers', payload);
  return response.data.data;
}

export async function updateMCPServer(serverId: string, payload: UpdateMCPServerRequest): Promise<MCPServer> {
  const response = await apiClient.put<ApiResponse<MCPServer>>(`/mcp/servers/${serverId}`, payload);
  return response.data.data;
}

export async function deleteMCPServer(serverId: string): Promise<{ ok: boolean }> {
  const response = await apiClient.delete<ApiResponse<{ ok: boolean }>>(`/mcp/servers/${serverId}`);
  return response.data.data;
}

export async function setMCPServerEnabled(serverId: string, enabled: boolean): Promise<MCPServer> {
  const response = await apiClient.put<ApiResponse<MCPServer>>(`/mcp/servers/${serverId}/enabled`, { enabled });
  return response.data.data;
}

export async function verifyMCPServer(serverId: string): Promise<MCPVerifyResult> {
  const response = await apiClient.post<ApiResponse<MCPVerifyResult>>(`/mcp/servers/${serverId}/verify`);
  return response.data.data;
}

export async function refreshMCPServerTools(serverId: string): Promise<MCPRefreshResult> {
  const response = await apiClient.post<ApiResponse<MCPRefreshResult>>(`/mcp/servers/${serverId}/refresh-tools`);
  return response.data.data;
}

export async function listMCPServerTools(serverId: string): Promise<MCPTool[]> {
  const response = await apiClient.get<ApiResponse<MCPTool[]>>(`/mcp/servers/${serverId}/tools`);
  return response.data.data;
}

export async function listMCPTools(): Promise<MCPTool[]> {
  const response = await apiClient.get<ApiResponse<MCPTool[]>>('/mcp/tools');
  return response.data.data;
}

export async function setMCPToolEnabled(toolId: string, enabled: boolean): Promise<MCPTool> {
  const response = await apiClient.put<ApiResponse<MCPTool>>(`/mcp/tools/${toolId}/enabled`, { enabled });
  return response.data.data;
}
