/**
 * DeepLynctus Browser Extension Background Script
 * 
 * Service worker that handles extension lifecycle, API communication,
 * and background processing for the GitHub code analysis integration.
 */

// Handle extension installation and setup
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('Deep Lynctus extension installed');
    
    // Set default API URL
    chrome.storage.sync.set({
      apiUrl: 'http://localhost:8000'
    });

    // Open welcome page
    chrome.tabs.create({
      url: 'http://localhost:5173'
    });
  } else if (details.reason === 'update') {
    console.log('Deep Lynctus extension updated');
  }
});

// Handle messages from content scripts or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'analyze') {
    handleAnalysis(request.repoUrl, sendResponse);
    return true; // Keep channel open for async response
  }
  
  if (request.action === 'getStatus') {
    handleStatusCheck(request.jobId, sendResponse);
    return true;
  }
});

// Handle context menu (right-click) actions
chrome.contextMenus.create({
  id: 'analyze-github-repo',
  title: 'Analyze with Deep Lynctus',
  contexts: ['page'],
  documentUrlPatterns: ['https://github.com/*/*']
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'analyze-github-repo') {
    // Trigger analysis from content script
    chrome.tabs.sendMessage(tab.id, { action: 'triggerAnalysis' });
  }
});

// Handle browser action click (toolbar icon)
chrome.action.onClicked.addListener((tab) => {
  // Open popup is configured in manifest, but this is a fallback
  if (tab.url.includes('github.com')) {
    chrome.action.openPopup();
  } else {
    // Not on GitHub, open dashboard
    chrome.storage.sync.get(['apiUrl'], (result) => {
      const dashboardUrl = (result.apiUrl || 'http://localhost:8000').replace(':8000', ':5173');
      chrome.tabs.create({ url: dashboardUrl });
    });
  }
});

// Analyze repository
async function handleAnalysis(repoUrl, sendResponse) {
  try {
    const { apiUrl } = await chrome.storage.sync.get(['apiUrl']);
    const baseUrl = apiUrl || 'http://localhost:8000';

    // Trigger scan
    const response = await fetch(`${baseUrl}/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_url: repoUrl })
    });

    if (!response.ok) {
      throw new Error(`Scan failed: ${response.statusText}`);
    }

    const data = await response.json();
    sendResponse({ success: true, data });

  } catch (error) {
    console.error('Analysis error:', error);
    sendResponse({ success: false, error: error.message });
  }
}

// Check job status
async function handleStatusCheck(jobId, sendResponse) {
  try {
    const { apiUrl } = await chrome.storage.sync.get(['apiUrl']);
    const baseUrl = apiUrl || 'http://localhost:8000';

    const response = await fetch(`${baseUrl}/jobs/${jobId}/status`);
    const status = await response.json();

    sendResponse({ success: true, status });

  } catch (error) {
    console.error('Status check error:', error);
    sendResponse({ success: false, error: error.message });
  }
}

// Handle tab updates to show/hide page action
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    if (tab.url.includes('github.com')) {
      // Enable extension icon on GitHub pages
      chrome.action.setIcon({
        tabId: tabId,
        path: {
          16: 'icons/icon16.png',
          48: 'icons/icon48.png',
          128: 'icons/icon128.png'
        }
      });
      
      chrome.action.setTitle({
        tabId: tabId,
        title: 'Analyze this repository with Deep Lynctus'
      });
    }
  }
});

// Keep service worker alive
let keepAliveInterval;

function keepAlive() {
  keepAliveInterval = setInterval(() => {
    chrome.runtime.getPlatformInfo(() => {
      // Just keeping the service worker alive
    });
  }, 20000); // Every 20 seconds
}

keepAlive();

// Cleanup on suspension
chrome.runtime.onSuspend.addListener(() => {
  clearInterval(keepAliveInterval);
});

console.log('Deep Lynctus background service worker loaded');
