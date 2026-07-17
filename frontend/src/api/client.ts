const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function getInitData(): string {
  return (window as any).Telegram?.WebApp?.initData || '';
}

export async function apiFetch(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Init-Data': getInitData(),
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err: any = new Error(body.detail || `Error ${res.status}`);
    err.status = res.status;
    err.detail = body.detail;
    throw err;
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  me: () => apiFetch('/users/me'),
  dashboard: () => apiFetch('/analytics/dashboard'),
  activity: () => apiFetch('/analytics/activity'),

  telegramStatus: () => apiFetch('/auth/status'),
  loginStart: (phone: string) =>
    apiFetch('/auth/login-start', { method: 'POST', body: JSON.stringify({ phone }) }),
  loginComplete: (data: any) =>
    apiFetch('/auth/login-complete', { method: 'POST', body: JSON.stringify(data) }),

  syncCommunities: () => apiFetch('/communities/sync', { method: 'POST' }),
  listCommunities: (q?: string) => apiFetch(`/communities${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  updateCommunity: (id: number, data: any) =>
    apiFetch(`/communities/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  listPosts: () => apiFetch('/posts'),
  createPost: (data: any) => apiFetch('/posts', { method: 'POST', body: JSON.stringify(data) }),
  updatePost: (id: number, data: any) =>
    apiFetch(`/posts/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deletePost: (id: number) => apiFetch(`/posts/${id}`, { method: 'DELETE' }),
  previewPost: (id: number, variables: Record<string, string>) =>
    apiFetch(`/posts/${id}/preview`, { method: 'POST', body: JSON.stringify({ variables }) }),

  listCampaigns: () => apiFetch('/campaigns'),
  createCampaign: (data: any) => apiFetch('/campaigns', { method: 'POST', body: JSON.stringify(data) }),
  executeOne: (campaignId: number, communityId: number) =>
    apiFetch(`/campaigns/${campaignId}/execute-one?community_id=${communityId}`, { method: 'POST' }),
};
