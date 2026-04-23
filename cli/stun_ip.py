#!/usr/bin/env python3
"""
STUN Client - Enhanced TUI to get public IP behind NAT (htop-style)
Implements STUN (Session Traversal Utilities for NAT) protocol
RFC 5389 compliant binding request
"""

import socket
import struct
import random
import time
import os
import platform
from datetime import datetime
from colorama import Fore, Back, Style, init
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.live import Live

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class StunClient:
    """Simple STUN client for NAT binding requests"""
    
    # STUN message types
    BINDING_REQUEST = 0x0001
    BINDING_RESPONSE = 0x0101
    
    # STUN attributes
    MAPPED_ADDRESS = 0x0001
    XOR_MAPPED_ADDRESS = 0x0020
    
    # STUN magic cookie (RFC 5389)
    MAGIC_COOKIE = 0x2112A442
    
    def __init__(self):
        self.transaction_id = None
        
    def generate_transaction_id(self):
        """Generate a random 96-bit transaction ID"""
        return struct.pack('!12s', bytes([random.randint(0, 255) for _ in range(12)]))
    
    def create_binding_request(self):
        """Create a STUN binding request packet"""
        self.transaction_id = self.generate_transaction_id()
        
        # STUN header: Type (2 bytes) + Length (2 bytes) + Magic Cookie (4 bytes) + Transaction ID (12 bytes)
        message_type = self.BINDING_REQUEST
        message_length = 0  # No attributes for basic binding request
        
        header = struct.pack('!HH', message_type, message_length)
        header += struct.pack('!L', self.MAGIC_COOKIE)
        header += self.transaction_id
        
        return header
    
    def parse_stun_response(self, response):
        """Parse STUN binding response to extract mapped address"""
        if len(response) < 20:
            return None, "Response too short"
            
        # Parse header
        message_type, message_length, magic_cookie = struct.unpack('!HHL', response[:8])
        transaction_id = response[8:20]
        
        if magic_cookie != self.MAGIC_COOKIE:
            return None, "Invalid magic cookie"
            
        if transaction_id != self.transaction_id:
            return None, "Transaction ID mismatch"
            
        if message_type != self.BINDING_RESPONSE:
            return None, f"Unexpected message type: {message_type:04x}"
        
        # Parse attributes
        offset = 20
        while offset < len(response):
            if offset + 4 > len(response):
                break
                
            attr_type, attr_length = struct.unpack('!HH', response[offset:offset+4])
            offset += 4
            
            if offset + attr_length > len(response):
                break
                
            attr_data = response[offset:offset+attr_length]
            
            if attr_type == self.MAPPED_ADDRESS:
                return self.parse_mapped_address(attr_data), None
            elif attr_type == self.XOR_MAPPED_ADDRESS:
                return self.parse_xor_mapped_address(attr_data), None
                
            # Move to next attribute (with padding)
            offset += attr_length
            # Attributes are padded to 4-byte boundary
            offset = (offset + 3) & ~3
            
        return None, "No mapped address found"
    
    def parse_mapped_address(self, data):
        """Parse MAPPED-ADDRESS attribute"""
        if len(data) < 8:
            return None
            
        _, family, port = struct.unpack('!BBH', data[:4])
        
        if family == 1:  # IPv4
            ip_bytes = struct.unpack('!BBBB', data[4:8])
            ip = '.'.join(str(b) for b in ip_bytes)
            return f"{ip}:{port}"
        
        return None
    
    def parse_xor_mapped_address(self, data):
        """Parse XOR-MAPPED-ADDRESS attribute"""
        if len(data) < 8:
            return None
            
        _, family, port = struct.unpack('!BBH', data[:4])
        
        # XOR the port with the most significant 16 bits of magic cookie
        port ^= (self.MAGIC_COOKIE >> 16) & 0xFFFF
        
        if family == 1:  # IPv4
            ip_int = struct.unpack('!L', data[4:8])[0]
            # XOR the IP with magic cookie
            ip_int ^= self.MAGIC_COOKIE
            
            ip_bytes = [
                (ip_int >> 24) & 0xFF,
                (ip_int >> 16) & 0xFF,
                (ip_int >> 8) & 0xFF,
                ip_int & 0xFF
            ]
            ip = '.'.join(str(b) for b in ip_bytes)
            return f"{ip}:{port}"
        
        return None
    
    def query_stun_server(self, server_host, server_port=3478, timeout=5):
        """Send STUN binding request to server and get response"""
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            
            # Create and send binding request
            request = self.create_binding_request()
            sock.sendto(request, (server_host, server_port))
            
            # Receive response
            response, addr = sock.recvfrom(1024)
            sock.close()
            
            return self.parse_stun_response(response)
            
        except socket.timeout:
            return None, "Request timed out"
        except socket.gaierror as e:
            return None, f"DNS resolution failed: {e}"
        except Exception as e:
            return None, f"Network error: {e}"


def create_header():
    """Create htop-style header with system information"""
    console = Console()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    system_info = f"{platform.system()} {platform.release()}"
    
    # Create header table
    header_table = Table.grid(padding=1)
    header_table.add_column(justify="left")
    header_table.add_column(justify="center")
    header_table.add_column(justify="right")
    
    header_table.add_row(
        f"[bold cyan]STUN Client v1.0[/bold cyan]",
        f"[bold yellow]NAT Public IP Discovery Tool[/bold yellow]",
        f"[dim]{current_time}[/dim]"
    )
    
    header_table.add_row(
        f"[dim]System: {system_info}[/dim]",
        "",
        f"[dim]PID: {os.getpid()}[/dim]"
    )
    
    return Panel(header_table, style="bright_blue", padding=(0, 1))


def create_server_table(stun_servers, highlight_index=None):
    """Create htop-style server selection table"""
    table = Table(title="[bold green]Available STUN Servers[/bold green]", 
                  show_header=True, header_style="bold magenta")
    
    table.add_column("#", style="cyan", width=3)
    table.add_column("Server", style="white")
    table.add_column("Port", style="yellow", width=8)
    table.add_column("Status", style="green", width=10)
    
    for i, (server, port) in enumerate(stun_servers, 1):
        status = "🟢 Active" if i <= 4 else "🟡 Backup"
        style = "bold white on blue" if highlight_index == i else ""
        
        table.add_row(
            str(i),
            server,
            str(port),
            status,
            style=style
        )
    
    table.add_row(
        str(len(stun_servers) + 1),
        "[italic]Custom Server[/italic]",
        "[dim]varies[/dim]",
        "⚙️ Manual",
        style="bold white on blue" if highlight_index == len(stun_servers) + 1 else ""
    )
    
    return table


def create_status_panel(status_text, status_type="info"):
    """Create htop-style status panel"""
    colors = {
        "info": "blue",
        "success": "green", 
        "error": "red",
        "warning": "yellow",
        "processing": "magenta"
    }
    
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "error": "❌", 
        "warning": "⚠️",
        "processing": "⚡"
    }
    
    color = colors.get(status_type, "white")
    icon = icons.get(status_type, "•")
    
    return Panel(
        f"{icon} {status_text}",
        style=color,
        padding=(0, 1),
        title=f"[bold]{status_type.upper()}[/bold]"
    )


def main():
    """Enhanced htop-style main TUI function"""
    console = Console()
    
    # Clear screen and show header
    console.clear()
    console.print(create_header())
    
    # List of well-known STUN servers
    stun_servers = [
        ("stun.l.google.com", 19302),
        ("stun1.l.google.com", 19302),
        ("stun2.l.google.com", 19302),
        ("stun.stunprotocol.org", 3478),
        ("stun.ekiga.net", 3478),
        ("stun.voiparound.com", 3478),
        ("stun.voipbuster.com", 3478),
    ]
    
    # Show server selection table
    console.print(create_server_table(stun_servers))
    console.print()
    
    # Server selection loop
    while True:
        try:
            console.print(create_status_panel(
                f"Select server (1-{len(stun_servers) + 1}) or 'q' to quit",
                "info"
            ))
            
            choice = input(f"{Fore.CYAN}❯ {Style.RESET_ALL}").strip()
            
            if choice.lower() == 'q':
                console.print(create_status_panel("Goodbye! 👋", "info"))
                return
                
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(stun_servers):
                server_host, server_port = stun_servers[choice_num - 1]
                console.clear()
                console.print(create_header())
                console.print(create_server_table(stun_servers, choice_num))
                break
            elif choice_num == len(stun_servers) + 1:
                console.print(create_status_panel("Enter custom server details", "info"))
                server_input = input(f"{Fore.CYAN}Server (host:port or just host): {Style.RESET_ALL}").strip()
                if ':' in server_input:
                    server_host, port_str = server_input.rsplit(':', 1)
                    server_port = int(port_str)
                else:
                    server_host = server_input
                    server_port = 3478
                console.clear()
                console.print(create_header())
                break
            else:
                console.print(create_status_panel("Invalid choice. Please try again.", "error"))
                
        except ValueError:
            console.print(create_status_panel("Invalid input. Please enter a number or 'q'", "error"))
        except KeyboardInterrupt:
            console.print(create_status_panel("\nGoodbye! 👋", "info"))
            return
    
    # Query STUN server with progress bar
    console.print(create_status_panel(f"Connecting to {server_host}:{server_port}", "processing"))
    
    client = StunClient()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Querying STUN server...", total=100)
        
        start_time = time.time()
        
        # Simulate progress steps
        progress.update(task, advance=20, description="Creating UDP socket...")
        time.sleep(0.1)
        
        progress.update(task, advance=30, description="Sending binding request...")
        mapped_address, error = client.query_stun_server(server_host, server_port)
        
        progress.update(task, advance=30, description="Processing response...")
        time.sleep(0.1)
        
        progress.update(task, advance=20, description="Complete!")
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
    
    console.print()
    
    # Display results in htop-style panels
    if mapped_address:
        # Success panel
        result_table = Table.grid(padding=1)
        result_table.add_column(justify="left")
        result_table.add_column(justify="right")
        
        result_table.add_row("🌐 Public IP & Port:", f"[bold green]{mapped_address}[/bold green]")
        result_table.add_row("⚡ Response Time:", f"[yellow]{response_time:.1f} ms[/yellow]")
        result_table.add_row("🔗 STUN Server:", f"[cyan]{server_host}:{server_port}[/cyan]")
        result_table.add_row("📅 Timestamp:", f"[dim]{datetime.now().strftime('%H:%M:%S')}[/dim]")
        
        console.print(Panel(
            result_table,
            title="[bold green]✅ SUCCESS - NAT Binding Result[/bold green]",
            style="green",
            padding=(1, 2)
        ))
    else:
        # Error panel
        error_table = Table.grid(padding=1)
        error_table.add_column(justify="left")
        error_table.add_column(justify="right")
        
        error_table.add_row("❌ Error:", f"[bold red]{error}[/bold red]")
        error_table.add_row("🔗 Server:", f"[cyan]{server_host}:{server_port}[/cyan]")
        error_table.add_row("⏱️ Timeout:", f"[yellow]{response_time:.1f} ms[/yellow]")
        
        console.print(Panel(
            error_table,
            title="[bold red]❌ FAILED - Connection Error[/bold red]",
            style="red",
            padding=(1, 2)
        ))
    
    console.print()
    console.print(create_status_panel("Press Enter to continue...", "info"))
    input()


if __name__ == "__main__":
    main()