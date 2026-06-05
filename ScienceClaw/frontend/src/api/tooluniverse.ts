import { apiClient } from './client';
import { i18n } from '../composables/useI18n';
import type { JsonObject, JsonValue } from '../types/json';

function _lang(): string {
  return i18n.global.locale.value || 'en';
}

export interface TUTool {
  name: string;
  display_name?: string;
  description: string;
  category: string;
  category_zh?: string;
  inventory_main_category?: string;
  inventory_sub_category?: string;
  inventory_availability?: string;
  inventory_reason?: string;
  param_count: number;
  required_params?: string[];
  has_examples?: boolean;
  has_return_schema?: boolean;
}

export interface TUToolSpec {
  name: string;
  display_name?: string;
  description: string;
  parameters: {
    type: string;
    properties: Record<string, {
      type: string;
      description: string;
      required?: boolean;
      enum?: string[];
    }>;
    required?: string[];
  };
  test_examples: JsonObject[];
  return_schema: unknown;
  category: string;
  category_zh?: string;
  inventory_main_category?: string;
  inventory_sub_category?: string;
  inventory_availability?: string;
  inventory_reason?: string;
  source_file: string;
}

export interface TUCategory {
  name: string;
  name_zh?: string;
  main_category?: string;
  count: number;
}

export async function listTUTools(search?: string, category?: string): Promise<{
  tools: TUTool[];
  total: number;
  categories: string[];
}> {
  const params: Record<string, string> = { lang: _lang() };
  if (search) params.search = search;
  if (category) params.category = category;
  const resp = await apiClient.get('/tooluniverse/tools', { params });
  return resp.data;
}

export async function getTUToolSpec(toolName: string): Promise<TUToolSpec> {
  const resp = await apiClient.get(`/tooluniverse/tools/${encodeURIComponent(toolName)}`, {
    params: { lang: _lang() },
  });
  return resp.data;
}

export async function runTUTool(toolName: string, args: Record<string, JsonValue>): Promise<{
  success: boolean;
  result: unknown;
}> {
  const resp = await apiClient.post(`/tooluniverse/tools/${encodeURIComponent(toolName)}/run`, {
    arguments: args,
  });
  return resp.data;
}

export async function listTUCategories(): Promise<TUCategory[]> {
  const resp = await apiClient.get('/tooluniverse/categories', {
    params: { lang: _lang() },
  });
  return resp.data.categories;
}
