# Shell Command Action Tool

A GUI application that allows you to execute shell commands with a simple button click. This tool was implemented based on the specifications in `plans/ShellCommandActionTool.md`.

## Features

- Execute shell commands by clicking buttons
- Monitor command output in real-time
- Disable buttons during command execution
- Switch between PowerShell and CMD
- Tooltips for command descriptions

## Usage

1. Run the application:
   ```
   python shell_command_action_tool.py
   ```
   or
   ```
   .venv\Scripts\python.exe shell_command_action_tool.py
   ```

2. The GUI will display buttons for each predefined command.

3. Hover over a button to see a tooltip with the command description.

4. Click a button to execute the corresponding command. The button will be disabled during execution.

5. The command output will be displayed in the text area.

6. Use the "Use CMD" switch to toggle between PowerShell and CMD.

## Customizing Commands

To add or modify commands, edit the `commands` list in the `ShellCommandActionTool` class:

```python
self.commands = [
    {
        "name": "Command Name",
        "description": "Description of the command",
        "command": "Actual shell command to execute"
    },
    # Add more commands here
]
```

Each command requires:
- `name`: The text displayed on the button
- `description`: The tooltip text shown when hovering over the button
- `command`: The actual shell command to execute

## Implementation Details

The tool is built using:
- customtkinter: For the modern UI components
- tkinter: For basic UI functionality
- subprocess: For executing shell commands
- threading: For running commands in the background

The main components of the application are:
1. `ShellCommandActionTool` class: The main application window
2. `ToolTip` class: Handles the tooltip functionality
3. Command execution logic: Runs commands in a separate thread to keep the UI responsive

## Requirements

- Python 3.8 or higher
- customtkinter 5.2.2 or higher
- tkinter (included with Python)