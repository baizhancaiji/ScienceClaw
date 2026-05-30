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
