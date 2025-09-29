#!/usr/bin/env python3
"""
Obsidian Notes Uploader - Beautiful CLI Tool
Zip and upload Obsidian notes from C:\\Notes to Firebase Storage
Enhanced TUI with rich styling and progress tracking
"""

import os
import sys
import json
import base64
import zipfile
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

import firebase_admin
from firebase_admin import credentials
from google.cloud import storage as gcs
from google.cloud.exceptions import NotFound, Forbidden, Unauthorized

from colorama import Fore, Back, Style, init
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    MofNCompleteColumn,
)
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.align import Align

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class ObsidianNotesUploader:
    """Beautiful CLI tool for uploading Obsidian notes to Firebase Storage"""

    def __init__(self):
        """Initialize the uploader with hardcoded Firebase credentials"""

        # Firebase configuration - HARDCODED CREDENTIALS
        self.PROJECT_ID = "useful-tools-api"
        self.STORAGE_BUCKET = "useful-tools-api.firebasestorage.app"

        # Hardcoded service account credentials (replace with your actual credentials)
        # NOTE: In production, consider using environment variables or secure credential storage
        self.SERVICE_ACCOUNT_CREDENTIALS = {
            "type": "service_account",
            "project_id": "useful-tools-api",
            "private_key_id": "140c7f4b5f5a097961abceb81b34396e945d4d09",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC3e0uLTxwOQTi0\notXKy3UHyLm3m3q78APcu1QUReYCzxOXg/ykc+uzDaJ8J2FKsiehjHJ4y1lD33nS\nxjHIH5Uif/C+z4xsPegayqN1KLnesatjQPQ0J2sYzzXuchGoe7rAKIUxC+tg1xEe\nVFWiSBJa4aCjvRL0TboRZHB+w1e/IG/jwD8Nhbxq2hyJicq7kQDberlRkW03oFl2\nQYBLHLSd9bxeeJeMSpWa+SeTfGXb6IZfFegqSK8WqElTbjohZh7ZU8N5WoijIX1z\nBHuCUB1ucklWHzcRlbqCW+y+84TMnJozKsRkYF3cFVrcShHzwKSkF6pAUoI+lMLJ\nq7C7Fm/HAgMBAAECggEAGbXxwo4t2MOD7jAJNFcpSZNzjsp/OtmpuOMZJ5QZ5Jfe\n33Lz0pmZ1CfbdnlQNVbcndMf8VRRaGTm3cW/ERN34vM5qYtM2pgcL7DokdDIpu+P\nnCNsdOh3Je1XWdfrKIhaBXZIH7TTYWkRsYXQ0CI4TDrktz0V7Fz971T7PJAj+hiU\nxNOPaIBf7hA/SNm05DB3R1hdoHtVF7kEfKZqsSFIc7gH0rXY22jlfq17/YDID2IJ\nnz2BbsBJiBCEGe+RPxwa12wm8uimBctqQT8z9JV2hYzvdhtDiVSkGWa6Lak83nCQ\n3auQG3X9447GdYDMtzlSga9015B0nmLhfiKZQt80rQKBgQD2voZQqrmA8DfQlw8o\nn/dEdMJMQuf8W7Oy5ZrveUJ+9fIQ50X55HW67042vGQQZEM2AL5/DIt++cr+m2zi\noZlgEalj2YPykY6CLcBt0I/iN1j8DdsPDerUE0grKtncC6GCD+5of1MuRbx69GGN\nMUeyJ33Jw92BafbWNiNhWeRYuwKBgQC+XUMRaRcDCB004INdmvFEihPDRK/WGn08\n8BndltNSaRIUnxVp7KLx2PP4sAwJ6ylZTxqGQOJ23csgQDsfs0bw/3k+2rW1Ub8i\nx8hnS0RKkxdShZZb4Al4wRfr4jKJqsPyZpmuK5pleGro9TY+tNcJWEsj4EJRxe0c\nCO4WqqZqZQKBgCRv8knLTGWcE8H77MMlDFDRpTe50aRUrm7GtWCT2ZwCGeMhJBZJ\nBJG8cSJoI6bAB6Tb60W7xoXTwYRj02qMTqf/M7KJFpElqZPTyczttbHEVqGyMh1B\nAuKajlfBljaGiS05yQ0pcFEu/yxxFk7RbjMC3fKDuBw6V7c+e28O5UetAoGADzY6\npsiECzz5wID0XmWERBrYi3EQsAY73cO9/WQRDPPSew1fU7CSMMtKa6P9wkkla7qT\nfwjuT9tXYQNg9h6IW7e+g5RMkumuYWQfkomEMoVghrqgEkVr3FdpxvKzYSbhM5yZ\nST64vsUJngYCSK6AxIFmt74y7n/ne6cHB46pb7UCgYEAx9cpy1uGvx+CxPvGKjV7\nfPTQ9Q8p37uNn3imR8tU8N5hxaLFZvuiUgakPXiFXcq6b89AEFpeYcbpVfW3gSaH\nj4JVp7lRwS90Q2RcfOynQJwle8c7uikoCHIQR+jiGDLsNoBiAIfyWDgmVT7mmDbw\nLoFAHSD//D0Q1g4aoRyzWAw=\n-----END PRIVATE KEY-----\n",
            "client_email": "firebase-adminsdk-amvs1@useful-tools-api.iam.gserviceaccount.com",
            "client_id": "113481818478502306669",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-amvs1%40useful-tools-api.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com",
        }

        # Obsidian notes directory
        self.notes_directory = Path("C:/Notes")

        # Initialize Firebase and console
        self.console = Console()
        self.storage_client = None
        self.bucket = None

    def create_header(self):
        """Create beautiful header with system information"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create header table
        header_table = Table.grid(padding=1)
        header_table.add_column(justify="left")
        header_table.add_column(justify="center")
        header_table.add_column(justify="right")

        header_table.add_row(
            f"[bold cyan]📝 Obsidian Notes Uploader v1.0[/bold cyan]",
            f"[bold yellow]🔥 Firebase Storage Integration[/bold yellow]",
            f"[dim]{current_time}[/dim]",
        )

        header_table.add_row(
            f"[dim]📁 Source: {self.notes_directory}[/dim]",
            "",
            f"[dim]PID: {os.getpid()}[/dim]",
        )

        return Panel(header_table, style="bright_blue", padding=(0, 1))

    def create_status_panel(self, status_text, status_type="info"):
        """Create beautiful status panel"""
        colors = {
            "info": "blue",
            "success": "green",
            "error": "red",
            "warning": "yellow",
            "processing": "magenta",
        }

        icons = {
            "info": "ℹ️",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "processing": "⚡",
        }

        color = colors.get(status_type, "white")
        icon = icons.get(status_type, "•")

        return Panel(
            f"{icon} {status_text}",
            style=color,
            padding=(0, 1),
            title=f"[bold]{status_type.upper()}[/bold]",
        )

    def create_notes_info_panel(self):
        """Create panel showing notes directory information"""
        if not self.notes_directory.exists():
            return Panel(
                f"[bold red]❌ Directory not found: {self.notes_directory}[/bold red]",
                style="red",
                title="[bold red]ERROR[/bold red]",
                padding=(1, 2),
            )

        # Count files and get directory size
        total_files = 0
        total_size = 0
        md_files = 0

        for file_path in self.notes_directory.rglob("*"):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size
                if file_path.suffix.lower() == ".md":
                    md_files += 1

        # Format size
        size_str = self.format_file_size(total_size)

        info_table = Table.grid(padding=1)
        info_table.add_column(justify="left")
        info_table.add_column(justify="right")

        info_table.add_row("📁 Directory:", f"[cyan]{self.notes_directory}[/cyan]")
        info_table.add_row("📄 Total Files:", f"[yellow]{total_files:,}[/yellow]")
        info_table.add_row("📝 Markdown Files:", f"[green]{md_files:,}[/green]")
        info_table.add_row("💾 Total Size:", f"[magenta]{size_str}[/magenta]")
        info_table.add_row(
            "🕒 Last Modified:",
            f"[dim]{datetime.fromtimestamp(self.notes_directory.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
        )

        return Panel(
            info_table,
            title="[bold green]📊 Obsidian Notes Information[/bold green]",
            style="green",
            padding=(1, 2),
        )

    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f} {size_names[i]}"

    def init_firebase(self):
        """Initialize Firebase connection with hardcoded credentials"""
        try:
            # Check if Firebase app is already initialized
            if not firebase_admin._apps:
                # Use hardcoded credentials
                cred = credentials.Certificate(self.SERVICE_ACCOUNT_CREDENTIALS)
                firebase_admin.initialize_app(
                    cred, {"storageBucket": self.STORAGE_BUCKET}
                )
                self.console.print(
                    self.create_status_panel(
                        "Firebase initialized with hardcoded credentials", "success"
                    )
                )

            # Initialize Google Cloud Storage client
            from google.oauth2 import service_account

            gcs_credentials = service_account.Credentials.from_service_account_info(
                self.SERVICE_ACCOUNT_CREDENTIALS
            )

            self.storage_client = gcs.Client(
                project=self.PROJECT_ID, credentials=gcs_credentials
            )

            # Get bucket with fallback for different naming conventions
            bucket_name = self.STORAGE_BUCKET.replace("gs://", "")

            try:
                self.bucket = self.storage_client.bucket(bucket_name)
                # Test bucket access
                list(self.bucket.list_blobs(max_results=1))
                self.console.print(
                    self.create_status_panel(
                        f"Connected to bucket: {bucket_name}", "success"
                    )
                )
            except Exception as e:
                # Fallback to .appspot.com format
                bucket_name_appspot = bucket_name.replace(
                    ".firebasestorage.app", ".appspot.com"
                )
                self.bucket = self.storage_client.bucket(bucket_name_appspot)
                list(self.bucket.list_blobs(max_results=1))
                self.console.print(
                    self.create_status_panel(
                        f"Connected to bucket: {bucket_name_appspot}", "success"
                    )
                )

            return True

        except Exception as e:
            self.console.print(
                self.create_status_panel(
                    f"Firebase initialization failed: {e}", "error"
                )
            )
            return False

    def create_zip_file(self, output_path):
        """Create zip file of Obsidian notes with progress tracking"""
        if not self.notes_directory.exists():
            raise FileNotFoundError(
                f"Notes directory not found: {self.notes_directory}"
            )

        # Count total files for progress tracking
        all_files = list(self.notes_directory.rglob("*"))
        files_to_zip = [f for f in all_files if f.is_file()]
        total_files = len(files_to_zip)

        self.console.print(
            self.create_status_panel(f"Found {total_files:,} files to zip", "info")
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:

            zip_task = progress.add_task("Creating zip file...", total=total_files)

            with zipfile.ZipFile(
                output_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6
            ) as zipf:
                for i, file_path in enumerate(files_to_zip):
                    try:
                        # Create archive name relative to notes directory
                        arcname = file_path.relative_to(self.notes_directory)
                        # Convert Windows path separators to forward slashes
                        arcname = str(arcname).replace(os.sep, "/")

                        zipf.write(file_path, arcname)

                        # Update progress
                        progress.update(
                            zip_task,
                            advance=1,
                            description=f"Zipping: {file_path.name}",
                        )

                    except Exception as e:
                        self.console.print(
                            self.create_status_panel(
                                f"Warning: Could not zip {file_path.name}: {e}",
                                "warning",
                            )
                        )
                        continue

        # Get final zip file size
        zip_size = Path(output_path).stat().st_size
        self.console.print(
            self.create_status_panel(
                f"Zip file created: {self.format_file_size(zip_size)}", "success"
            )
        )

        return zip_size

    def upload_to_firebase(self, zip_path, remote_filename):
        """Upload zip file to Firebase Storage with progress tracking"""
        try:
            zip_size = Path(zip_path).stat().st_size

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                console=self.console,
            ) as progress:

                upload_task = progress.add_task(
                    "Uploading to Firebase Storage...", total=100
                )

                # Create blob and upload
                blob = self.bucket.blob(remote_filename)

                progress.update(
                    upload_task, advance=20, description="Initiating upload..."
                )

                # Upload file
                blob.upload_from_filename(zip_path)

                progress.update(
                    upload_task,
                    advance=60,
                    description="Upload completed, verifying...",
                )

                # Verify upload
                if blob.exists():
                    progress.update(
                        upload_task, advance=20, description="Upload verified!"
                    )
                    return True, (
                        blob.public_url
                        if hasattr(blob, "public_url")
                        else f"gs://{self.bucket.name}/{remote_filename}"
                    )
                else:
                    return False, "Upload verification failed"

        except Exception as e:
            return False, str(e)

    def create_upload_summary(self, zip_size, upload_time, remote_url):
        """Create beautiful upload summary panel"""
        summary_table = Table.grid(padding=1)
        summary_table.add_column(justify="left")
        summary_table.add_column(justify="right")

        summary_table.add_row(
            "📦 Zip File Size:",
            f"[bold green]{self.format_file_size(zip_size)}[/bold green]",
        )
        summary_table.add_row(
            "⚡ Upload Time:", f"[yellow]{upload_time:.1f} seconds[/yellow]"
        )
        summary_table.add_row("🔗 Firebase URL:", f"[cyan]{remote_url}[/cyan]")
        summary_table.add_row(
            "📅 Timestamp:",
            f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
        )
        summary_table.add_row("🎯 Status:", f"[bold green]✅ SUCCESS[/bold green]")

        return Panel(
            summary_table,
            title="[bold green]🎉 Upload Complete![/bold green]",
            style="green",
            padding=(1, 2),
        )

    def run(self):
        """Main execution flow with beautiful CLI interface"""
        # Clear screen and show header
        self.console.clear()
        self.console.print(self.create_header())
        self.console.print()

        # Show notes directory information
        self.console.print(self.create_notes_info_panel())
        self.console.print()

        # Check if notes directory exists
        if not self.notes_directory.exists():
            self.console.print(
                self.create_status_panel("Notes directory not found. Exiting.", "error")
            )
            return

        # Initialize Firebase
        self.console.print(
            self.create_status_panel(
                "Initializing Firebase connection...", "processing"
            )
        )
        if not self.init_firebase():
            self.console.print(
                self.create_status_panel(
                    "Failed to initialize Firebase. Exiting.", "error"
                )
            )
            return

        self.console.print()

        # Confirm upload
        self.console.print(
            self.create_status_panel("Ready to zip and upload Obsidian notes", "info")
        )
        try:
            confirm = (
                input(f"{Fore.CYAN}❯ Continue with upload? (y/N): {Style.RESET_ALL}")
                .strip()
                .lower()
            )
            if confirm not in ["y", "yes"]:
                self.console.print(
                    self.create_status_panel("Upload cancelled by user", "warning")
                )
                return
        except KeyboardInterrupt:
            self.console.print(
                self.create_status_panel("\nUpload cancelled by user", "warning")
            )
            return

        self.console.print()

        # Use fixed filename
        zip_filename = "Notes.zip"

        try:
            # Create temporary zip file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
                temp_zip_path = temp_zip.name

            # Create zip file
            self.console.print(
                self.create_status_panel("Creating zip file...", "processing")
            )
            start_time = time.time()
            zip_size = self.create_zip_file(temp_zip_path)

            # Upload to Firebase
            self.console.print(
                self.create_status_panel(
                    "Uploading to Firebase Storage...", "processing"
                )
            )
            success, result = self.upload_to_firebase(temp_zip_path, zip_filename)
            end_time = time.time()

            upload_time = end_time - start_time

            if success:
                # Show success summary
                self.console.print()
                self.console.print(
                    self.create_upload_summary(zip_size, upload_time, result)
                )
            else:
                self.console.print(
                    self.create_status_panel(f"Upload failed: {result}", "error")
                )

        except Exception as e:
            self.console.print(
                self.create_status_panel(f"Operation failed: {e}", "error")
            )

        finally:
            # Clean up temporary file
            try:
                if "temp_zip_path" in locals():
                    os.unlink(temp_zip_path)
            except:
                pass

        self.console.print()
        self.console.print(self.create_status_panel("Press Enter to exit...", "info"))
        input()


def main():
    """Main function to run the Obsidian Notes Uploader"""
    try:
        uploader = ObsidianNotesUploader()
        uploader.run()
    except KeyboardInterrupt:
        console = Console()
        console.print(Panel("👋 Goodbye!", style="yellow", padding=(0, 1)))
    except Exception as e:
        console = Console()
        console.print(
            Panel(
                f"❌ Application error: {e}",
                style="red",
                title="[bold red]ERROR[/bold red]",
                padding=(1, 2),
            )
        )


if __name__ == "__main__":
    main()
