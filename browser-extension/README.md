# Deep Lynctus Browser Extension

AI-powered code quality analyzer for GitHub repositories. Analyze any public repository directly from your browser!

## Features

- 🧠 **One-Click Analysis**: Analyze any GitHub repository with a single click
- 📊 **Instant Insights**: Get quality scores, complexity metrics, and issue detection
- 🎨 **Beautiful UI**: Glassmorphic design with smooth animations
- ⚡ **Fast Integration**: Seamlessly integrates into GitHub's interface
- 🔒 **Privacy-Focused**: Analysis happens on your configured backend

## Installation

### Option 1: Load Unpacked (Development)

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right)
3. Click "Load unpacked"
4. Select the `browser-extension` folder
5. The extension icon should appear in your toolbar!

### Option 2: Chrome Web Store (Coming Soon)

Will be available once published to Chrome Web Store.

## Setup

1. **Configure Backend URL**:
   - Click the extension icon in your toolbar
   - Scroll down to "Backend API URL"
   - Enter your backend URL (default: `http://localhost:8000`)
   - Click "Save Settings"

2. **Visit GitHub**:
   - Navigate to any public GitHub repository
   - You'll see an "Analyze with Deep Lynctus 🧠" button appear

3. **Analyze**:
   - Click the button to start analysis
   - Wait 1-2 minutes for processing
   - View results in the dashboard automatically

## Usage

### From GitHub Page (Injected Button)

1. Visit any GitHub repository (e.g., `https://github.com/facebook/react`)
2. Look for the gradient "Analyze with Deep Lynctus 🧠" button
3. Click to start analysis
4. Status updates will appear next to the button
5. Dashboard opens automatically when complete

### From Extension Popup

1. Navigate to a GitHub repository
2. Click the extension icon in toolbar
3. See repository info and status
4. Click "🚀 Analyze Repository"
5. View progress and metrics
6. Click "View Full Report" for details

## Features

### Popup Interface
- **Repository Detection**: Automatically detects current GitHub repo
- **Quality Metrics**: Shows quality score, file count, critical/high issues
- **Dashboard Link**: Quick access to full dashboard
- **Settings**: Configure backend API URL

### Content Script (GitHub Integration)
- **Auto-Injection**: Button appears on all GitHub repository pages
- **Real-Time Status**: Live updates during analysis
- **Error Handling**: Clear error messages if issues occur
- **Auto-Navigation**: Opens results when complete

### Background Worker
- **Context Menu**: Right-click on GitHub pages to analyze
- **Message Handling**: Coordinates between popup and content scripts
- **Settings Storage**: Persists your configuration

## Configuration

### Backend API URL

Default: `http://localhost:8000`

For production: `https://your-backend.com`

Change in popup settings or via:
```javascript
chrome.storage.sync.set({ apiUrl: 'https://your-api.com' });
```

## Permissions

- **activeTab**: Access current tab URL (GitHub repos only)
- **storage**: Save settings (API URL, preferences)
- **github.com**: Inject analysis button on GitHub pages
- **localhost:8000**: Connect to local backend (development)

## Development

### Project Structure

```
browser-extension/
├── manifest.json        # Extension configuration
├── popup.html          # Extension popup UI
├── popup.js            # Popup logic
├── content.js          # GitHub page injection
├── content.css         # Injected button styles
├── background.js       # Service worker
└── icons/              # Extension icons
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

### Build & Test

1. **Load Extension**:
   ```bash
   # Chrome: chrome://extensions/ → Load unpacked
   # Edge: edge://extensions/ → Load unpacked
   ```

2. **Test on GitHub**:
   - Visit `https://github.com/torvalds/linux`
   - Should see analyze button
   - Click to trigger analysis

3. **Debug**:
   - Popup: Right-click icon → "Inspect popup"
   - Content Script: F12 on GitHub page → Console
   - Background: chrome://extensions/ → "Service worker"

### Hot Reload

After making changes:
1. Go to `chrome://extensions/`
2. Click refresh icon on Deep Lynctus card
3. Reload any GitHub tabs

## Troubleshooting

### Button not appearing on GitHub

- **Solution**: Refresh the page, check console for errors
- **Verify**: Extension is enabled in `chrome://extensions/`
- **Check**: Page is a repository (not profile or search)

### Analysis fails

- **Solution**: Check backend is running at configured URL
- **Verify**: `curl http://localhost:8000/health` returns success
- **Check**: Repository is public and accessible

### Popup shows "Not a GitHub repository"

- **Solution**: Navigate to actual repo page (e.g., `/owner/repo`)
- **Note**: Won't work on github.com homepage or user profiles

### CORS errors

- **Solution**: Backend must allow extension origin
- **Fix**: Add CORS headers in backend (already configured)

## Keyboard Shortcuts

None by default. Add in `manifest.json`:

```json
"commands": {
  "analyze": {
    "suggested_key": {
      "default": "Ctrl+Shift+A"
    },
    "description": "Analyze current repository"
  }
}
```

## Privacy

- Extension only activates on GitHub pages
- No data collected or sent to third parties
- All analysis happens on your configured backend
- Settings stored locally in browser

## Compatibility

- ✅ Chrome 88+
- ✅ Edge 88+
- ✅ Brave
- ✅ Opera
- ❌ Firefox (Manifest V2 needed)

## Support

- **Issues**: GitHub Issues
- **Docs**: Main project README
- **Backend**: Requires Deep Lynctus backend running

## License

Same as main project

## Changelog

### v1.0.0 (2026-01-09)
- Initial release
- GitHub repository analysis
- Popup interface with metrics
- Content script injection
- Background service worker
- Settings configuration

## Roadmap

- [ ] Firefox support (Manifest V2)
- [ ] Keyboard shortcuts
- [ ] Multiple backend profiles
- [ ] Batch analysis
- [ ] Comparison from extension
- [ ] Private repo support (OAuth)
- [ ] Analysis history
- [ ] Export reports from popup

---

Made with 🧠 by Deep Lynctus Team
