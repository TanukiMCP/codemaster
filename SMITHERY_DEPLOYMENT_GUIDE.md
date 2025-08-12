# Smithery Deployment Guide for Codemaster MCP Server

## Overview

This guide explains how to deploy your Codemaster MCP server to Smithery so users can install it directly via `mcp.json` without downloading source code.

## What is Smithery?

Smithery is a platform for developers to find and ship AI-native services that communicate with AI agents using the Model Context Protocol (MCP). It provides:

- **Centralized Registry**: Discover and distribute MCP servers
- **Automated Deployment**: Docker-based deployment with auto-scaling
- **Configuration Management**: User-friendly UI for server configuration
- **Direct Installation**: Users install via URLs, no source code needed

## Smithery Requirements

### 1. Required Files

Your repository must contain these files in the root:

- ✅ **`smithery.yaml`** - Deployment configuration
- ✅ **`Dockerfile`** - Container build instructions  
- ✅ **`server.py`** - Your MCP server implementation
- ✅ **`requirements.txt`** - Python dependencies

### 2. Technical Requirements

Your MCP server must:

- ✅ **Expose `/mcp` endpoint** - Handle GET, POST, DELETE requests
- ✅ **Listen on `PORT` environment variable** - Smithery sets this dynamically
- ✅ **Use Streamable HTTP protocol** - FastMCP already implements this
- ✅ **Handle configuration via query parameters** - Using dot-notation

### 3. Container Requirements

Your Docker container must:

- ✅ **Use `PORT` environment variable** - Dynamic port assignment
- ✅ **Run as non-root user** - Security best practice
- ✅ **Include health check** - For container orchestration
- ✅ **Handle signals properly** - Graceful shutdown

## Current Status ✅

Your Codemaster MCP server is **already properly configured** for Smithery deployment:

### ✅ Smithery.yaml Configuration
```yaml
runtime: "container"
build:
  dockerfile: "Dockerfile"
  dockerBuildPath: "."
startCommand:
  type: "http"
  configSchema:
    type: "object"
    properties:
      apiKey:
        type: "string"
        title: "API Key"
        description: "Optional API key for enhanced authentication and rate limiting"
      debug:
        type: "boolean" 
        title: "Debug Mode"
        description: "Enable debug logging for troubleshooting"
        default: false
      sessionTimeout:
        type: "integer"
        title: "Session Timeout"
        description: "Session timeout in minutes"
        default: 30
        minimum: 5
        maximum: 120
    required: []
  exampleConfig:
    apiKey: "optional-api-key-123"
    debug: false
    sessionTimeout: 30
```

### ✅ Server Implementation
- FastMCP with streamable-http transport
- Proper `/mcp` endpoint
- Configuration handling via environment variables
- Health check endpoint at `/health`

### ✅ Docker Configuration
- Multi-stage optimized build
- Non-root user for security
- Proper port handling with `$PORT`
- Health checks configured

## Deployment Steps

### 1. Repository Setup
```bash
# Ensure all files are committed
git add .
git commit -m "Add Smithery deployment configuration"
git push origin main
```

### 2. Connect to Smithery
1. Visit [Smithery.ai](https://smithery.ai)
2. Sign up/log in with GitHub
3. Connect your repository
4. Smithery will automatically detect your MCP server

### 3. Configure Deployment
- Smithery reads your `smithery.yaml` automatically
- No additional configuration needed
- Build process starts automatically

### 4. Verify Deployment
Once deployed, your server will be available at:
```
https://server.smithery.ai/your-username/codemaster/mcp
```

## User Installation Process

### For End Users

1. **Browse Registry**: Visit `https://smithery.ai/server/your-username/codemaster`
2. **Configure**: Set optional parameters (API key, debug mode, etc.)
3. **Install**: Copy the provided configuration
4. **Add to MCP Client**: Add to `mcp.json` or Claude Desktop config

### Example User Configuration

#### Cursor IDE (mcp.json)
```json
{
  "servers": {
    "codemaster": {
      "type": "http",
      "url": "https://server.smithery.ai/your-username/codemaster/mcp",
      "apiKey": "user-api-key",
      "debug": false,
      "sessionTimeout": 30
    }
  }
}
```

#### Claude Desktop
```json
{
  "mcpServers": {
    "codemaster": {
      "type": "http", 
      "url": "https://server.smithery.ai/your-username/codemaster/mcp?apiKey=user-key&debug=false&sessionTimeout=30"
    }
  }
}
```

## Configuration Schema Benefits

Your `configSchema` provides:

- **Type Safety**: JSON Schema validation
- **User-Friendly UI**: Smithery generates forms automatically  
- **Default Values**: Sensible defaults for all parameters
- **Validation**: Min/max ranges and required fields
- **Documentation**: Descriptions help users understand each option

## How Smithery Works

### 1. Build Process
- Smithery reads your `smithery.yaml`
- Builds Docker container using your `Dockerfile`
- Tests the container build process
- Deploys to Smithery infrastructure

### 2. Runtime
- Container runs with dynamic port assignment
- Configuration passed via query parameters
- Health checks monitor container status
- Auto-scaling based on usage

### 3. User Experience
- No source code download required
- Configuration via web UI
- Direct URL installation
- Automatic updates when you push changes

## Monitoring & Updates

### Automatic Updates
- Push changes to your main branch
- Smithery automatically rebuilds and redeploys
- Users get updates transparently

### Monitoring
- Smithery provides usage analytics
- Health check monitoring
- Error tracking and logging

## Security Features

- **Security Scanning**: Smithery scans for vulnerabilities
- **Isolation**: Each deployment runs in isolated containers
- **SSL**: Automatic HTTPS for all endpoints
- **Rate Limiting**: Built-in protection against abuse

## Next Steps

1. **Push to GitHub**: Ensure latest changes are committed
2. **Connect Smithery**: Link your GitHub repository
3. **Test Deployment**: Verify the build process
4. **Share with Users**: Provide installation instructions
5. **Monitor Usage**: Track adoption and performance

Your Codemaster MCP server is ready for Smithery deployment! 🚀
