const BASE_URL = 'http://localhost:8000';

async function fetchWithTimeout(url, options = {}, timeout = 120000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  
  try {
    console.log(`API Request: ${options.method || 'GET'} ${url}`);
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(id);
    
    console.log(`API Response: ${response.status} ${response.statusText}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('API Error Response:', errorText);
      throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
    }
    
    return response;
  } catch (error) {
    clearTimeout(id);
    console.error('API Fetch Error:', error);
    if (error.name === 'AbortError') {
      throw new Error('Request timed out - the server took too long to respond');
    }
    if (error.message.includes('Failed to fetch')) {
      throw new Error('Cannot connect to server. Is the backend running on http://localhost:8000?');
    }
    throw error;
  }
}

export async function getMetrics(projectId, limit = 50, sort) {
  const url = new URL(`${BASE_URL}/metrics/${projectId}`);
  if (limit) url.searchParams.set('limit', String(limit));
  if (sort) url.searchParams.set('sort', sort);
  const res = await fetchWithTimeout(url);
  return res.json();
}

export async function getRisks(projectId, tier, top = 10) {
  const url = new URL(`${BASE_URL}/risks/${projectId}`);
  if (tier) url.searchParams.set('tier', tier);
  if (top) url.searchParams.set('top', String(top));
  const res = await fetchWithTimeout(url);
  return res.json();
}

export async function getSmells(projectId, severity) {
  const url = new URL(`${BASE_URL}/smells/${projectId}`);
  if (severity) url.searchParams.set('severity', String(severity));
  const res = await fetchWithTimeout(url);
  return res.json();
}

export async function queueGithubRepo(sourceRef) {
  const res = await fetchWithTimeout(`${BASE_URL}/upload/repo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source_type: 'github', source_ref: sourceRef })
  });
  return res.json();
}

export async function startScan(projectId) {
  // Longer timeout for scanning - it can take a while
  const res = await fetchWithTimeout(`${BASE_URL}/scan/project`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId })
  }, 300000); // 5 minutes timeout for scan
  return res.json();
}

export async function getSuggestions(projectId, fileId, limit = 5) {
  const url = new URL(`${BASE_URL}/suggestions/${projectId}/${fileId}`);
  if (limit) url.searchParams.set('limit', String(limit));
  const res = await fetchWithTimeout(url);
  return res.json();
}

export async function exportReport(projectId, sections = []) {
  const res = await fetchWithTimeout(`${BASE_URL}/report/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId, format: 'pdf', sections })
  });
  return res.blob();
}
