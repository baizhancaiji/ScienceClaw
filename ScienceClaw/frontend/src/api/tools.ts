import { apiClient, type ApiResponse } from './client';

export type ToolSourceType = 'tooluniverse' | 'https_mcp' | 'external_python_tool';

export interface ToolSearchRequest {
  query: string;
  source_type?: ToolSourceType;
  category_zh?: string;
  limit?: number;
  debug?: boolean;
}

export interface ToolSearchResult {
  tool_ref: string;
  name: string;
  cat_zh: string;
  why: string;
  score?: number;
  source_type?: ToolSourceType;
  hit_fields?: string[];
}

export interface ToolInfoResult {
  tool_ref: string;
  source_type: ToolSourceType;
  name: string;
  display_name?: string;
  description?: string;
  cat_zh: string;
  input_schema: Record<string, unknown>;
  examples: unknown[];
  limitations?: string[];
  provider?: string;
  metadata?: Record<string, unknown>;
}

export interface ToolRunRequest {
  tool_ref: string;
  arguments: Record<string, unknown>;
}

export interface ToolRunResult {
  tool_ref: string;
  ok: boolean;
  result?: unknown;
  error?: string;
}

export async function searchTools(payload: ToolSearchRequest): Promise<ToolSearchResult[]> {
  const response = await apiClient.post<ApiResponse<{ results: ToolSearchResult[] }>>('/tools/search', payload);
  return response.data.data.results;
}

export async function getToolInfo(toolRef: string): Promise<ToolInfoResult> {
  const response = await apiClient.get<ApiResponse<ToolInfoResult>>(`/tools/info/${encodeURIComponent(toolRef)}`);
  return response.data.data;
}

export async function runTool(payload: ToolRunRequest): Promise<ToolRunResult> {
  const response = await apiClient.post<ApiResponse<ToolRunResult>>('/tools/run', payload);
  return response.data.data;
}
