## Installation

### Prerequisites

Let's get you set up with everything you need. This project uses a few modern tools that make development a breeze:

#### Node.js & pnpm

```bash
# Using nvm is the easiest way to manage Node versions (macOS/Linux)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
nvm install --lts

npm install -g pnpm@10
```

> **Windows users**: Grab Node.js from [nodejs.org](https://nodejs.org/) and then run `npm install -g pnpm@10.11.0`

#### Python & Poetry

```bash
# Install Python 3.11 on macOS with Homebrew
brew install python@3.11

# Then grab Poetry for dependency management
curl -sSL https://install.python-poetry.org | python3 -
```

> 💡 **Windows/Linux users**: Install Python 3.11+ from [python.org/downloads](https://www.python.org/downloads/) or your package manager

#### LangGraph CLI

```bash
# One simple command and you're good to go
pip install "langgraph-cli[inmem]"
```

#### Verify everything's ready

Let's make sure you've got everything set up correctly:

```bash
node --version    # Should be 22+
pnpm --version    # Should show 10+
python --version  # Should be 3.11+
poetry --version  # Should be 2.1+
langgraph --version
```

You're all set with the tools. Now let's get this project running.

### Setting Up the Project

Now for the fun part - let's get the fact-checker up and running:

```bash
# Clone and change into the project directory
git clone https://github.com/bharathxd/fact-checker.git
cd fact-checker

# One magic command to install everything
pnpm setup:dev

# Fire it up!
pnpm dev
```

That's it! Your fact-checker should now be running at [http://localhost:3000](http://localhost:3000) 🚀

### API Keys

You'll need to set up a couple API keys:

```
# Create a .env file in the root directory
cp .env.example .env
# Then edit the file to add your keys:
OPENAI_API_KEY=your_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

You can grab these from:
* OpenAI: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
* Tavily: [tavily.com](https://tavily.com/) (for web search - their generous free tier should be enough for testing)

### Troubleshooting

If you encounter any issues:

- **Poetry installation fails**: Try `pip install poetry` as an alternative
- **LangGraph CLI errors**: Ensure you have Python 3.11+ and try `pip install --upgrade "langgraph-cli[inmem]"`
- **pnpm command not found**: Make sure to restart your terminal after installation
- **Package conflicts**: Try `poetry env remove --all` and then `pnpm setup:dev` again

## 🖥️ Running the Application

To run the complete application (both the frontend and backend components):

```bash
# Install all dependencies (packages for both frontend and backend)
pnpm setup:dev

# Start the development server
pnpm dev
```

This will:
1. Set up all Node.js dependencies with pnpm
2. Install the Python packages needed for the fact-checker component
3. Start both the frontend web interface and backend services

You can then access the application in your browser at http://localhost:3000
