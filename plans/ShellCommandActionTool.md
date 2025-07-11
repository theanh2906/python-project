- A GUI to execute shell commands by button clicks
- This tool monitors the output of the command and displays it in a text area.
- When the command is being executed, the button is disabled. When the command finishes, the button is enabled again.
- The tool should be written in Python using Tkinter, customtkinter.
- The tool should have a text area to display the output of the command.
- Define a dictionary to define the commands and their descriptions with structure:
```json
[
  {
    "name": "Command Name",
    "description": "Description of the command",
    "command": "Actual shell command to execute"
  }
]
```
In the above example, the description will be displayed as a tooltip when hovering over the button. The name is the text on the button, and the command is the actual shell command to execute when the button is clicked.
- The GUI will render a button for each command defined in the dictionary. Take care the button size and layout.
- The execution shell should be PowerShell. But it should be possible to change it to another shell using a switch button.