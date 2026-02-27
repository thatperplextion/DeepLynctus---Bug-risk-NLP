/**
 * DeepLynctus Browser Extension Popup Interface
 * 
 * Main interface logic for the extension popup, handling user interactions,
 * API communication, and repository analysis initiation.
 */

// Global state variables
let currentTab = null;
let repoInfo = null;

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
  // Load saved API URL
  const saved = await chrome.storage.sync.get(['apiUrl']);
  if (saved.apiUrl) {
    document.getElementById('apiUrl').value = saved.apiUrl;
  }

  // Get current tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  currentTab = tab;

  // Check if on GitHub
  if (isGitHubRepo(tab.url)) {
    repoInfo = parseGitHubUrl(tab.url);
    displayRepoInfo(repoInfo);
  } else {
    showNotGitHub();
  }

  // Setup event listeners
  setupEventListeners();
});

function setupEventListeners() {
  document.getElementById('analyzeBtn').addEventListener('click', analyzeRepository);
  document.getElementById('viewDashboardBtn').addEventListener('click', openDashboard);
  document.getElementById('viewDetailsBtn').addEventListener('click', viewDetails);
  document.getElementById('saveSettingsBtn').addEventListener('click', saveSettings);
}

function isGitHubRepo(url) {
  return url && url.includes('github.com') && url.split('/').length >= 5;
}

function parseGitHubUrl(url) {
  const parts = url.split('github.com/')[1]?.split('/');
  if (parts && parts.length >= 2) {
    return {
      owner: parts[0],
      repo: parts[1].split('?')[0].split('#')[0],
      url: `https://github.com/${parts[0]}/${parts[1].split('?')[0].split('#')[0]}`
    };
  }
  return null;
}

function displayRepoInfo(repo) {
  document.getElementById('repoUrl').textContent = repo.url;
  document.getElementById('statusTitle').textContent = 'GitHub Repository Detected';
  document.getElementById('statusDesc').textContent = `${repo.owner}/${repo.repo}`;
  document.getElementById('statusIcon').textContent = '✅';
  document.getElementById('analyzeBtn').disabled = false;
}

function showNotGitHub() {
  document.getElementById('repoUrl').textContent = 'Not a GitHub repository';
  document.getElementById('statusTitle').textContent = 'Navigate to GitHub';
  document.getElementById('statusDesc').textContent = 'Please open a GitHub repository page';
  document.getElementById('statusIcon').textContent = '❌';
  document.getElementById('analyzeBtn').disabled = true;
}

async function analyzeRepository() {
  if (!repoInfo) return;

  const apiUrl = document.getElementById('apiUrl').value || 'http://localhost:8000';
  
  // Show loading state
  document.getElementById('loading').classList.add('show');
  document.getElementById('analyzeBtn').disabled = true;
  document.getElementById('error').classList.remove('show');
  document.getElementById('results').classList.remove('show');

  try {
    // Step 1: Trigger scan
    const scanResponse = await fetch(`${apiUrl}/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_url: repoInfo.url })
    });

    if (!scanResponse.ok) {
      throw new Error(`Scan failed: ${scanResponse.statusText}`);
    }

    const scanData = await scanResponse.json();
    const projectId = scanData.project_id;

    // Step 2: Poll for job completion
    await pollJobStatus(apiUrl, scanData.job_id);

    // Step 3: Fetch results
    const resultsResponse = await fetch(`${apiUrl}/projects/${projectId}/overview`);
    const results = await resultsResponse.json();

    displayResults(results, projectId);

  } catch (error) {
    console.error('Analysis error:', error);
    showError(error.message);
  } finally {
    document.getElementById('loading').classList.remove('show');
    document.getElementById('analyzeBtn').disabled = false;
  }
}

async function pollJobStatus(apiUrl, jobId, maxAttempts = 60) {
  for (let i = 0; i < maxAttempts; i++) {
    const response = await fetch(`${apiUrl}/jobs/${jobId}/status`);
    const status = await response.json();

    if (status.status === 'completed') {
      return status;
    }

    if (status.status === 'failed') {
      throw new Error(status.error || 'Job failed');
    }

    // Wait 2 seconds before next poll
    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  throw new Error('Analysis timeout - taking too long');
}

function displayResults(data, projectId) {
  // Store project ID for later
  chrome.storage.local.set({ lastProjectId: projectId });

  // Calculate metrics
  const qualityScore = calculateQualityScore(data);
  const criticalIssues = data.risks?.filter(r => r.severity === 'critical').length || 0;
  const highIssues = data.risks?.filter(r => r.severity === 'high').length || 0;
  const totalFiles = data.metrics?.length || 0;

  // Display metrics
  document.getElementById('qualityScore').textContent = `${qualityScore}%`;
  document.getElementById('totalFiles').textContent = totalFiles;
  document.getElementById('criticalIssues').textContent = criticalIssues;
  document.getElementById('highIssues').textContent = highIssues;

  // Show results
  document.getElementById('results').classList.add('show');
}

function calculateQualityScore(data) {
  // Simple quality score calculation
  const totalFiles = data.metrics?.length || 1;
  const criticalIssues = data.risks?.filter(r => r.severity === 'critical').length || 0;
  const highIssues = data.risks?.filter(r => r.severity === 'high').length || 0;
  const mediumIssues = data.risks?.filter(r => r.severity === 'medium').length || 0;

  const issuesPenalty = (criticalIssues * 10 + highIssues * 5 + mediumIssues * 2);
  const maxPenalty = totalFiles * 15;
  const score = Math.max(0, 100 - (issuesPenalty / maxPenalty * 100));

  return Math.round(score);
}

function showError(message) {
  const errorEl = document.getElementById('error');
  errorEl.textContent = `❌ Error: ${message}`;
  errorEl.classList.add('show');
}

async function openDashboard() {
  const apiUrl = document.getElementById('apiUrl').value || 'http://localhost:8000';
  const dashboardUrl = apiUrl.replace(':8000', ':5173');
  chrome.tabs.create({ url: dashboardUrl });
}

async function viewDetails() {
  const { lastProjectId } = await chrome.storage.local.get(['lastProjectId']);
  if (lastProjectId) {
    const apiUrl = document.getElementById('apiUrl').value || 'http://localhost:8000';
    const dashboardUrl = apiUrl.replace(':8000', ':5173') + `?project=${lastProjectId}`;
    chrome.tabs.create({ url: dashboardUrl });
  }
}

async function saveSettings() {
  const apiUrl = document.getElementById('apiUrl').value;
  await chrome.storage.sync.set({ apiUrl });
  
  // Visual feedback
  const btn = document.getElementById('saveSettingsBtn');
  const originalText = btn.textContent;
  btn.textContent = '✓ Saved';
  setTimeout(() => {
    btn.textContent = originalText;
  }, 2000);
}
