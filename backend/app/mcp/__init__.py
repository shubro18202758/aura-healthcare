"""
Model Context Protocol (MCP) Implementation for AURA Healthcare
Provides intelligent context injection for AI responses
"""

from .mcp_server import MCPServer
from .context_engine import ContextEngine

__all__ = ["MCPServer", "ContextEngine"]
