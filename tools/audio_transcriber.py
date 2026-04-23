#!/usr/bin/env python3
"""
Audio Transcriber - Beautiful TUI/CLI Tool
Transcribe audio files to text using OpenAI Whisper (local, free)

Modes:
  url    — Download from a web URL then transcribe
  file   — Transcribe a single local audio file
  folder — Recursively transcribe all audio files in a folder

Usage:
  python audio_transcriber.py                          # Interactive TUI
  python audio_transcriber.py <url|file|folder> [opts] # CLI mode

Examples:
  python audio_transcriber.py
  python audio_transcriber.py https://example.com/speech.mp3
  python audio_transcriber.py recording.mp3 --output-format pdf
  python audio_transcriber.py /audio/folder/ --output-dir ./transcripts
  python audio_transcriber.py speech.wav --model small --language vi
"""

import os
import re
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from colorama import init as colorama_init
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
import questionary
from questionary import Style as QStyle

colorama_init(autoreset=True)

# ---------------------------------------------------------------------------
# Questionary arrow-key theme
# ---------------------------------------------------------------------------

_Q_STYLE = QStyle(
    [
        ("qmark",       "fg:#00d7ff bold"),
        ("question",    "bold"),
        ("answer",      "fg:#00ff87 bold"),
        ("pointer",     "fg:#00d7ff bold"),
        ("highlighted", "fg:#00d7ff bold"),
        ("selected",    "fg:#00ff87"),
        ("separator",   "fg:#5f5f5f"),
        ("instruction", "fg:#5f5f5f italic"),
        ("text",        ""),
        ("disabled",    "fg:#5f5f5f italic"),
    ]
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AUDIO_EXTENSIONS: frozenset = frozenset(
    {
        ".mp3",
        ".mp4",
        ".wav",
        ".flac",
        ".m4a",
        ".ogg",
        ".wma",
        ".aac",
        ".webm",
        ".mkv",
        ".opus",
        ".mpeg",
        ".avi",
        ".mov",
    }
)

WHISPER_MODELS: List[str] = ["tiny", "base", "small", "medium", "large"]

VERSION = "1.0.0"

_CONTENT_TYPE_EXT: Dict[str, str] = {
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/ogg": ".ogg",
    "audio/flac": ".flac",
    "audio/aac": ".aac",
    "audio/webm": ".webm",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/mpeg": ".mpeg",
}


# ---------------------------------------------------------------------------
# AudioDownloader
# ---------------------------------------------------------------------------


class AudioDownloader:
    """Downloads audio from a URL using requests (direct links) or yt-dlp (streaming sites)."""

    def __init__(self, console: Console) -> None:
        self.console = console

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_direct_audio_url(url: str) -> bool:
        path = url.split("?")[0].lower()
        return any(path.endswith(ext) for ext in AUDIO_EXTENSIONS)

    @staticmethod
    def _filename_from_response(response: Any, url: str) -> str:
        """Determine a safe filename from the HTTP response and URL."""
        # 1. Content-Disposition header
        cd = response.headers.get("content-disposition", "")
        if cd:
            matches = re.findall(
                r'filename\*?=["\']?(?:UTF-\d+\'\')?([^;\n"\']+)', cd, re.IGNORECASE
            )
            if matches:
                name = matches[0].strip()
                if name:
                    return name

        # 2. Path segment of the URL
        url_segment = url.split("?")[0].split("/")[-1]
        if "." in url_segment and any(
            url_segment.lower().endswith(ext) for ext in AUDIO_EXTENSIONS
        ):
            return url_segment

        # 3. Guess from Content-Type
        ct = response.headers.get("content-type", "").split(";")[0].strip().lower()
        ext = _CONTENT_TYPE_EXT.get(ct, ".mp3")
        return f"audio_download{ext}"

    # ------------------------------------------------------------------
    # Download methods
    # ------------------------------------------------------------------

    def _download_with_requests(self, url: str, dest_dir: Path) -> Optional[Path]:
        """Attempt a direct HTTP download."""
        try:
            import requests  # type: ignore

            session = requests.Session()
            session.headers["User-Agent"] = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
            )

            head = session.head(url, allow_redirects=True, timeout=15)
            filename = self._filename_from_response(head, url)
            dest_path = dest_dir / filename

            response = session.get(url, stream=True, timeout=60)
            response.raise_for_status()

            with open(dest_path, "wb") as fh:
                for chunk in response.iter_content(chunk_size=65_536):
                    if chunk:
                        fh.write(chunk)

            if dest_path.stat().st_size > 0:
                return dest_path

            dest_path.unlink(missing_ok=True)
            return None

        except Exception:
            return None

    def _download_with_ytdlp(self, url: str, dest_dir: Path) -> Optional[Path]:
        """Download via yt-dlp (supports YouTube, SoundCloud, and 1000+ sites)."""
        try:
            import yt_dlp  # type: ignore

            downloaded: List[str] = []

            def _hook(d: dict) -> None:
                if d.get("status") == "finished":
                    downloaded.append(d["filename"])

            ydl_opts: Dict[str, Any] = {
                "format": "bestaudio/best",
                "outtmpl": str(dest_dir / "%(title).100s.%(ext)s"),
                "progress_hooks": [_hook],
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Prefer the file reported by the hook
            if downloaded:
                path = Path(downloaded[-1])
                if path.exists():
                    return path

            # Fallback: newest audio file in dest_dir
            candidates = [
                f
                for f in dest_dir.iterdir()
                if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS
            ]
            if candidates:
                return max(candidates, key=lambda p: p.stat().st_mtime)

            return None

        except Exception:
            return None

    def download(self, url: str, dest_dir: Path) -> Tuple[Optional[Path], str]:
        """
        Download audio from *url* into *dest_dir*.
        Returns (local_path, method) where method is 'requests', 'yt-dlp', or 'failed'.
        """
        dest_dir.mkdir(parents=True, exist_ok=True)

        if self._is_direct_audio_url(url):
            result = self._download_with_requests(url, dest_dir)
            if result:
                return result, "requests"

        result = self._download_with_ytdlp(url, dest_dir)
        if result:
            return result, "yt-dlp"

        # Last resort for direct-looking URLs that failed the HEAD check
        result = self._download_with_requests(url, dest_dir)
        if result:
            return result, "requests"

        return None, "failed"


# ---------------------------------------------------------------------------
# TranscriptionEngine
# ---------------------------------------------------------------------------


class TranscriptionEngine:
    """Wraps OpenAI Whisper for on-device audio transcription."""

    def __init__(self, model_name: str = "base") -> None:
        self.model_name = model_name
        self._model: Any = None

    def load_model(self) -> Any:
        """Lazily load the Whisper model (cached after first call)."""
        if self._model is None:
            import whisper  # type: ignore  # noqa: PLC0415

            self._model = whisper.load_model(self.model_name)
        return self._model

    def transcribe(
        self, audio_path: Path, language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe *audio_path* and return a result dict with keys:
        text, segments, language, duration (seconds), word_count.
        """
        model = self.load_model()
        kwargs: Dict[str, Any] = {}
        if language and language.lower() not in ("auto", ""):
            kwargs["language"] = language

        raw = model.transcribe(str(audio_path), **kwargs)

        text: str = (raw.get("text") or "").strip()
        segments: list = raw.get("segments") or []
        duration = segments[-1]["end"] if segments else 0.0

        return {
            "text": text,
            "segments": segments,
            "language": raw.get("language", "unknown"),
            "duration": duration,
            "word_count": len(text.split()) if text else 0,
        }


# ---------------------------------------------------------------------------
# OutputWriter
# ---------------------------------------------------------------------------


class OutputWriter:
    """Writes a transcription result to a .txt or .pdf file."""

    @staticmethod
    def _fmt_duration(seconds: float) -> str:
        if seconds <= 0:
            return "unknown"
        h, rem = divmod(int(seconds), 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    def _meta_lines(
        self, transcription: Dict[str, Any], source_name: str
    ) -> List[Tuple[str, str]]:
        return [
            ("Source", source_name),
            ("Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ("Language", transcription["language"]),
            ("Duration", self._fmt_duration(transcription["duration"])),
            ("Words", f"{transcription['word_count']:,}"),
        ]

    def write_txt(
        self,
        transcription: Dict[str, Any],
        source_name: str,
        output_path: Path,
    ) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sep = "=" * 60
        lines = [
            sep,
            " AUDIO TRANSCRIPT",
            sep,
        ]
        for label, value in self._meta_lines(transcription, source_name):
            lines.append(f" {label:<10}: {value}")
        lines += [sep, "", transcription["text"], ""]
        output_path.write_text("\n".join(lines), encoding="utf-8")

    def write_pdf(
        self,
        transcription: Dict[str, Any],
        source_name: str,
        output_path: Path,
    ) -> None:
        from fpdf import FPDF  # type: ignore  # noqa: PLC0415

        output_path.parent.mkdir(parents=True, exist_ok=True)

        pdf = FPDF()
        pdf.set_margins(15, 15, 15)
        pdf.add_page()

        # ── Title ──────────────────────────────────────────────────────
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(30, 30, 90)
        pdf.cell(
            0, 14, "Audio Transcript", new_x="LMARGIN", new_y="NEXT", align="C"
        )

        # ── Rule ───────────────────────────────────────────────────────
        pdf.set_draw_color(80, 80, 170)
        pdf.set_line_width(0.8)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(5)

        # ── Metadata ───────────────────────────────────────────────────
        for label, value in self._meta_lines(transcription, source_name):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(32, 6, f"{label}:", border=0)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(30, 30, 30)
            pdf.multi_cell(0, 6, value)

        # ── Divider ────────────────────────────────────────────────────
        pdf.ln(3)
        pdf.set_draw_color(180, 180, 210)
        pdf.set_line_width(0.3)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(6)

        # ── Body ───────────────────────────────────────────────────────
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(15, 15, 15)
        pdf.multi_cell(0, 7, transcription["text"])

        pdf.output(str(output_path))


# ---------------------------------------------------------------------------
# AudioTranscriberApp  — orchestrator with TUI & CLI
# ---------------------------------------------------------------------------


class AudioTranscriberApp:
    """Main application: drives the interactive TUI and the headless CLI."""

    def __init__(self) -> None:
        self.console = Console()
        self.downloader = AudioDownloader(self.console)
        self.engine: Optional[TranscriptionEngine] = None
        self.writer = OutputWriter()

    # ==================================================================
    # Rich panel / table builders
    # ==================================================================

    def _header(self) -> Panel:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        grid = Table.grid(padding=1)
        grid.add_column(justify="left")
        grid.add_column(justify="center")
        grid.add_column(justify="right")
        grid.add_row(
            f"[bold cyan]🎙 Audio Transcriber v{VERSION}[/bold cyan]",
            "[bold yellow]🤖 Powered by OpenAI Whisper[/bold yellow]",
            f"[dim]{now}[/dim]",
        )
        grid.add_row(
            "[dim]URL · File · Folder modes[/dim]",
            "",
            f"[dim]PID: {os.getpid()}[/dim]",
        )
        return Panel(grid, style="bright_blue", padding=(0, 1))

    def _status(self, text: str, kind: str = "info") -> Panel:
        cfg = {
            "info":       ("blue",    "ℹ️ "),
            "success":    ("green",   "✅ "),
            "error":      ("red",     "❌ "),
            "warning":    ("yellow",  "⚠️  "),
            "processing": ("magenta", "⚡ "),
        }
        style, icon = cfg.get(kind, ("white", "• "))
        return Panel(
            f"{icon}{text}",
            style=style,
            padding=(0, 1),
            title=f"[bold]{kind.upper()}[/bold]",
        )

    def _settings_panel(self, settings: dict) -> Panel:
        icons = {"url": "🌐", "file": "📄", "folder": "📁"}
        mode = settings.get("mode", "?")
        grid = Table.grid(padding=1)
        grid.add_column(justify="left", style="dim")
        grid.add_column(justify="left")
        grid.add_row(
            "Mode:",
            f"{icons.get(mode, '•')} [bold cyan]{mode.upper()}[/bold cyan]",
        )
        grid.add_row("Input:", f"[yellow]{settings.get('input', '?')}[/yellow]")
        grid.add_row(
            "Output Format:",
            f"[green].{settings.get('output_format', 'txt')}[/green]",
        )
        grid.add_row(
            "Output Directory:",
            f"[cyan]{settings.get('output_dir', '.')}[/cyan]",
        )
        grid.add_row(
            "Whisper Model:",
            f"[magenta]{settings.get('model', 'base')}[/magenta]",
        )
        lang = settings.get("language") or "auto-detect"
        grid.add_row("Language:", f"[dim]{lang}[/dim]")
        return Panel(
            grid,
            title="[bold green]⚙️  Settings[/bold green]",
            style="green",
            padding=(1, 2),
        )

    def _results_table(self, results: List[dict]) -> Table:
        table = Table(
            title="[bold green]📋 Transcription Results[/bold green]",
            border_style="bright_blue",
            header_style="bold cyan",
            show_lines=True,
        )
        table.add_column("File", style="yellow", max_width=28, overflow="fold")
        table.add_column("Language", justify="center", style="cyan")
        table.add_column("Duration", justify="right")
        table.add_column("Words", justify="right", style="magenta")
        table.add_column("Output", style="dim", max_width=38, overflow="fold")
        table.add_column("Status", justify="center")

        for r in results:
            ok = r["status"] == "success"
            status_str = (
                "[bold green]✅ OK[/bold green]"
                if ok
                else "[bold red]❌ ERR[/bold red]"
            )
            duration_str = OutputWriter._fmt_duration(r.get("duration", 0))
            words_str = f"{r.get('word_count', 0):,}" if ok else "-"
            output_str = (
                str(r.get("output_path", ""))
                if ok
                else r.get("error", "unknown error")
            )
            table.add_row(
                r.get("audio_file", "?"),
                r.get("language", "-"),
                duration_str,
                words_str,
                output_str,
                status_str,
            )
        return table

    def _summary_panel(self, results: List[dict], elapsed: float) -> Panel:
        ok = [r for r in results if r["status"] == "success"]
        err_count = len(results) - len(ok)
        total_words = sum(r.get("word_count", 0) for r in ok)

        grid = Table.grid(padding=1)
        grid.add_column(justify="left", style="dim")
        grid.add_column(justify="left")
        grid.add_row("Files processed:", f"[bold]{len(results)}[/bold]")
        grid.add_row("Successful:", f"[bold green]{len(ok)}[/bold green]")
        if err_count:
            grid.add_row("Errors:", f"[bold red]{err_count}[/bold red]")
        grid.add_row("Total words:", f"[magenta]{total_words:,}[/magenta]")
        grid.add_row("Total time:", f"[yellow]{elapsed:.1f}s[/yellow]")
        return Panel(
            grid,
            title="[bold green]🎉 Transcription Complete[/bold green]",
            style="green",
            padding=(1, 2),
        )

    # ==================================================================
    # Mode detection
    # ==================================================================

    @staticmethod
    def detect_mode(input_str: str) -> str:
        """Auto-detect url / folder / file mode from the input string."""
        if re.match(r"^https?://", input_str, re.IGNORECASE):
            return "url"
        if input_str.endswith("/") or input_str.endswith("\\"):
            return "folder"
        return "file"

    # ==================================================================
    # Core transcription helpers
    # ==================================================================

    def _load_engine(self, model_name: str) -> bool:
        """Load Whisper model; returns False and prints error on failure."""
        # Reuse already-loaded engine for the same model (important in app-loop mode)
        if (
            self.engine is not None
            and self.engine.model_name == model_name
            and self.engine._model is not None
        ):
            self.console.print(
                self._status(
                    f"Model [bold]{model_name}[/bold] already loaded — skipping reload",
                    "success",
                )
            )
            return True

        self.console.print(
            self._status(
                f"Loading Whisper model [bold]{model_name}[/bold]"
                "  [dim](first run downloads model weights)[/dim]",
                "processing",
            )
        )
        try:
            self.engine = TranscriptionEngine(model_name)
            self.engine.load_model()
            self.console.print(
                self._status(
                    f"Model [bold]{model_name}[/bold] ready", "success"
                )
            )
            return True
        except ImportError:
            self.console.print(
                self._status(
                    "openai-whisper is not installed.\n"
                    "Run: pip install -r tools/audio_transcriber_requirements.txt",
                    "error",
                )
            )
            return False
        except Exception as exc:
            self.console.print(self._status(f"Failed to load model: {exc}", "error"))
            return False

    def _transcribe_one(
        self,
        audio_path: Path,
        settings: dict,
        progress: Optional[Progress] = None,
        task_id: Any = None,
    ) -> dict:
        """Transcribe a single file; optionally updates an existing Progress task."""
        if progress and task_id is not None:
            progress.update(
                task_id,
                description=f"[cyan]Transcribing:[/cyan] {audio_path.name[:45]}",
            )
        try:
            t0 = time.time()
            result = self.engine.transcribe(audio_path, settings.get("language"))

            output_dir = Path(settings.get("output_dir", "."))
            fmt = settings.get("output_format", "txt")
            out_path = output_dir / f"{audio_path.stem}.{fmt}"

            if fmt == "pdf":
                self.writer.write_pdf(result, audio_path.name, out_path)
            else:
                self.writer.write_txt(result, audio_path.name, out_path)

            return {
                "status": "success",
                "audio_file": audio_path.name,
                "output_path": out_path,
                "language": result["language"],
                "duration": result["duration"],
                "word_count": result["word_count"],
                "elapsed": time.time() - t0,
            }
        except Exception as exc:
            return {
                "status": "error",
                "audio_file": audio_path.name,
                "output_path": None,
                "error": str(exc),
                "language": "?",
                "duration": 0.0,
                "word_count": 0,
                "elapsed": 0.0,
            }

    def _transcribe_one_with_spinner(
        self, audio_path: Path, settings: dict
    ) -> dict:
        """Wrap _transcribe_one with a single-file spinner Progress."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task(
                f"Transcribing [bold]{audio_path.name[:45]}[/bold]...",
                total=None,
            )
            result = self._transcribe_one(audio_path, settings, progress, task)

        if result["status"] == "success":
            self.console.print(
                self._status(
                    f"Saved → [bold]{result['output_path']}[/bold]  "
                    f"[dim]({result['word_count']:,} words, "
                    f"{OutputWriter._fmt_duration(result['duration'])})[/dim]",
                    "success",
                )
            )
        else:
            self.console.print(
                self._status(result.get("error", "Unknown error"), "error")
            )
        return result

    # ==================================================================
    # Mode processors
    # ==================================================================

    def process_url(self, url: str, settings: dict) -> List[dict]:
        self.console.print(
            self._status("Downloading audio from URL…", "processing")
        )

        output_dir = Path(settings.get("output_dir", "."))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:
            dl_task = progress.add_task("Connecting…", total=None)
            audio_path, method = self.downloader.download(url, output_dir)
            progress.update(dl_task, description="Done", completed=True)

        if not audio_path:
            self.console.print(
                self._status(
                    "Download failed. Check the URL or install yt-dlp for streaming sites.",
                    "error",
                )
            )
            return [
                {
                    "status": "error",
                    "audio_file": url,
                    "error": "Download failed",
                    "output_path": None,
                    "language": "?",
                    "duration": 0.0,
                    "word_count": 0,
                    "elapsed": 0.0,
                }
            ]

        self.console.print(
            self._status(
                f"Downloaded via [bold]{method}[/bold]: [yellow]{audio_path.name}[/yellow]",
                "success",
            )
        )
        self.console.print()
        return [self._transcribe_one_with_spinner(audio_path, settings)]

    def process_file(self, file_path: Path, settings: dict) -> List[dict]:
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            self.console.print(self._status(msg, "error"))
            return [
                {
                    "status": "error",
                    "audio_file": str(file_path),
                    "error": msg,
                    "output_path": None,
                    "language": "?",
                    "duration": 0.0,
                    "word_count": 0,
                    "elapsed": 0.0,
                }
            ]

        if file_path.suffix.lower() not in AUDIO_EXTENSIONS:
            self.console.print(
                self._status(
                    f"Extension [bold]{file_path.suffix}[/bold] is not in the known "
                    "audio list — attempting anyway…",
                    "warning",
                )
            )

        return [self._transcribe_one_with_spinner(file_path, settings)]

    def process_folder(self, folder_path: Path, settings: dict) -> List[dict]:
        if not folder_path.exists() or not folder_path.is_dir():
            msg = f"Folder not found: {folder_path}"
            self.console.print(self._status(msg, "error"))
            return [
                {
                    "status": "error",
                    "audio_file": str(folder_path),
                    "error": msg,
                    "output_path": None,
                    "language": "?",
                    "duration": 0.0,
                    "word_count": 0,
                    "elapsed": 0.0,
                }
            ]

        audio_files = sorted(
            f
            for f in folder_path.rglob("*")
            if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS
        )

        if not audio_files:
            self.console.print(
                self._status(f"No audio files found in: {folder_path}", "warning")
            )
            return []

        self.console.print(
            self._status(
                f"Found [bold]{len(audio_files)}[/bold] audio file(s) in "
                f"[cyan]{folder_path}[/cyan]",
                "info",
            )
        )
        self.console.print()

        base_output_dir = Path(settings.get("output_dir", "."))
        results: List[dict] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:
            overall = progress.add_task("Transcribing…", total=len(audio_files))

            for audio_file in audio_files:
                # Preserve relative sub-directory structure in output
                rel = audio_file.relative_to(folder_path).parent
                file_settings = {
                    **settings,
                    "output_dir": str(base_output_dir / rel),
                }
                result = self._transcribe_one(
                    audio_file, file_settings, progress, overall
                )
                results.append(result)
                progress.advance(overall)

        return results

    # ==================================================================
    # Shared execution core
    # ==================================================================

    def _execute(self, mode: str, input_val: str, settings: dict) -> None:
        """Load model then dispatch to the correct process_* method."""
        if not self._load_engine(settings["model"]):
            return

        self.console.print()
        t0 = time.time()

        if mode == "url":
            results = self.process_url(input_val, settings)
        elif mode == "file":
            results = self.process_file(Path(input_val), settings)
        elif mode == "folder":
            results = self.process_folder(
                Path(input_val.rstrip("/\\")), settings
            )
        else:
            self.console.print(self._status(f"Unknown mode: {mode}", "error"))
            return

        elapsed = time.time() - t0

        if results:
            self.console.print()
            self.console.print(self._results_table(results))

        self.console.print()
        self.console.print(self._summary_panel(results, elapsed))

    # ==================================================================
    # Interactive TUI
    # ==================================================================

    def run_tui(self) -> None:
        self.console.clear()
        self.console.print(self._header())
        self.console.print()

        # ── About panel (shown only on first launch) ───────────────────
        self.console.print(
            Panel(
                "[bold]Welcome to Audio Transcriber![/bold]\n\n"
                "Transcribes audio to [green].txt[/green] or [green].pdf[/green] "
                "using OpenAI Whisper — runs [bold]locally[/bold], no API key.\n\n"
                "Formats: " + "  ".join(sorted(AUDIO_EXTENSIONS)) + "\n"
                "Models:  tiny · base · small · medium · large  "
                "[dim](larger = more accurate, slower)[/dim]\n\n"
                "[dim]Navigate with [bold]↑ ↓[/bold] arrows  ·  "
                "[bold]Enter[/bold] to select  ·  [bold]Ctrl+C[/bold] to quit[/dim]",
                title="[bold blue]ℹ️  About[/bold blue]",
                style="blue",
                padding=(1, 2),
            )
        )
        self.console.print()

        while True:  # ── App loop ──────────────────────────────────────

            # ── Mode ───────────────────────────────────────────────────
            mode = questionary.select(
                "Select transcription mode:",
                choices=[
                    questionary.Choice(
                        "🌐  URL    — Download audio from a web URL then transcribe",
                        value="url",
                    ),
                    questionary.Choice(
                        "📄  File   — Transcribe a single local audio file",
                        value="file",
                    ),
                    questionary.Choice(
                        "📁  Folder — Recursively transcribe all audio in a folder",
                        value="folder",
                    ),
                ],
                style=_Q_STYLE,
                use_arrow_keys=True,
            ).ask()
            if mode is None:
                return  # Ctrl+C
            self.console.print()

            # ── Input ──────────────────────────────────────────────────
            if mode == "file":
                input_val = questionary.path(
                    "Enter audio file path:",
                    style=_Q_STYLE,
                ).ask()
            elif mode == "folder":
                input_val = questionary.path(
                    "Enter folder path:",
                    only_directories=True,
                    style=_Q_STYLE,
                ).ask()
            else:
                input_val = questionary.text(
                    "Enter audio URL:",
                    validate=lambda v: (
                        True
                        if re.match(r"^https?://", v.strip())
                        else "Must start with http:// or https://"
                    ),
                    style=_Q_STYLE,
                ).ask()
            if input_val is None:
                return
            input_val = input_val.strip()
            self.console.print()

            # ── Output format ──────────────────────────────────────────
            output_format = questionary.select(
                "Output format:",
                choices=[
                    questionary.Choice("📄  txt — Plain text file", value="txt"),
                    questionary.Choice("📑  pdf — Formatted PDF with metadata header", value="pdf"),
                ],
                style=_Q_STYLE,
                use_arrow_keys=True,
            ).ask()
            if output_format is None:
                return
            self.console.print()

            # ── Output directory ───────────────────────────────────────
            output_dir_raw = questionary.path(
                "Output directory:",
                default=str(Path.cwd()),
                only_directories=True,
                style=_Q_STYLE,
            ).ask()
            if output_dir_raw is None:
                return
            output_dir = output_dir_raw.strip() or str(Path.cwd())
            self.console.print()

            # ── Whisper model ──────────────────────────────────────────
            model_name = questionary.select(
                "Whisper model:",
                choices=[
                    questionary.Choice("tiny    — Fastest · lowest accuracy   (~39 M params)",  value="tiny"),
                    questionary.Choice("base    — Good balance · recommended   (~74 M params)",  value="base"),
                    questionary.Choice("small   — Better accuracy · slower    (~244 M params)",  value="small"),
                    questionary.Choice("medium  — High accuracy · much slower (~769 M params)",  value="medium"),
                    questionary.Choice("large   — Best accuracy · very slow   (~1.5 B params)",  value="large"),
                ],
                default="base",
                style=_Q_STYLE,
                use_arrow_keys=True,
            ).ask()
            if model_name is None:
                return
            self.console.print()

            # ── Language ───────────────────────────────────────────────
            language_raw = questionary.text(
                "Language code (en, vi, fr, ja … or 'auto' for auto-detect):",
                default="auto",
                style=_Q_STYLE,
            ).ask()
            if language_raw is None:
                return
            language = (
                None
                if language_raw.strip().lower() in ("auto", "")
                else language_raw.strip()
            )
            self.console.print()

            # ── Settings summary + confirm ─────────────────────────────
            settings: Dict[str, Any] = {
                "mode": mode,
                "input": input_val,
                "output_format": output_format,
                "output_dir": output_dir,
                "model": model_name,
                "language": language,
            }
            self.console.print(self._settings_panel(settings))
            self.console.print()

            confirmed = questionary.confirm(
                "Start transcription?",
                default=True,
                style=_Q_STYLE,
            ).ask()
            if not confirmed:
                self.console.print()
                self.console.print(self._status("Transcription cancelled.", "warning"))
            else:
                self.console.print()
                self._execute(mode, input_val, settings)

            # ── Restart / Exit prompt ──────────────────────────────────
            self.console.print()
            next_action = questionary.select(
                "What would you like to do next?",
                choices=[
                    questionary.Choice("🔄  New transcription — start again", value="restart"),
                    questionary.Choice("🚪  Exit",                            value="exit"),
                ],
                style=_Q_STYLE,
                use_arrow_keys=True,
            ).ask()
            if next_action != "restart":
                break
            self.console.clear()
            self.console.print(self._header())
            self.console.print()

    # ==================================================================
    # Headless CLI
    # ==================================================================

    def run_cli(self, args: argparse.Namespace) -> None:
        self.console.print(self._header())
        self.console.print()

        input_val: str = args.input
        mode: str = args.mode or self.detect_mode(input_val)
        language = (
            args.language
            if args.language and args.language.lower() not in ("auto", "")
            else None
        )

        settings: Dict[str, Any] = {
            "mode": mode,
            "input": input_val,
            "output_format": args.output_format,
            "output_dir": args.output_dir,
            "model": args.model,
            "language": language,
        }

        self.console.print(self._settings_panel(settings))
        self.console.print()
        self._execute(mode, input_val, settings)


# ---------------------------------------------------------------------------
# CLI argument parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audio_transcriber",
        description="Transcribe audio to text with OpenAI Whisper (runs locally).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                              # Interactive TUI
  %(prog)s https://example.com/speech.mp3               # URL (auto-detected)
  %(prog)s recording.mp3 --output-format pdf            # File → PDF
  %(prog)s /audio/folder/                               # Folder (auto-detected)
  %(prog)s /audio/folder/ --output-dir ./transcripts    # Folder + custom output
  %(prog)s speech.wav --model small --language vi       # Vietnamese, small model
        """,
    )

    parser.add_argument(
        "input",
        nargs="?",
        metavar="INPUT",
        help="URL, file path, or folder path — omit to launch the interactive TUI.",
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["url", "file", "folder"],
        default=None,
        help="Explicitly set mode (auto-detected from INPUT when omitted).",
    )
    parser.add_argument(
        "--output-format", "-f",
        choices=["txt", "pdf"],
        default="txt",
        dest="output_format",
        metavar="FORMAT",
        help="Transcript file format: txt or pdf  (default: txt).",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=str(Path.cwd()),
        dest="output_dir",
        metavar="PATH",
        help="Directory for output files  (default: current working directory).",
    )
    parser.add_argument(
        "--model",
        choices=WHISPER_MODELS,
        default="base",
        metavar="MODEL",
        help="Whisper model size: tiny/base/small/medium/large  (default: base).",
    )
    parser.add_argument(
        "--language", "-l",
        default=None,
        metavar="LANG",
        help="Audio language code, e.g. en, vi, fr.  Default: auto-detect.",
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"%(prog)s {VERSION}",
    )
    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    try:
        parser = _build_parser()
        args = parser.parse_args()
        app = AudioTranscriberApp()

        if args.input is None:
            app.run_tui()
        else:
            app.run_cli(args)

    except KeyboardInterrupt:
        Console().print(Panel("👋 Goodbye!", style="yellow", padding=(0, 1)))
    except Exception as exc:
        Console().print(
            Panel(
                f"❌ Unexpected error: {exc}",
                style="red",
                title="[bold red]ERROR[/bold red]",
                padding=(1, 2),
            )
        )
        raise


if __name__ == "__main__":
    main()
