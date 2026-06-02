import axios, { type AxiosError, type AxiosResponse } from 'axios';

import { clearStoredTokens, getStoredToken } from './auth';

export const TASK_SERVICE_BASE =
  (import.meta as any).env?.VITE_TASK_SERVICE_URL ?? '';

export const TASK_SERVICE_BASE_URL = TASK_SERVICE_BASE || '/task-service';

export interface TaskServiceError {
  code: number;
  message: string;
  details?: unknown;
}

export const taskClient = axios.create({
  baseURL: TASK_SERVICE_BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

taskClient.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function normalizeTaskServiceError(error: AxiosError): TaskServiceError {
  const fallback: TaskServiceError = {
    code: 500,
    message: 'Task service request failed',
  };

  if (!error.response) {
    return error.request
      ? { code: 503, message: 'Task service network error' }
      : fallback;
  }

  const response = error.response as AxiosResponse<unknown>;
  const details = response.data;
  const status = response.status || 500;
  const messageFromData =
    details && typeof details === 'object'
      ? (details as { detail?: unknown; message?: unknown; msg?: unknown }).detail
        ?? (details as { message?: unknown }).message
        ?? (details as { msg?: unknown }).msg
      : undefined;

  return {
    code: status,
    message: typeof messageFromData === 'string'
      ? messageFromData
      : response.statusText || fallback.message,
    details,
  };
}

taskClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      clearStoredTokens();
      window.dispatchEvent(new CustomEvent('auth:logout'));
    }

    return Promise.reject(normalizeTaskServiceError(error));
  },
);

export function isTaskServiceConfigured(): boolean {
  return !!TASK_SERVICE_BASE_URL;
}
