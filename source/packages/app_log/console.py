"""Rich terminal primitives with stable application semantics."""

from __future__ import annotations

import sys
from collections.abc import Iterable, Sequence
from typing import Any, TextIO

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text


class AppConsole:
    """Single terminal presentation surface for the whole workspace."""

    def __init__(
        self,
        *,
        out: TextIO | None = None,
        err: TextIO | None = None,
        color: str = "auto",
    ) -> None:
        self._out_stream = out or sys.stdout
        self._err_stream = err or sys.stderr
        self.configure(color=color)

    def configure(
        self,
        *,
        color: str = "auto",
        out: TextIO | None = None,
        err: TextIO | None = None,
    ) -> None:
        if color not in {"auto", "always", "never"}:
            raise ValueError("color 必须是 auto、always 或 never")
        if out is not None:
            self._out_stream = out
        if err is not None:
            self._err_stream = err
        force_terminal = True if color == "always" else None
        no_color = color == "never"
        self._out = Console(
            file=self._out_stream,
            force_terminal=force_terminal,
            no_color=no_color,
            highlight=False,
            soft_wrap=False,
        )
        self._err = Console(
            file=self._err_stream,
            force_terminal=force_terminal,
            no_color=no_color,
            highlight=False,
            soft_wrap=False,
            stderr=True,
        )

    def print(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: str | None = None,
        err: bool = False,
    ) -> None:
        target = self._err if err else self._out
        text = sep.join(str(item) for item in objects)
        target.print(Text(text, style=style or ""), end=end)

    def emit(self, text: str = "", *, err: bool = False) -> None:
        self.print(text, err=err)

    def blank(self) -> None:
        self._out.print()

    def title(self, name: str, subtitle: str | None = None) -> None:
        body = Text(subtitle or "", style="dim")
        self._out.print(Panel(body, title=Text(name, style="bold cyan"), border_style="cyan"))

    def section(self, name: str) -> None:
        self._out.print(Rule(Text(name, style="bold blue"), style="blue"))

    def field(self, name: str, value: Any = None, *, indent: int = 0) -> None:
        text = Text("  " * indent)
        text.append(name, style="cyan")
        if value is not None:
            text.append("  ")
            text.append(str(value))
        self._out.print(text)

    def item(self, index: int | str, text: str, *, indent: int = 1) -> None:
        line = Text("  " * indent)
        line.append(f"{index}. ", style="cyan")
        line.append(text)
        self._out.print(line)

    def text(self, name: str, content: str, *, indent: int = 1) -> None:
        self.field(name, indent=indent)
        prefix = "  " * (indent + 1)
        if not content:
            self._out.print(Text(f"{prefix}(empty)", style="dim"))
            return
        for line in content.splitlines():
            self._out.print(Text(f"{prefix}{line}"))

    def info(self, message: str) -> None:
        self._status("INFO", message, "blue")

    def success(self, message: str) -> None:
        self._status("SUCCESS", message, "bold green")

    def warning(self, message: str) -> None:
        self._status("WARNING", message, "yellow", err=True)

    def error(self, name: str, message: str | None = None, *, indent: int = 0) -> None:
        content = f"{name}: {message}" if message is not None else name
        prefix = "  " * indent
        self._status("ERROR", f"{prefix}{content}", "bold red", err=True)

    def hint(self, message: str) -> None:
        self._status("HINT", message, "dim cyan")

    def table(
        self,
        columns: Sequence[str],
        rows: Iterable[Sequence[Any]],
        *,
        title: str | None = None,
        styles: Sequence[str | None] | None = None,
    ) -> None:
        table = Table(
            title=title,
            box=box.SQUARE,
            show_lines=True,
            header_style="bold bright_cyan",
            border_style="turquoise4",
            title_style="bold cyan",
        )
        for index, column in enumerate(columns):
            style = styles[index] if styles and index < len(styles) else None
            table.add_column(column, style=style)
        for row in rows:
            table.add_row(*(str(value) for value in row))
        self._out.print(table)

    def log_event(
        self,
        *,
        level: str,
        component: str,
        event_name: str,
        message: str,
        fields: dict[str, Any],
        verbose: bool,
    ) -> None:
        style = {
            "debug": "dim",
            "info": "blue",
            "warning": "yellow",
            "error": "bold red",
        }.get(level, "white")
        target = self._err if level in {"warning", "error"} else self._out
        line = Text()
        line.append(level.upper().ljust(7), style=style)
        line.append(f" {component}", style="cyan")
        line.append(f" · {event_name}", style="dim")
        line.append(f" · {message}")
        target.print(line)
        if verbose and fields:
            for key, value in fields.items():
                detail = Text("         ")
                detail.append(str(key), style="dim cyan")
                detail.append(f"={value}", style="dim")
                target.print(detail)

    def _status(self, label: str, message: str, style: str, *, err: bool = False) -> None:
        target = self._err if err else self._out
        line = Text()
        line.append(label.ljust(8), style=style)
        line.append(message)
        target.print(line)


console = AppConsole()
