"""Async-ready Text-based UI for diagnostics."""

from __future__ import annotations

import asyncio
import urwid

class TuiFallback:
    """Simple dashboard for plugin states and system metrics."""

    def __init__(self, plugin_states: dict, system_metrics: dict) -> None:
        """Initialize the TUI with plugin information and metrics."""
        self.plugin_states = plugin_states
        self.system_metrics = system_metrics
        self.loop = None

        self.header = urwid.Text("💀 OSIRIS TUI Fallback — Evil Twin Mode 💀", align="center")
        self.footer = urwid.Text("Press Q to Quit | Arrows to Navigate", align="center")

        self.plugin_list = self._create_plugin_list()
        self.metrics_list = self._create_metrics_list()

        columns = urwid.Columns([
            ('weight', 1, urwid.LineBox(self.plugin_list, title="Plugins")),
            ('weight', 1, urwid.LineBox(self.metrics_list, title="System Metrics"))
        ])

        self.layout = urwid.Frame(
            header=urwid.AttrWrap(self.header, 'header'),
            body=columns,
            footer=urwid.AttrWrap(self.footer, 'footer')
        )

    def _create_plugin_list(self) -> urwid.ListBox:
        """Return a widget listing plugins and their states."""
        items = []
        for name, status in self.plugin_states.items():
            status_icon = "🟢" if status else "🔴"
            txt = f"{name}: {status_icon} {'ON' if status else 'OFF'}"
            items.append(urwid.Text(txt))
        return urwid.ListBox(urwid.SimpleFocusListWalker(items))

    def _create_metrics_list(self) -> urwid.ListBox:
        """Return a widget listing basic system metrics."""
        items = []
        for key, val in self.system_metrics.items():
            txt = f"{key}: {val}"
            items.append(urwid.Text(txt))
        return urwid.ListBox(urwid.SimpleFocusListWalker(items))

    def main(self) -> None:
        """Run the blocking TUI loop."""
        palette = [
            ('header', 'black', 'light gray'),
            ('footer', 'black', 'light gray'),
        ]
        self.loop = urwid.MainLoop(self.layout, palette, unhandled_input=self.unhandled_input)
        self.loop.run()

    def unhandled_input(self, key: str) -> None:
        """Handle global key bindings."""
        if key in ("q", "Q"):
            raise urwid.ExitMainLoop()

async def start_tui(plugin_states: dict, system_metrics: dict) -> None:
    """Launch the TUI in a thread and return when closed."""
    tui_app = TuiFallback(plugin_states, system_metrics)
    await asyncio.to_thread(tui_app.main)
