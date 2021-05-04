from threading import RLock
from typing import List, Optional

from .console import Console, ConsoleOptions, RenderableType, RenderResult
from .segment import Segment
from .style import StyleType
from .jupyter import JupyterMixin


class Log(JupyterMixin):
    """A log view of renderables.

    Args:
        scrollback (int): Maximum number of lines to store before discarding. Or
            None for infinite. Defaults to 1000.
        style (Style): Style of log.
    """

    def __init__(
        self, scrollback: Optional[int] = 1000, *, style: StyleType = "log"
    ) -> None:
        self.scrollback = scrollback
        self.style = style
        self._buffer: List[RenderableType] = []
        self._line_buffer: List[List[Segment]] = []
        self._lock = RLock()

    def add(self, renderable: RenderableType) -> None:
        """Add a renderable to the log.

        Args:
            renderable (RenderableType): Any renderable type.
        """
        with self._lock:
            self._buffer.append(renderable)

    def _render_buffer(self, console: Console, options: "ConsoleOptions") -> None:
        if self._buffer:
            style = console.get_style(self.style)
            for renderable in self._buffer:
                lines = console.render_lines(renderable, style=style, new_lines=True)
                self._line_buffer.extend(lines)
            if self.scrollback is not None:
                del self._line_buffer[: -self.scrollback]
            del self._buffer[:]

    def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> "RenderResult":
        height = options.height or console.height
        with self._lock:
            self._render_buffer(console, options)
            for line in self._line_buffer[-height:]:
                yield from line


if __name__ == "__main__":

    from rich.console import Console
    from rich.live import Live
    from rich.layout import Layout
    from rich.table import Table
    from time import sleep

    table = Table(
        title="Star Wars Movies",
        caption="Rich example table",
        caption_justify="right",
    )

    table.add_column("Released", header_style="bright_cyan", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Box Office", justify="right", style="green")

    table.add_row(
        "Dec 20, 2019",
        "Star Wars: The Rise of Skywalker",
        "$952,110,690",
    )
    table.add_row("May 25, 2018", "Solo: A Star Wars Story", "$393,151,347")

    console = Console()

    log = Log()
    layout = Layout()
    layout.split_row(Layout(name="demo"), Layout(log, name="log"))

    with Live(layout, refresh_per_second=20, screen=True):
        while True:
            log.add(table)
            sleep(0.2)
            log.add(layout.tree)
            sleep(0.2)
            log.add("Add anything to the log")
