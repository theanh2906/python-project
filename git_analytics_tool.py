import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from collections import defaultdict
import re
import threading

class GitAnalyticsTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Git Analytics Tool")
        self.root.geometry("1200x800")

        # Set up the main frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Repository selection frame
        self.repo_frame = ctk.CTkFrame(self.main_frame)
        self.repo_frame.pack(fill=tk.X, padx=10, pady=10)

        self.repo_label = ctk.CTkLabel(self.repo_frame, text="Git Repository:")
        self.repo_label.pack(side=tk.LEFT, padx=5)

        self.repo_path = ctk.CTkEntry(self.repo_frame, width=400)
        self.repo_path.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.browse_button = ctk.CTkButton(self.repo_frame, text="Browse", command=self.browse_repository)
        self.browse_button.pack(side=tk.LEFT, padx=5)

        self.analyze_button = ctk.CTkButton(self.repo_frame, text="Analyze", command=self.analyze_repository)
        self.analyze_button.pack(side=tk.LEFT, padx=5)

        # Tabs for different visualizations
        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.tab_commits_by_author = self.tab_view.add("Commits by Author")
        self.tab_lines_by_author = self.tab_view.add("Lines by Author")
        self.tab_commits_by_time = self.tab_view.add("Commits by Time")
        self.tab_percentage_commits = self.tab_view.add("Percentage of Commits")
        self.tab_percentage_contributors = self.tab_view.add("Percentage of Contributors")

        # Initialize plot frames in each tab
        self.frames = {
            "commits_by_author": ctk.CTkFrame(self.tab_commits_by_author),
            "lines_by_author": ctk.CTkFrame(self.tab_lines_by_author),
            "commits_by_time": ctk.CTkFrame(self.tab_commits_by_time),
            "percentage_commits": ctk.CTkFrame(self.tab_percentage_commits),
            "percentage_contributors": ctk.CTkFrame(self.tab_percentage_contributors)
        }

        for frame in self.frames.values():
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Time period selection for commits by time
        self.time_frame = ctk.CTkFrame(self.tab_commits_by_time)
        self.time_frame.pack(fill=tk.X, padx=10, pady=5)

        self.time_period_var = tk.StringVar(value="month")

        self.day_radio = ctk.CTkRadioButton(self.time_frame, text="Day", variable=self.time_period_var, value="day")
        self.day_radio.pack(side=tk.LEFT, padx=10)

        self.week_radio = ctk.CTkRadioButton(self.time_frame, text="Week", variable=self.time_period_var, value="week")
        self.week_radio.pack(side=tk.LEFT, padx=10)

        self.month_radio = ctk.CTkRadioButton(self.time_frame, text="Month", variable=self.time_period_var, value="month")
        self.month_radio.pack(side=tk.LEFT, padx=10)

        self.update_time_button = ctk.CTkButton(self.time_frame, text="Update", command=self.update_time_graph)
        self.update_time_button.pack(side=tk.LEFT, padx=10)

        # Store canvas objects
        self.canvases = {}

        # Store git data
        self.git_data = None

        # Loading indicator
        self.loading_frame = ctk.CTkFrame(self.main_frame)
        self.loading_frame.pack(fill=tk.X, padx=10, pady=5)
        self.loading_frame.pack_forget()  # Hide initially

        self.loading_label = ctk.CTkLabel(self.loading_frame, text="Analyzing repository... Please wait")
        self.loading_label.pack(side=tk.LEFT, padx=10, pady=5)

        self.loading_progress = ctk.CTkProgressBar(self.loading_frame, width=400)
        self.loading_progress.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)
        self.loading_progress.set(0)  # Start at 0

    def browse_repository(self):
        repo_path = filedialog.askdirectory(title="Select Git Repository")
        if repo_path:
            self.repo_path.delete(0, tk.END)
            self.repo_path.insert(0, repo_path)
            if self.validate_repository(repo_path):
                # Call analyze_repository which will handle showing the loading indicator
                self.analyze_repository()

    def validate_repository(self, repo_path):
        # Check if it's a valid Git repository
        if not os.path.exists(os.path.join(repo_path, ".git")):
            messagebox.showerror("Invalid Repository", "The selected directory is not a valid Git repository.")
            return False
        return True

    def analyze_repository(self):
        repo_path = self.repo_path.get()
        if not repo_path:
            messagebox.showwarning("No Repository", "Please select a Git repository first.")
            return

        if not self.validate_repository(repo_path):
            return

        # Show loading indicator
        self.show_loading_indicator()

        # Disable analyze button during analysis
        self.analyze_button.configure(state="disabled")

        # Start analysis in a separate thread
        analysis_thread = threading.Thread(target=self.analyze_repository_thread, args=(repo_path,))
        analysis_thread.daemon = True  # Thread will exit when main program exits
        analysis_thread.start()

    def show_loading_indicator(self):
        # Show loading frame
        self.loading_frame.pack(fill=tk.X, padx=10, pady=5, after=self.repo_frame)
        self.loading_label.configure(text="Initializing analysis...")
        self.loading_progress.set(0)
        self.loading_progress.configure(mode="determinate")  # Set to determinate mode for precise progress
        self.root.update()  # Force update of the UI

    def hide_loading_indicator(self):
        # Hide loading frame
        self.loading_frame.pack_forget()
        # Re-enable analyze button
        self.analyze_button.configure(state="normal")
        self.root.update()  # Force update of the UI

    def analyze_repository_thread(self, repo_path):
        try:
            # Update loading label for git data extraction
            self.root.after(0, lambda: self.loading_label.configure(text="Extracting git data... This may take a while"))

            # Extract git data
            self.git_data = self.extract_git_data(repo_path)

            # Use after method to update UI from the main thread
            self.root.after(0, self.update_loading_progress, 0.2)

            # Create visualizations (in the main thread)
            self.root.after(0, self.create_visualizations)

        except Exception as e:
            # Show error in the main thread
            self.root.after(0, lambda: messagebox.showerror("Analysis Error", f"An error occurred during analysis: {str(e)}"))
            # Hide loading indicator in the main thread
            self.root.after(0, self.hide_loading_indicator)

    def update_loading_progress(self, progress):
        self.loading_progress.set(progress)
        self.root.update()

    def create_visualizations(self):
        try:
            # Create visualizations with progress updates
            self.update_loading_progress(0.2)
            self.loading_label.configure(text="Creating commits by author graph...")
            self.create_commits_by_author_graph()

            self.update_loading_progress(0.4)
            self.loading_label.configure(text="Creating lines by author graph...")
            self.create_lines_by_author_graph()

            self.update_loading_progress(0.6)
            self.loading_label.configure(text="Creating commits by time graph...")
            self.create_commits_by_time_graph()

            self.update_loading_progress(0.8)
            self.loading_label.configure(text="Creating percentage of commits graph...")
            self.create_percentage_commits_graph()

            self.update_loading_progress(1.0)
            self.loading_label.configure(text="Creating percentage of contributors graph...")
            self.create_percentage_contributors_graph()

            # Hide loading indicator
            self.hide_loading_indicator()

            # Show success message
            messagebox.showinfo("Analysis Complete", "Git repository analysis completed successfully.")
        except Exception as e:
            messagebox.showerror("Visualization Error", f"An error occurred during visualization: {str(e)}")
            self.hide_loading_indicator()

    def extract_git_data(self, repo_path):
        # Change to the repository directory
        original_dir = os.getcwd()
        os.chdir(repo_path)

        try:
            # Get all commits data
            git_log_cmd = [
                'git', 'log', '--pretty=format:%H|%an|%at', '--numstat'
            ]
            git_log_output = subprocess.check_output(git_log_cmd, universal_newlines=True)

            # Parse the git log output
            commits = []
            current_commit = None

            for line in git_log_output.split('\n'):
                if '|' in line:  # This is a commit header
                    if current_commit:
                        commits.append(current_commit)

                    commit_hash, author, timestamp = line.split('|')
                    timestamp = int(timestamp)
                    date = datetime.fromtimestamp(timestamp)

                    current_commit = {
                        'hash': commit_hash,
                        'author': author,
                        'timestamp': timestamp,
                        'date': date,
                        'files': [],
                        'additions': 0,
                        'deletions': 0
                    }
                elif line.strip() and current_commit:  # This is a file stat line
                    parts = line.split('\t')
                    if len(parts) == 3:
                        try:
                            additions = int(parts[0]) if parts[0] != '-' else 0
                            deletions = int(parts[1]) if parts[1] != '-' else 0
                            filename = parts[2]

                            current_commit['files'].append({
                                'filename': filename,
                                'additions': additions,
                                'deletions': deletions
                            })

                            current_commit['additions'] += additions
                            current_commit['deletions'] += deletions
                        except ValueError:
                            # Skip lines that can't be parsed
                            pass

            # Add the last commit
            if current_commit:
                commits.append(current_commit)

            # Process the data
            authors = {}
            commits_by_date = defaultdict(int)
            commits_by_week = defaultdict(int)
            commits_by_month = defaultdict(int)

            for commit in commits:
                author = commit['author']
                if author not in authors:
                    authors[author] = {
                        'commits': 0,
                        'additions': 0,
                        'deletions': 0
                    }

                authors[author]['commits'] += 1
                authors[author]['additions'] += commit['additions']
                authors[author]['deletions'] += commit['deletions']

                # Format dates for different time periods
                date = commit['date']
                day_key = date.strftime('%Y-%m-%d')
                week_key = f"{date.year}-W{date.isocalendar()[1]}"
                month_key = date.strftime('%Y-%m')

                commits_by_date[day_key] += 1
                commits_by_week[week_key] += 1
                commits_by_month[month_key] += 1

            # Calculate total commits
            total_commits = len(commits)

            # Calculate percentages
            for author in authors:
                authors[author]['commit_percentage'] = (authors[author]['commits'] / total_commits) * 100

            # Sort time-based data
            sorted_by_date = dict(sorted(commits_by_date.items()))
            sorted_by_week = dict(sorted(commits_by_week.items()))
            sorted_by_month = dict(sorted(commits_by_month.items()))

            return {
                'commits': commits,
                'authors': authors,
                'total_commits': total_commits,
                'commits_by_date': sorted_by_date,
                'commits_by_week': sorted_by_week,
                'commits_by_month': sorted_by_month
            }

        finally:
            # Return to the original directory
            os.chdir(original_dir)

    def create_commits_by_author_graph(self):
        if not self.git_data:
            return

        # Clear previous plot
        if "commits_by_author" in self.canvases:
            self.canvases["commits_by_author"].get_tk_widget().destroy()

        # Create figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))

        # Extract data
        authors = self.git_data['authors']
        names = []
        commits = []

        for author, data in sorted(authors.items(), key=lambda x: x[1]['commits'], reverse=True):
            names.append(author)
            commits.append(data['commits'])

        # Create bar chart
        bars = ax.bar(names, commits, color='skyblue')

        # Add labels and title
        ax.set_xlabel('Author')
        ax.set_ylabel('Number of Commits')
        ax.set_title('Number of Commits per Author')

        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')

        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height}', ha='center', va='bottom')

        plt.tight_layout()

        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=self.frames["commits_by_author"])
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Store canvas
        self.canvases["commits_by_author"] = canvas

    def create_lines_by_author_graph(self):
        if not self.git_data:
            return

        # Clear previous plot
        if "lines_by_author" in self.canvases:
            self.canvases["lines_by_author"].get_tk_widget().destroy()

        # Create figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))

        # Extract data
        authors = self.git_data['authors']
        names = []
        additions = []
        deletions = []

        for author, data in sorted(authors.items(), key=lambda x: x[1]['additions'] + x[1]['deletions'], reverse=True):
            names.append(author)
            additions.append(data['additions'])
            deletions.append(data['deletions'])

        # Create stacked bar chart
        width = 0.35
        ax.bar(names, additions, width, label='Additions', color='green')
        ax.bar(names, deletions, width, bottom=additions, label='Deletions', color='red')

        # Add labels and title
        ax.set_xlabel('Author')
        ax.set_ylabel('Number of Lines')
        ax.set_title('Number of Lines Added/Removed per Author')
        ax.legend()

        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')

        plt.tight_layout()

        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=self.frames["lines_by_author"])
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Store canvas
        self.canvases["lines_by_author"] = canvas

    def create_commits_by_time_graph(self):
        if not self.git_data:
            return

        # Get selected time period
        time_period = self.time_period_var.get()

        # Clear previous plot
        if "commits_by_time" in self.canvases:
            self.canvases["commits_by_time"].get_tk_widget().destroy()

        # Create figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))

        # Extract data based on time period
        if time_period == "day":
            data = self.git_data['commits_by_date']
            title = 'Number of Commits per Day'
        elif time_period == "week":
            data = self.git_data['commits_by_week']
            title = 'Number of Commits per Week'
        else:  # month
            data = self.git_data['commits_by_month']
            title = 'Number of Commits per Month'

        dates = list(data.keys())
        commit_counts = list(data.values())

        # Create line chart
        ax.plot(dates, commit_counts, marker='o', linestyle='-', color='blue')

        # Add labels and title
        ax.set_xlabel('Time Period')
        ax.set_ylabel('Number of Commits')
        ax.set_title(title)

        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')

        plt.tight_layout()

        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=self.frames["commits_by_time"])
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Store canvas
        self.canvases["commits_by_time"] = canvas

    def update_time_graph(self):
        self.create_commits_by_time_graph()

    def create_percentage_commits_graph(self):
        if not self.git_data:
            return

        # Clear previous plot
        if "percentage_commits" in self.canvases:
            self.canvases["percentage_commits"].get_tk_widget().destroy()

        # Create figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))

        # Extract data
        authors = self.git_data['authors']
        names = []
        percentages = []

        # Sort authors by their commit percentage in descending order
        sorted_authors = sorted(authors.items(), key=lambda x: x[1]['commit_percentage'], reverse=True)

        # Group small contributors into "Other" category (≤10% total)
        other_percentage = 0
        other_count = 0
        total_percentage = 0

        for author, data in sorted_authors:
            # Add major contributors until we reach 90%
            if total_percentage < 90:
                names.append(author)
                percentages.append(data['commit_percentage'])
                total_percentage += data['commit_percentage']
            else:
                # Group remaining contributors into "Other"
                other_percentage += data['commit_percentage']
                other_count += 1

        # Add "Other" category if there are any grouped contributors
        if other_count > 0:
            names.append(f"Other ({other_count} contributors)")
            percentages.append(other_percentage)

        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            percentages,
            labels=names,
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops={'edgecolor': 'w'}
        )

        # Ensure equal aspect ratio
        ax.axis('equal')

        # Add title
        ax.set_title('Percentage of Commits by Author')

        plt.tight_layout()

        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=self.frames["percentage_commits"])
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Store canvas
        self.canvases["percentage_commits"] = canvas

    def create_percentage_contributors_graph(self):
        if not self.git_data:
            return

        # Clear previous plot
        if "percentage_contributors" in self.canvases:
            self.canvases["percentage_contributors"].get_tk_widget().destroy()

        # Create figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))

        # Extract data
        authors = self.git_data['authors']
        total_commits = self.git_data['total_commits']

        # Sort authors by number of commits
        sorted_authors = sorted(authors.items(), key=lambda x: x[1]['commits'], reverse=True)

        # Calculate cumulative percentages
        names = []
        commits = []
        cumulative_percentage = 0

        for author, data in sorted_authors:
            names.append(author)
            commits.append(data['commits'])
            cumulative_percentage += (data['commits'] / total_commits) * 100

        # Create bar chart
        bars = ax.bar(names, commits, color='lightgreen')

        # Add a line for cumulative percentage
        ax2 = ax.twinx()
        cumulative = [sum(commits[:i+1])/sum(commits)*100 for i in range(len(commits))]
        ax2.plot(names, cumulative, 'r-', marker='o', linewidth=2)
        ax2.set_ylabel('Cumulative Percentage (%)', color='r')
        ax2.tick_params(axis='y', labelcolor='r')
        ax2.set_ylim([0, 105])

        # Add labels and title
        ax.set_xlabel('Contributors')
        ax.set_ylabel('Number of Commits')
        ax.set_title('Percentage of Contributors')

        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')

        # Add values on top of bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height}', ha='center', va='bottom')
            ax2.text(bar.get_x() + bar.get_width()/2., cumulative[i] + 2,
                    f'{cumulative[i]:.1f}%', ha='center', va='bottom', color='r')

        plt.tight_layout()

        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=self.frames["percentage_contributors"])
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Store canvas
        self.canvases["percentage_contributors"] = canvas

if __name__ == "__main__":
    # Set up the customtkinter appearance
    ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

    # Create the root window
    root = ctk.CTk()

    # Create the application
    app = GitAnalyticsTool(root)

    # Start the main loop
    root.mainloop()
