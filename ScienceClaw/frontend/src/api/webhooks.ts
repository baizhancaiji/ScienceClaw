/**
 * Webhook management API (via task-service).
 */
import { taskClient } from './taskClient';

export interface Webhook {
  id: string;
  name: string;
  type: 'feishu' | 'dingtalk' | 'wecom';
  url: string;
  created_at?: string;
  updated_at?: string;
}

export interface WebhookCreatePayload {
  name: string;
  type: string;
  url: string;
}

export interface WebhookUpdatePayload {
  name?: string;
  type?: string;
  url?: string;
}

export async function listWebhooks(): Promise<Webhook[]> {
  const { data } = await taskClient.get<Webhook[]>('/webhooks');
  return Array.isArray(data) ? data : [];
}

export async function createWebhook(payload: WebhookCreatePayload): Promise<Webhook> {
  const { data } = await taskClient.post<Webhook>('/webhooks', payload);
  return data;
}

export async function updateWebhook(id: string, payload: WebhookUpdatePayload): Promise<Webhook> {
  const { data } = await taskClient.put<Webhook>(`/webhooks/${id}`, payload);
  return data;
}

export async function deleteWebhook(id: string): Promise<void> {
  await taskClient.delete(`/webhooks/${id}`);
}

export async function testWebhook(id: string): Promise<{ success: boolean; message: string }> {
  const { data } = await taskClient.post<{ success: boolean; message: string }>(`/webhooks/${id}/test`);
  return data;
}
