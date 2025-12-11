# Deep Knowledge MCP Server

**Give your AI the power to browse, read, and understand technical documentation and code repositories.**

This [Apify Actor](https://apify.com/eager_cornet/deep-knowledge-mcp-server) implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction), allowing LLMs (like Claude) to perform deep research on technical topics by leveraging Apify's powerful scraping infrastructure.

---

## 🚀 Features

*   **🔍 Search Technical Docs**: Finds relevant documentation, libraries, and GitHub repositories using a specialized Google Search setup.
*   **📖 Fetch Documentation**: Extracts clean, markdown-formatted content from any documentation URL, perfect for LLM context windows.
*   **⚡ Fast & Scalable**: built on Apify's infrastructure, handling anti-scraping protections automatically.
*   **💰 Pay-per-Event**: Simple pricing model based on the tools you use.

---

## 🛠️ Tools Provided

### 1. `search_technical_docs`
Searches for technical resources.
*   **Input**: `query` (e.g., "LangChain python documentation"), `max_results` (default: 5).
*   **Output**: A list of titles, URLs, and descriptions.

### 2. `fetch_documentation`
Reads a web page and returns its content.
*   **Input**: `url` (e.g., "https://python.langchain.com/docs/get_started/introduction").
*   **Output**: The page content converted to Markdown.

---

## 💻 How to Use

### Option 1: limit with Claude Desktop (Recommended)

To use this Actor as a tool in Claude Desktop:

1.  **Deploy** this Actor to your Apify account.
2.  **Get your Apify Token** from [Settings > Integrations](https://console.apify.com/account/integrations).
3.  **Configure** your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "deep-knowledge": {
      "command": "npx",
      "args": [
        "-y",
        "@apify/mcp-server-runner",
        "ACTOR_NAME_OR_ID",
        "--token",
        "YOUR_APIFY_TOKEN"
      ]
    }
  }
}
```
*(Replace `ACTOR_NAME_OR_ID` with this Actor's name, e.g., `eager_cornet/deep-knowledge-mcp-server-v2`)*

### Option 2: Standalone Mode (Demo)

You can run this Actor directly on the Apify Platform to test it without an AI client.

1.  Go to the **Input** tab.
2.  Uncheck **Run as MCP Server**.
3.  Enter a **Demo Search Query**.
4.  Click **Start**.
5.  View results in the **Output** tab.

---

## 💸 Monetization & Pricing

This Actor uses **Pay-per-Event** pricing. You are charged only when the AI successfully calls a tool.

*   **Search**: charged per successful search operation.
*   **Fetch**: charged per successful page fetch.

*Check the Pricing tab for exact rates.*

---

## 👨‍💻 Development

This server is built with Python using the `mcp` SDK and `apify-client`.

**Local Development:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (requires APIFY_TOKEN env var)
python src/main.py
```
