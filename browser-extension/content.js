/**
 * DeepLynctus GitHub Integration Content Script
 * 
 * Dynamically injects analysis button into GitHub repository pages.
 * Provides seamless integration with the DeepLynctus analysis platform.
 */

(function() {
  'use strict';

  // Only run on GitHub repository pages
  if (!isGitHubRepoPage()) return;

  // Create and inject the analyze button
  injectAnalyzeButton();

  // Listen for messages from popup
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getRepoInfo') {
      sendResponse(getRepoInfo());
    }
  });

  function isGitHubRepoPage() {
    const url = window.location.href;
    const pathParts = window.location.pathname.split('/').filter(p => p);
    
    // Must be on github.com and have at least owner/repo
    return url.includes('github.com') && pathParts.length >= 2;
  }

  function getRepoInfo() {
    const pathParts = window.location.pathname.split('/').filter(p => p);
    if (pathParts.length >= 2) {
      return {
        owner: pathParts[0],
        repo: pathParts[1],
        url: `https://github.com/${pathParts[0]}/${pathParts[1]}`
      };
    }
    return null;
  }

  function injectAnalyzeButton() {
    // Wait for GitHub UI to load
    const checkInterval = setInterval(() => {
      const targetElement = findInsertionPoint();
      if (targetElement && !document.getElementById('deep-lynctus-btn')) {
        clearInterval(checkInterval);
        createButton(targetElement);
      }
    }, 500);

    // Stop checking after 10 seconds
    setTimeout(() => clearInterval(checkInterval), 10000);
  }

  function findInsertionPoint() {
    // Try to find the repository header actions area
    // GitHub's UI changes, so we try multiple selectors
    const selectors = [
      '.file-navigation',
      '[data-target="react-app.embeddedData"]',
      '.repository-content',
      '#repository-container-header'
    ];

    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) return element;
    }

    return null;
  }

  function createButton(insertionPoint) {
    // Create button container
    const container = document.createElement('div');
    container.id = 'deep-lynctus-btn';
    container.className = 'deep-lynctus-container';

    // Create button
    const button = document.createElement('button');
    button.className = 'deep-lynctus-analyze-btn';
    button.innerHTML = `
      <span class="deep-lynctus-icon">🧠</span>
      <span class="deep-lynctus-text">Analyze with Deep Lynctus</span>
      <span class="deep-lynctus-badge">AI</span>
    `;

    // Create status indicator
    const status = document.createElement('div');
    status.className = 'deep-lynctus-status';
    status.style.display = 'none';

    container.appendChild(button);
    container.appendChild(status);

    // Insert into DOM
    if (insertionPoint.firstChild) {
      insertionPoint.insertBefore(container, insertionPoint.firstChild);
    } else {
      insertionPoint.appendChild(container);
    }

    // Add click handler
    button.addEventListener('click', handleAnalyzeClick);
  }

  async function handleAnalyzeClick(e) {
    e.preventDefault();
    
    const button = e.currentTarget;
    const container = button.parentElement;
    const status = container.querySelector('.deep-lynctus-status');

    // Get API URL from storage
    const { apiUrl } = await chrome.storage.sync.get(['apiUrl']);
    const baseUrl = apiUrl || 'http://localhost:8000';

    try {
      // Show loading state
      button.disabled = true;
      button.classList.add('loading');
      status.textContent = '🔄 Analyzing repository...';
      status.style.display = 'block';
      status.className = 'deep-lynctus-status loading';

      const repoInfo = getRepoInfo();
      if (!repoInfo) {
        throw new Error('Could not detect repository information');
      }

      // Trigger scan
      const scanResponse = await fetch(`${baseUrl}/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoInfo.url })
      });

      if (!scanResponse.ok) {
        throw new Error(`Scan failed: ${scanResponse.statusText}`);
      }

      const scanData = await scanResponse.json();

      // Poll for completion
      status.textContent = '⏳ Processing code (this may take 1-2 minutes)...';
      await pollJobStatus(baseUrl, scanData.job_id);

      // Success
      status.textContent = '✅ Analysis complete!';
      status.className = 'deep-lynctus-status success';

      // Open results in new tab after 2 seconds
      setTimeout(() => {
        const dashboardUrl = baseUrl.replace(':8000', ':5173') + `?project=${scanData.project_id}`;
        window.open(dashboardUrl, '_blank');
      }, 2000);

    } catch (error) {
      console.error('Analysis error:', error);
      status.textContent = `❌ Error: ${error.message}`;
      status.className = 'deep-lynctus-status error';
    } finally {
      button.disabled = false;
      button.classList.remove('loading');

      // Hide status after 5 seconds
      setTimeout(() => {
        status.style.display = 'none';
      }, 5000);
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

    throw new Error('Analysis timeout');
  }

})();
