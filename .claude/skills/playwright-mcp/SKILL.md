---
name: playwright-mcp
description: Browser automation using Playwright MCP server. Use this skill when the user needs to interact with web pages, scrape data, fill forms, take screenshots, test web UIs, or automate any browser-based workflow. Relevant for JPL's website scraping and scoring pipeline.
---

Use the Playwright MCP server for all browser automation tasks. This includes navigating pages, clicking elements, filling forms, scraping content, taking screenshots, and running automated workflows.

## When to Use This Skill

- Scraping websites (Google Maps listings, business sites for JPL pipeline)
- Scoring website design quality by inspecting pages
- Testing web apps and UIs you've built
- Filling out forms or automating repetitive browser tasks
- Taking screenshots or generating PDFs of pages
- Any task that requires interacting with a live web page

## Installation

### Claude Code (recommended)
```bash
claude mcp add playwright npx @playwright/mcp@latest
```

### VS Code
```bash
code --add-mcp '{"name":"playwright","command":"npx","args":["@playwright/mcp@latest"]}'
```

### Windsurf / Antigravity / Other MCP Clients
Add to your MCP config:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

## Available Tools

### Navigation & Pages
- **browser_navigate** -- Go to a URL
- **browser_go_back** / **browser_go_forward** -- Browser history navigation
- **browser_wait** -- Wait for page changes or network activity
- **browser_close** -- Close the page
- **browser_tab_list** -- List open tabs
- **browser_tab_new** / **browser_tab_select** / **browser_tab_close** -- Manage tabs

### Interaction
- **browser_click** -- Click elements (single, double, right-click, with modifiers)
- **browser_type** -- Type text into focused element
- **browser_fill_form** -- Fill multiple form fields at once
- **browser_select_option** -- Select dropdown options
- **browser_hover** -- Hover over elements
- **browser_drag** -- Drag and drop between elements
- **browser_press_key** -- Press keyboard keys
- **browser_file_upload** -- Upload files

### Data Extraction
- **browser_snapshot** -- Get accessibility snapshot of the page (primary way to read page content)
- **browser_evaluate** -- Run JavaScript on the page to extract data
- **browser_console_messages** -- Get console output
- **browser_network_requests** -- Get network request/response data

### Output
- **browser_take_screenshot** -- Screenshot the page or a specific element (requires `vision` capability)
- **browser_pdf_save** -- Save page as PDF (requires `pdf` capability)

## How It Works

Playwright MCP uses **accessibility snapshots**, not screenshots. Each snapshot returns a structured tree of page elements with `ref` attributes. Use these refs to interact with elements.

### Typical workflow:
1. **Navigate** to a URL with `browser_navigate`
2. **Snapshot** the page with `browser_snapshot` to see what's on it
3. **Interact** using element refs from the snapshot (click, type, fill)
4. **Extract** data with `browser_evaluate` for custom JS or read from snapshots
5. **Repeat** as needed

### Example: Scrape a business website
```
1. browser_navigate → "https://example-business.com"
2. browser_snapshot → read the page structure
3. browser_evaluate → extract contact info, design elements, meta tags
4. Use the data to score the website quality
```

## Configuration Options

Run headed (default) or headless:
```json
["@playwright/mcp@latest", "--headless"]
```

Enable extra capabilities:
```json
["@playwright/mcp@latest", "--caps", "vision,pdf"]
```

Use a specific browser:
```json
["@playwright/mcp@latest", "--browser", "firefox"]
```

Set viewport size:
```json
["@playwright/mcp@latest", "--viewport-size", "1280x720"]
```

## Guidelines

- **Use snapshots, not screenshots** for reading page content. Snapshots are faster and more token-efficient.
- **Use element refs** from snapshots to interact with elements. Don't guess selectors.
- **Wait after navigation** if the page loads dynamically. Use `browser_wait` when needed.
- **Run headless for automation** pipelines (scraping, scoring). Use headed for debugging.
- **Don't store sensitive data** in browser sessions. Use `--isolated` for throwaway sessions.
