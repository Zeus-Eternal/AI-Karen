#!/usr/bin/env python3
"""
Enhanced Kari Developer CLI with AG-UI integration and CopilotKit assistance.
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.tree import Tree

try:
    from ai_karen_engine.plugin_manager import get_plugin_manager
    from ai_karen_engine.extensions.manager import ExtensionManager
    from ai_karen_engine.hooks.hook_manager import get_hook_manager
    KARI_AVAILABLE = True
except ImportError:
    KARI_AVAILABLE = False

console = Console()


class KariDevCLI:
    """Enhanced CLI for Kari development with AG-UI integration."""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        
        if KARI_AVAILABLE:
            self.plugin_manager = get_plugin_manager()
            self.hook_manager = get_hook_manager()
        else:
            self.plugin_manager = None
            self.hook_manager = None
    
    def authenticate(self, token: Optional[str] = None) -> bool:
        """Authenticate with the Kari API."""
        if not token:
            token = Prompt.ask("Enter your API token", password=True)
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        try:
            response = self.session.get(f"{self.api_base_url}/api/auth/verify")
            if response.status_code == 200:
                console.print("✅ Authentication successful", style="green")
                return True
            else:
                console.print("❌ Authentication failed", style="red")
                return False
        except Exception as e:
            console.print(f"❌ Connection failed: {e}", style="red")
            return False
    
    def list_components(self, component_type: Optional[str] = None) -> None:
        """List all system components with their status."""
        try:
            response = self.session.get(f"{self.api_base_url}/api/developer/components")
            if response.status_code != 200:
                console.print(f"❌ Failed to fetch components: {response.status_code}", style="red")
                return
            
            data = response.json()
            components = data.get("components", [])
            
            if component_type:
                components = [c for c in components if c["type"] == component_type]
            
            if not components:
                console.print("No components found", style="yellow")
                return
            
            # Create a rich table
            table = Table(title=f"Kari Components ({len(components)} total)")
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Type", style="magenta")
            table.add_column("Status", style="green")
            table.add_column("Health", style="yellow")
            table.add_column("Success Rate", justify="right")
            table.add_column("Chat", justify="center")
            table.add_column("AI", justify="center")
            
            for component in components:
                status_style = "green" if component["status"] == "active" else "red"
                health_style = "green" if component["health"] == "healthy" else "yellow" if component["health"] == "warning" else "red"
                
                success_rate = component["metrics"]["success_rate"]
                success_style = "green" if success_rate > 0.9 else "yellow" if success_rate > 0.7 else "red"
                
                table.add_row(
                    component["name"],
                    component["type"].title(),
                    f"[{status_style}]{component['status']}[/{status_style}]",
                    f"[{health_style}]{component['health']}[/{health_style}]",
                    f"[{success_style}]{success_rate:.1%}[/{success_style}]",
                    "✅" if component["chat_integration"] else "❌",
                    "🧠" if component["copilot_enabled"] else "❌",
                )
            
            console.print(table)
            
            # Show summary
            summary = data.get("summary", {})
            console.print(f"\n📊 Summary: {summary.get('active_count', 0)} active, "
                         f"{summary.get('healthy_count', 0)} healthy, "
                         f"{summary.get('chat_integrated_count', 0)} chat-ready, "
                         f"{summary.get('ai_enabled_count', 0)} AI-enabled")
            
        except Exception as e:
            console.print(f"❌ Error listing components: {e}", style="red")
    
    def show_component_details(self, component_name: str) -> None:
        """Show detailed information about a component."""
        try:
            response = self.session.get(f"{self.api_base_url}/api/developer/components")
            if response.status_code != 200:
                console.print(f"❌ Failed to fetch components: {response.status_code}", style="red")
                return
            
            data = response.json()
            components = data.get("components", [])
            
            component = next((c for c in components if c["name"] == component_name), None)
            if not component:
                console.print(f"❌ Component '{component_name}' not found", style="red")
                return
            
            # Create detailed panel
            details = f"""
[bold cyan]Name:[/bold cyan] {component['name']}
[bold cyan]Type:[/bold cyan] {component['type'].title()}
[bold cyan]Status:[/bold cyan] {component['status']}
[bold cyan]Health:[/bold cyan] {component['health']}

[bold yellow]Metrics:[/bold yellow]
  • Executions: {component['metrics']['executions']:,}
  • Success Rate: {component['metrics']['success_rate']:.1%}
  • Avg Response Time: {component['metrics']['avg_response_time']:.0f}ms
  • Memory Usage: {component['metrics']['memory_usage']:.1f}MB
  • CPU Usage: {component['metrics']['cpu_usage']:.1f}%

[bold green]Integration:[/bold green]
  • Chat Integration: {'✅ Enabled' if component['chat_integration'] else '❌ Disabled'}
  • AI Assistance: {'🧠 Enabled' if component['copilot_enabled'] else '❌ Disabled'}

[bold blue]Capabilities:[/bold blue]
{chr(10).join(f'  • {cap}' for cap in component.get('capabilities', []))}

[bold purple]Last Activity:[/bold purple] {component['last_activity']}
            """
            
            panel = Panel(details, title=f"Component Details: {component_name}", border_style="blue")
            console.print(panel)
            
        except Exception as e:
            console.print(f"❌ Error showing component details: {e}", style="red")
    
    def execute_component_action(self, component_id: str, action: str) -> None:
        """Execute an action on a component."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Executing {action} on {component_id}...", total=None)
                
                response = self.session.post(
                    f"{self.api_base_url}/api/developer/components/{component_id}/{action}"
                )
                
                progress.update(task, completed=True)
            
            if response.status_code == 200:
                result = response.json()
                console.print(f"✅ {result.get('message', 'Action completed successfully')}", style="green")
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                console.print(f"❌ Action failed: {error_data.get('detail', response.text)}", style="red")
                
        except Exception as e:
            console.print(f"❌ Error executing action: {e}", style="red")
    
    def show_chat_metrics(self, hours: int = 24) -> None:
        """Show chat system performance metrics."""
        try:
            response = self.session.get(f"{self.api_base_url}/api/developer/chat-metrics?hours={hours}")
            if response.status_code != 200:
                console.print(f"❌ Failed to fetch chat metrics: {response.status_code}", style="red")
                return
            
            data = response.json()
            summary = data.get("summary", {})
            
            # Create metrics table
            table = Table(title=f"Chat Metrics (Last {hours} hours)")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green", justify="right")
            
            table.add_row("Total Messages", f"{summary.get('total_messages', 0):,}")
            table.add_row("Avg Response Time", f"{summary.get('avg_response_time', 0):.0f}ms")
            table.add_row("User Satisfaction", f"{summary.get('avg_satisfaction', 0):.1%}")
            table.add_row("AI Suggestions", f"{summary.get('total_ai_suggestions', 0):,}")
            table.add_row("Tool Calls", f"{summary.get('total_tool_calls', 0):,}")
            
            console.print(table)
            
            # Show recent metrics trend
            metrics = data.get("metrics", [])
            if metrics:
                console.print("\n📈 Recent Trend (last 5 data points):")
                recent_metrics = metrics[-5:]
                
                trend_table = Table()
                trend_table.add_column("Time", style="cyan")
                trend_table.add_column("Messages", justify="right")
                trend_table.add_column("Response Time", justify="right")
                trend_table.add_column("AI Suggestions", justify="right")
                
                for metric in recent_metrics:
                    timestamp = metric["timestamp"].split("T")[1][:5]  # HH:MM
                    trend_table.add_row(
                        timestamp,
                        str(metric["total_messages"]),
                        f"{metric['response_time_ms']}ms",
                        str(metric["ai_suggestions"])
                    )
                
                console.print(trend_table)
            
        except Exception as e:
            console.print(f"❌ Error showing chat metrics: {e}", style="red")
    
    def generate_component_code(self, component_type: str, component_name: str, features: List[str]) -> None:
        """Generate boilerplate code for a new component."""
        templates = {
            "plugin": self._generate_plugin_template,
            "extension": self._generate_extension_template,
            "hook": self._generate_hook_template,
        }
        
        if component_type not in templates:
            console.print(f"❌ Unknown component type: {component_type}", style="red")
            return
        
        try:
            code, files = templates[component_type](component_name, features)
            
            console.print(f"\n🎯 Generated {component_type} boilerplate for '{component_name}'")
            
            # Show generated files
            tree = Tree(f"📁 {component_name}/")
            for file_name, file_content in files.items():
                tree.add(f"📄 {file_name}")
            
            console.print(tree)
            
            # Show main code file
            if files:
                main_file = list(files.keys())[0]
                syntax = Syntax(files[main_file], "python", theme="monokai", line_numbers=True)
                console.print(f"\n📝 {main_file}:")
                console.print(syntax)
            
            # Ask if user wants to save files
            if Confirm.ask("Save generated files to disk?"):
                self._save_generated_files(component_name, files)
            
        except Exception as e:
            console.print(f"❌ Error generating component code: {e}", style="red")
    
    def _generate_plugin_template(self, name: str, features: List[str]) -> tuple[str, Dict[str, str]]:
        """Generate plugin template."""
        class_name = "".join(word.capitalize() for word in name.split("_"))
        
        main_code = f'''"""
{name} plugin for Kari with AG-UI and CopilotKit integration.
"""

from datetime import datetime
import logging
from typing import Any, Dict, List

from ai_karen_engine.plugins.base import BasePlugin
from ai_karen_engine.hooks.hook_mixin import HookMixin
from ai_karen_engine.hooks.hook_types import HookTypes


class {class_name}Plugin(BasePlugin, HookMixin):
    """
    {name.replace("_", " ").title()} plugin with enhanced capabilities.

    Features: {", ".join(features) if features else "Basic functionality"}
    """

    def __init__(self):
        super().__init__()
        self.name = "{name}"
        self.version = "1.0.0"
        self.description = "{name.replace('_', ' ').title()} plugin"
        self._features: List[str] = {repr(features or [])}
        self._logger = logging.getLogger(f"plugin.{name}")
        self._hooks_registered = False

    async def _ensure_hooks(self) -> None:
        """Register lifecycle hooks when the plugin is first used."""
        if self._hooks_registered:
            return

        await self.register_hook(
            HookTypes.PLUGIN_EXECUTION_START,
            self._on_execution_start,
            source_name=self.name,
        )

        await self.register_hook(
            HookTypes.PLUGIN_EXECUTION_END,
            self._on_execution_end,
            source_name=self.name,
        )

        self._hooks_registered = True

    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Execute the plugin."""
        await self._ensure_hooks()

        payload = {{"plugin_name": self.name, "params": params}}
        await self.trigger_hooks(HookTypes.PLUGIN_EXECUTION_START, payload, context)

        try:
            result = await self._process_request(params, context)

            await self.trigger_hooks(
                HookTypes.PLUGIN_EXECUTION_END,
                {{"plugin_name": self.name, "result": result}},
                context,
            )

            return result

        except Exception as exc:
            await self.trigger_hooks(
                HookTypes.PLUGIN_ERROR,
                {{"plugin_name": self.name, "error": str(exc)}},
                context,
            )
            self._logger.exception(
                "Plugin execution failed",
                extra={{"plugin": self.name, "params": params}},
            )
            raise

    async def _process_request(self, params: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Process the main plugin request."""
        action = (params.get("action") or "capabilities").lower()
        timestamp = datetime.utcnow().isoformat() + "Z"

        if action == "ping":
            response = {{"status": "ok", "timestamp": timestamp, "plugin": self.name}}
            self._logger.info("Ping processed", extra=response)
            return response

        if action == "capabilities":
            response = {{
                "status": "ok",
                "timestamp": timestamp,
                "plugin": self.name,
                "features": self._features or ["introspection"],
            }}
            self._logger.info("Capability report generated", extra=response)
            return response

        if action == "run":
            feature_name = params.get("feature")
            if not feature_name:
                raise ValueError("Missing 'feature' parameter for run action")

            if self._features and feature_name not in self._features:
                raise ValueError(f"Unsupported feature: {{feature_name}}")

            payload = params.get("payload")
            result = {{
                "status": "executed",
                "timestamp": timestamp,
                "plugin": self.name,
                "feature": feature_name,
                "payload": payload,
                "context_summary": self._summarize_context(context),
            }}
            self._logger.info("Feature executed", extra=result)
            return result

        raise ValueError(f"Unsupported action: {{action}}")

    def _summarize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a safe summary of the execution context for logging."""
        summary: Dict[str, Any] = {}
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                summary[key] = value
            elif isinstance(value, dict):
                summary[key] = sorted(value.keys())
            elif isinstance(value, list):
                summary[key] = len(value)
            else:
                summary[key] = value.__class__.__name__
        return summary

    async def _on_execution_start(self, data: Dict[str, Any], user_context: Dict[str, Any]) -> None:
        """Handle execution start hook."""
        self._logger.info(
            "Plugin execution started",
            extra={{"plugin": self.name, "params": data.get("params", {{}})}},
        )

    async def _on_execution_end(self, data: Dict[str, Any], user_context: Dict[str, Any]) -> None:
        """Handle execution end hook."""
        self._logger.info(
            "Plugin execution completed",
            extra={{"plugin": self.name, "result": data.get("result")}},
        )


plugin_instance = {class_name}Plugin()


def get_plugin() -> {class_name}Plugin:
    """Get plugin instance."""
    return plugin_instance
'''
        
        config_code = f'''{{
    "name": "{name}",
    "version": "1.0.0",
    "description": "{name.replace('_', ' ').title()} plugin",
    "author": "Kari Developer",
    "features": {json.dumps(features)},
    "chat_integration": true,
    "copilot_enabled": true,
    "hooks": [
        "plugin_execution_start",
        "plugin_execution_end",
        "plugin_error"
    ],
    "dependencies": [],
    "permissions": ["chat", "memory"]
}}'''
        
        test_code = f'''"""
Tests for {name} plugin.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from {name} import {class_name}Plugin


@pytest.fixture
def plugin():
    """Create plugin instance for testing."""
    return {class_name}Plugin()


@pytest.mark.asyncio
async def test_plugin_execution(plugin):
    """Test basic plugin execution."""
    params = {{"action": "ping"}}
    context = {{"user_id": "test_user"}}

    result = await plugin.execute(params, context)

    assert result is not None
    assert result["status"] == "ok"
    assert result["plugin"] == plugin.name
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_hook_registration(plugin):
    """Test that hooks are properly registered."""
    await plugin.execute({{"action": "capabilities"}}, {{}})

    assert plugin._hooks_registered is True
'''
        
        files = {
            f"{name}.py": main_code,
            f"{name}_config.json": config_code,
            f"test_{name}.py": test_code,
        }
        
        return main_code, files
    
    def _generate_extension_template(self, name: str, features: List[str]) -> tuple[str, Dict[str, str]]:
        """Generate extension template."""
        class_name = "".join(word.capitalize() for word in name.split("_")) + "Extension"
        
        main_code = f'''"""
{name} extension for Kari with AG-UI and CopilotKit integration.
"""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

try:
    from fastapi import APIRouter
except ImportError:  # pragma: no cover - FastAPI optional in some environments
    APIRouter = None  # type: ignore[assignment]

from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.extensions.models import ExtensionManifest, ExtensionContext
from ai_karen_engine.hooks.hook_types import HookTypes


class {class_name}(BaseExtension):
    """
    {name.replace("_", " ").title()} extension with enhanced capabilities.

    Features: {", ".join(features) if features else "Basic functionality"}
    """

    def __init__(self, manifest: ExtensionManifest, context: ExtensionContext):
        super().__init__(manifest, context)
        self.name = "{name}"
        self._features: List[str] = {repr(features or [])}
        self._last_health_check: Optional[datetime] = None
        self._runtime_logger = logging.getLogger(f"extension.{name}.runtime")

    async def _initialize(self) -> None:
        """Extension-specific initialization logic."""
        await self.register_hook(
            HookTypes.EXTENSION_ACTIVATED,
            self._handle_activation,
            source_name=self.name,
        )

        await self.register_hook(
            HookTypes.EXTENSION_ERROR,
            self._handle_error,
            source_name=self.name,
        )

        self._runtime_logger.info(
            "Extension ready",
            extra={{"extension": self.name, "features": self._features}},
        )

    async def _shutdown(self) -> None:
        """Extension-specific cleanup."""
        self._runtime_logger.info(
            "Extension shutdown requested", extra={{"extension": self.name}}
        )
        self._last_health_check = None

    def create_api_router(self) -> Optional[APIRouter]:
        """Expose operational endpoints for monitoring."""
        router = super().create_api_router()
        if router is None:
            return None

        router.add_api_route(
            "/status",
            self._status_endpoint,
            methods=["GET"],
            name=f"{name}_status",
        )

        router.add_api_route(
            "/features",
            self._features_endpoint,
            methods=["GET"],
            name=f"{name}_features",
        )

        return router

    async def _status_endpoint(self) -> Dict[str, Any]:
        """Return current health information for API consumers."""
        self._last_health_check = datetime.utcnow()
        return self.get_status()

    async def _features_endpoint(self) -> Dict[str, Any]:
        """Expose supported feature metadata via API."""
        return {{
            "name": self.name,
            "features": self._features,
            "manifest_version": self.manifest.version,
        }}

    async def _handle_activation(
        self, data: Dict[str, Any], user_context: Dict[str, Any]
    ) -> None:
        """Hook callback when the extension is activated."""
        self._runtime_logger.info(
            "Extension activated",
            extra={{
                "extension": self.name,
                "payload": data,
                "user": user_context.get("user_id") if user_context else None,
            }},
        )

    async def _handle_error(
        self, data: Dict[str, Any], user_context: Dict[str, Any]
    ) -> None:
        """Hook callback for extension errors."""
        self._runtime_logger.error(
            "Extension reported error",
            extra={{
                "extension": self.name,
                "payload": data,
                "user": user_context.get("user_id") if user_context else None,
            }},
        )

    def get_status(self) -> Dict[str, Any]:
        """Get extension status."""
        status = {{
            "name": self.name,
            "status": "active",
            "features": self._features,
            "initialized": True,
        }}

        if self._last_health_check is not None:
            status["last_health_check"] = (
                self._last_health_check.isoformat(timespec="seconds") + "Z"
            )

        return status
'''
        
        manifest_code = f'''{{
    "name": "{name}",
    "version": "1.0.0",
    "description": "{name.replace('_', ' ').title()} extension",
    "author": "Kari Developer",
    "category": "utility",
    "features": {json.dumps(features)},
    "dependencies": [],
    "permissions": ["api", "hooks"],
    "api_routes": [],
    "hooks": [],
    "mcp_integration": false,
    "chat_integration": true,
    "copilot_enabled": true
}}'''
        
        files = {
            "__init__.py": main_code,
            "extension.json": manifest_code,
        }
        
        return main_code, files
    
    def _generate_hook_template(self, name: str, features: List[str]) -> tuple[str, Dict[str, str]]:
        """Generate hook template."""
        hook_code = f'''"""
{name} hook for Kari system.
"""

import logging
from typing import Any, Dict
from ai_karen_engine.hooks.hook_manager import get_hook_manager
from ai_karen_engine.hooks.hook_types import HookTypes


async def {name}_handler(data: Dict[str, Any], user_context: Dict[str, Any]) -> Any:
    """
    Handle {name.replace('_', ' ')} hook.

    Args:
        data: Hook data
        user_context: User context

    Returns:
        Hook result
    """
    logger = logging.getLogger(f"hooks.{name}")
    hook_type_name = "{name.upper()}"
    resolved_hook_type = getattr(HookTypes, hook_type_name, "{name}")

    logger.info(
        "Hook execution started",
        extra={{
            "hook_type": resolved_hook_type,
            "payload": data,
            "user": user_context.get("user_id") if user_context else None,
        }},
    )

    result = {{
        "hook": resolved_hook_type,
        "processed": True,
        "data": data,
        "context": {{
            "user_id": user_context.get("user_id") if user_context else None,
            "source": user_context.get("source") if user_context else None,
        }},
    }}

    logger.info("Hook execution completed", extra=result)
    return result


async def register_{name}_hook():
    """Register the {name} hook."""
    hook_manager = get_hook_manager()
    
    hook_type_name = "{name.upper()}"
    resolved_hook_type = getattr(HookTypes, hook_type_name, "{name}")
    hook_identifier = await hook_manager.register_hook(
        hook_type=resolved_hook_type,
        handler={name}_handler,
        source_type="custom",
        source_name="{name}",
    )

    logging.getLogger(f"hooks.{name}").info(
        "Hook registered",
        extra={{"hook_type": resolved_hook_type, "hook_id": hook_identifier}},
    )


# Auto-register when imported when an event loop is available
import asyncio

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = None

if loop and not loop.is_closed():
    loop.create_task(register_{name}_hook())
'''
        
        files = {
            f"{name}_hook.py": hook_code,
        }
        
        return hook_code, files
    
    def _save_generated_files(self, component_name: str, files: Dict[str, str]) -> None:
        """Save generated files to disk."""
        try:
            base_path = Path(component_name)
            base_path.mkdir(exist_ok=True)
            
            for file_name, content in files.items():
                file_path = base_path / file_name
                file_path.write_text(content)
                console.print(f"💾 Saved {file_path}", style="green")
            
            console.print(f"✅ All files saved to {base_path}/", style="green")
            
        except Exception as e:
            console.print(f"❌ Error saving files: {e}", style="red")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Kari Developer CLI with AG-UI integration")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--token", help="API authentication token")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List components command
    list_parser = subparsers.add_parser("list", help="List system components")
    list_parser.add_argument("--type", choices=["plugin", "extension", "hook", "llm_provider"], 
                           help="Filter by component type")
    
    # Show component details command
    show_parser = subparsers.add_parser("show", help="Show component details")
    show_parser.add_argument("name", help="Component name")
    
    # Execute action command
    action_parser = subparsers.add_parser("action", help="Execute component action")
    action_parser.add_argument("component_id", help="Component ID (type_name)")
    action_parser.add_argument("action", help="Action to execute")
    
    # Chat metrics command
    metrics_parser = subparsers.add_parser("metrics", help="Show chat metrics")
    metrics_parser.add_argument("--hours", type=int, default=24, help="Hours of metrics to show")
    
    # Generate code command
    generate_parser = subparsers.add_parser("generate", help="Generate component boilerplate")
    generate_parser.add_argument("type", choices=["plugin", "extension", "hook"], 
                                help="Component type to generate")
    generate_parser.add_argument("name", help="Component name")
    generate_parser.add_argument("--features", nargs="*", default=[], 
                                help="Features to include")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = KariDevCLI(args.api_url)
    
    # Authenticate if token provided or required
    if args.token or args.command in ["action", "metrics"]:
        if not cli.authenticate(args.token):
            return
    
    # Execute command
    try:
        if args.command == "list":
            cli.list_components(args.type)
        elif args.command == "show":
            cli.show_component_details(args.name)
        elif args.command == "action":
            cli.execute_component_action(args.component_id, args.action)
        elif args.command == "metrics":
            cli.show_chat_metrics(args.hours)
        elif args.command == "generate":
            cli.generate_component_code(args.type, args.name, args.features)
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!", style="yellow")
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    main()