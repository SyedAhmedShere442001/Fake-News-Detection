async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`)
  return data
}

export const api = {
  health: () => request('/api/health'),
  predict: (text) => request('/api/predict', { method: 'POST', body: JSON.stringify({ text }) }),
  analyzeUrl: (url) => request('/api/analyze-url', { method: 'POST', body: JSON.stringify({ url }) }),
  history: (limit = 50) => request(`/api/history?limit=${limit}`),
  deleteHistory: (id) => request(`/api/history/${id}`, { method: 'DELETE' }),
  analytics: () => request('/api/analytics'),
}
