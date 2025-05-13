# Agent UI for PrismDB

A modern chat interface for PrismDB agents built with Next.js, Tailwind CSS, and TypeScript. This template provides a ready-to-use UI for interacting with PrismDB's AI-powered database agents.

<img src="https://github.com/user-attachments/assets/7765fae5-a813-46cb-993b-904af9bc1672" alt="agent-ui" style="border-radius: 10px; width: 100%; max-width: 800px;" />

## Features

- 💬 **Modern Chat Interface**: Clean design with real-time streaming support
- 🧩 **Tool Calls Support**: Visualizes agent tool calls and their results
- 🧠 **Reasoning Steps**: Displays agent reasoning process (when available)
- 📚 **References Support**: Show sources used by the agent
- 🖼️ **Multi-modality Support**: Handles various content types including images, video, and audio
- 🎨 **Customizable UI**: Built with Tailwind CSS for easy styling
- 🧰 **Built with Modern Stack**: Next.js, TypeScript, shadcn/ui, Framer Motion, and more

## Getting Started

### Prerequisites

Before setting up Agent UI, you should have the PrismDB backend running. If you haven't set up the PrismDB backend yet, follow the instructions in the main [README.md](../../README.md) to run the backend locally.

### Installation

### Manual Installation

1. Clone the repository:

```bash
git clone https://github.com/your-org/prismdb
cd prismdb/prism-framework/agent-ui
```

2. Install dependencies:

```bash
pnpm install
```

3. Start the development server:

```bash
pnpm dev
```

4. Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Connecting to PrismDB Backend

By default Agent UI connects to `http://localhost:7777`. You can easily change this by hovering over the endpoint URL and clicking the edit option.

The UI is designed to work with the PrismDB agent framework and allows you to:
- Submit natural language queries to your databases
- View SQL query generation and execution
- Explore database schema information
- Access execution history and context
- Visualize query results

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for contribution guidelines.

## License

This project is licensed under the [MIT License](./LICENSE).
