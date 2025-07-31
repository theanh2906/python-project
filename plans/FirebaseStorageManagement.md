# Python GUI Tool for Firebase Storage Management

Create a Python application with a graphical user interface (GUI) for managing Firebase Storage. The tool should be intuitive, visually appealing, and user-friendly, with modern UI/UX design principles. Use a suitable GUI framework (e.g., Tkinter with customtkinter, PyQt, or Kivy) to ensure an attractive and responsive interface. Below are the detailed requirements:

## Core Features
1. **File and Folder Display**:
   - Display all files and folders stored in Firebase Storage.
   - If possible, implement a tree view to represent the folder structure hierarchically (e.g., expandable/collapsible nodes for folders and subfolders).
   - Show relevant file details (e.g., name, size, last modified date) in a clean, tabular, or grid format.

2. **File/Folder Upload**:
   - Allow users to upload individual files or entire folders to Firebase Storage.
   - Provide a file/folder picker dialog for easy selection.
   - Display a progress bar or loading indicator during uploads.

3. **File/Folder Removal**:
   - Enable deletion of single or multiple files/folders.
   - Implement a confirmation dialog requiring the user to input a predefined PIN to prevent accidental deletions.
   - Show a loading state during deletion and handle errors gracefully (e.g., display error messages if deletion fails).

4. **Refresh Button**:
   - Include a button to refresh the list of files and folders from Firebase Storage.
   - Ensure the refresh action updates the UI instantly and displays a loading indicator during the process.

## Advanced Feature: Zip and Upload
- Provide an option to zip selected files or folders before uploading to Firebase Storage:
  - **Folder Zipping**: If a folder is selected, zip all its child files and folders. Name the zip file after the parent folder (e.g., `folder_name.zip`).
  - **File Zipping**: If multiple files are selected, zip them together. Name the zip file after their parent folder if they share one; otherwise, use a default name format: `{device_name}-{timestamp}.zip` (e.g., `MyPC-20250731123045.zip`).
  - Display a progress indicator during zipping and uploading.
  - Ensure the zip file is uploaded to Firebase Storage in the same directory as the original files/folders.

## Firebase Configuration
- Hardcode the Firebase configuration (e.g., API key, project ID, storage bucket) within the code.
- Ensure secure handling of credentials and proper initialization of the Firebase Storage client using the `pyrebase` or `firebase-admin` Python library.

## UI/UX Requirements
- Design a modern, visually appealing interface with a clean layout, consistent color scheme, and readable typography.
- Use animations or transitions for loading states to enhance user experience.
- Ensure the GUI is responsive and works well on different screen sizes.
- Implement clear visual feedback for user actions (e.g., button hover effects, success/error notifications).
- Handle loading and disabled states for buttons and UI elements during actions (e.g., upload, delete, refresh) to prevent multiple clicks and provide feedback.

## Error Handling and Accessibility
- Handle errors gracefully (e.g., network issues, invalid PIN, Firebase authentication errors) with user-friendly error messages.
- Disable buttons or show loading indicators during ongoing operations (e.g., uploading, deleting, refreshing).
- Ensure accessibility by supporting keyboard navigation and providing text descriptions for UI elements (e.g., tooltips, labels).

## Technical Requirements
- Use Python 3.x and a suitable GUI framework (recommend `customtkinter` for modern Tkinter styling or PyQt for advanced UI capabilities).
- Use `pyrebase` or `firebase-admin` for Firebase Storage integration.
- Ensure the code is well-structured, modular, and commented for maintainability.
- Avoid external file dependencies (e.g., images, config files) to keep the tool self-contained.
- Test the application to ensure it handles edge cases (e.g., empty folders, large files, network interruptions).

## Deliverables
- Provide the complete Python source code for the application.
- Include inline comments explaining key sections of the code.
- Ensure the code is executable with minimal setup (e.g., list required pip packages).