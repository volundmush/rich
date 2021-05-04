from threading import RLock
from typing import Iterable, List, Optional

from . import get_console
from .console import Console, ConsoleOptions, RenderableType, RenderResult
from .jupyter import JupyterMixin
from .segment import Segment
from .style import StyleType


class Log(JupyterMixin):
    """A log view of renderables. When you :meth:`~rich.log.Log.add` add a renderable, it will be
    immediately rendered and stored in a buffer to be displayed when the Log itself is rendered.
    The effect is similar to the normal operation of terminals with a scrolling buffer, but can be
    displayed within another renderable, such as :class:`~rich.layout.Layout`.

    Args:
        scrollback (int): Maximum number of lines to store before discarding. Or ``None`` for infinite.
            Defaults to 1000.
        style (Style): Style of log.
        console (Console): The console use when rendering.
    """

    def __init__(
        self,
        scrollback: Optional[int] = 1000,
        *,
        style: StyleType = "log",
        console: Optional[Console] = None
    ) -> None:
        self.scrollback = scrollback
        self.style = style
        self.console = console or get_console()
        self._buffer: List[List[Segment]] = []
        self._lock = RLock()

    def add(self, *renderables: RenderableType) -> None:
        """Add a renderable to the log.

        Args:
            *renderables (RenderableType): Any renderable type.
        """
        with self._lock:
            self._buffer.extend(self._render(self.console, renderables))
            if self.scrollback is not None:
                del self._buffer[: -self.scrollback]

    def _render(
        self, console: Console, renderables: Iterable[RenderableType]
    ) -> List[List[Segment]]:
        """Render a number of renderables with the given console."""
        rendered_lines: List[List[Segment]] = []
        style = console.get_style(self.style)
        for renderable in renderables:
            lines = console.render_lines(renderable, style=style, new_lines=True)
            rendered_lines.extend(lines)
        return rendered_lines

    def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> "RenderResult":
        height = options.height or console.height
        with self._lock:
            for line in self._buffer[-height:]:
                yield from line


if __name__ == "__main__":

    from time import sleep

    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.table import Table

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

    log.add("hello", "world")
    console.print(layout)

    with Live(layout, refresh_per_second=20, screen=True):
        while True:
            log.add(table)
            sleep(0.2)
            log.add(layout.tree)
            sleep(0.2)
            log.add("Add anything to the log")
