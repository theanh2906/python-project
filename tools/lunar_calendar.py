import calendar
import datetime
import math

import customtkinter as ctk

# Configure customtkinter appearance
ctk.set_appearance_mode("System")  # Options: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"

# Constants for lunar calendar calculations
LUNAR_CYCLE = 29.53  # Average length of a lunar month in days

class LunarDate:
    """Class to handle lunar date calculations and conversions"""
    
    def __init__(self, year: int, month: int, day: int):
        self.year = year
        self.month = month
        self.day = day
        
    @classmethod
    def from_solar_date(cls, date: datetime.date) -> 'LunarDate':
        """Convert a solar date to lunar date"""
        # This is a simplified calculation for demonstration
        # In a real application, you would use more accurate algorithms or libraries
        
        # Days since new moon on 2000-01-6 (a known new moon)
        days_since_new_moon_2000 = (date - datetime.date(2000, 1, 6)).days
        
        # Calculate lunar cycles since then
        lunar_cycles = days_since_new_moon_2000 / LUNAR_CYCLE
        
        # Extract the fractional part to get the day in the lunar month
        fractional_part = lunar_cycles - math.floor(lunar_cycles)
        lunar_day = math.floor(fractional_part * LUNAR_CYCLE) + 1
        
        # Calculate lunar month and year (simplified)
        total_months = math.floor(lunar_cycles)
        lunar_year = 2000 + total_months // 12
        lunar_month = (total_months % 12) + 1
        
        return cls(lunar_year, lunar_month, lunar_day)
    
    def __str__(self) -> str:
        return f"Lunar {self.year}/{self.month}/{self.day}"


class CalendarApp:
    """Modern calendar application with lunar calendar support"""
    
    def __init__(self):
        # Create the main window
        self.window = ctk.CTk()
        self.window.title("Lunar Calendar")
        self.window.geometry("1200x800")
        
        # Current date and view settings
        self.today = datetime.date.today()
        self.current_date = self.today
        self.current_view = "month"  # Options: "week", "month", "year"
        
        # Create the main layout
        self.create_layout()
        
        # Initialize the calendar view
        self.update_calendar()
        
        # Start the application
        self.window.mainloop()
    
    def create_layout(self):
        """Create the main application layout"""
        # Main container
        self.main_container = ctk.CTkFrame(self.window)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header with navigation and view controls
        self.create_header()
        
        # Calendar view area
        self.calendar_frame = ctk.CTkFrame(self.main_container)
        self.calendar_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Footer with status and info
        self.create_footer()
    
    def create_header(self):
        """Create the header with navigation and view controls"""
        header_frame = ctk.CTkFrame(self.main_container)
        header_frame.pack(fill="x", padx=10, pady=(10, 20))
        
        # Left side - Navigation buttons
        nav_frame = ctk.CTkFrame(header_frame)
        nav_frame.pack(side="left", fill="y")
        
        ctk.CTkButton(
            nav_frame,
            text="Today",
            command=self.go_to_today,
            width=80,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2d7d46",
            hover_color="#266f3c"
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            nav_frame,
            text="◀",
            command=self.previous_period,
            width=40,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            nav_frame,
            text="▶",
            command=self.next_period,
            width=40,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=5)
        
        # Center - Current period display
        self.period_label = ctk.CTkLabel(
            header_frame,
            text="",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.period_label.pack(side="left", expand=True)
        
        # Right side - View selection
        view_frame = ctk.CTkFrame(header_frame)
        view_frame.pack(side="right", fill="y")
        
        self.view_buttons = {}
        for view in ["Week", "Month", "Year"]:
            view_lower = view.lower()
            button = ctk.CTkButton(
                view_frame,
                text=view,
                command=lambda v=view_lower: self.change_view(v),
                width=80,
                height=35,
                font=ctk.CTkFont(size=13),
                fg_color="#3a7ebf" if view_lower == self.current_view else "gray40",
                hover_color="#2a6eaf"
            )
            button.pack(side="left", padx=5)
            self.view_buttons[view_lower] = button
    
    def create_footer(self):
        """Create the footer with status and info"""
        footer_frame = ctk.CTkFrame(self.main_container)
        footer_frame.pack(fill="x", padx=10, pady=(20, 10))
        
        # Left side - Lunar date info
        self.lunar_info = ctk.CTkLabel(
            footer_frame,
            text="",
            font=ctk.CTkFont(size=13)
        )
        self.lunar_info.pack(side="left", padx=10)
        
        # Right side - Theme toggle
        theme_frame = ctk.CTkFrame(footer_frame)
        theme_frame.pack(side="right", fill="y", padx=10)
        
        ctk.CTkLabel(theme_frame, text="Theme:").pack(side="left", padx=(0, 10))
        
        self.theme_switch = ctk.CTkSwitch(
            theme_frame,
            text="Dark",
            command=self.toggle_theme,
            onvalue=True,
            offvalue=False
        )
        self.theme_switch.pack(side="left")
        
        # Set initial state based on system theme
        if ctk.get_appearance_mode() == "Dark":
            self.theme_switch.select()
    
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        if self.theme_switch.get():
            ctk.set_appearance_mode("Dark")
            self.theme_switch.configure(text="Dark")
        else:
            ctk.set_appearance_mode("Light")
            self.theme_switch.configure(text="Light")
        
    def go_to_today(self):
        """Reset to today's date"""
        self.current_date = self.today
        self.update_calendar()
    
    def previous_period(self):
        """Go to previous week/month/year based on current view"""
        if self.current_view == "week":
            self.current_date -= datetime.timedelta(days=7)
        elif self.current_view == "month":
            # Go to first day of current month, then subtract one day to get to previous month
            first_day = datetime.date(self.current_date.year, self.current_date.month, 1)
            self.current_date = first_day - datetime.timedelta(days=1)
            # Then set to first day of that month
            self.current_date = datetime.date(self.current_date.year, self.current_date.month, 1)
        elif self.current_view == "year":
            self.current_date = datetime.date(self.current_date.year - 1, self.current_date.month, 1)
        
        self.update_calendar()
    
    def next_period(self):
        """Go to next week/month/year based on current view"""
        if self.current_view == "week":
            self.current_date += datetime.timedelta(days=7)
        elif self.current_view == "month":
            # If December, go to January of next year
            if self.current_date.month == 12:
                self.current_date = datetime.date(self.current_date.year + 1, 1, 1)
            else:
                self.current_date = datetime.date(self.current_date.year, self.current_date.month + 1, 1)
        elif self.current_view == "year":
            self.current_date = datetime.date(self.current_date.year + 1, self.current_date.month, 1)
        
        self.update_calendar()
    
    def change_view(self, view: str):
        """Change the calendar view (week, month, year)"""
        if view != self.current_view:
            self.current_view = view
            
            # Update button colors
            for v, button in self.view_buttons.items():
                button.configure(fg_color="#3a7ebf" if v == view else "gray40")
            
            self.update_calendar()
    
    def update_calendar(self):
        """Update the calendar display based on current date and view"""
        # Clear existing calendar widgets
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
        
        # Update period label
        if self.current_view == "week":
            # Calculate the start of the week (Monday)
            start_of_week = self.current_date - datetime.timedelta(days=self.current_date.weekday())
            end_of_week = start_of_week + datetime.timedelta(days=6)
            self.period_label.configure(
                text=f"{start_of_week.strftime('%b %d')} - {end_of_week.strftime('%b %d, %Y')}"
            )
            self.display_week_view(start_of_week)
        
        elif self.current_view == "month":
            self.period_label.configure(
                text=self.current_date.strftime("%B %Y")
            )
            self.display_month_view()
        
        elif self.current_view == "year":
            self.period_label.configure(
                text=str(self.current_date.year)
            )
            self.display_year_view()
        
        # Update lunar info for current date
        lunar_date = LunarDate.from_solar_date(self.current_date)
        self.lunar_info.configure(
            text=f"Today: {self.today.strftime('%Y-%m-%d')} | {lunar_date}"
        )
    
    def display_week_view(self, start_date: datetime.date):
        """Display the week view"""
        # Create header row with day names
        header_frame = ctk.CTkFrame(self.calendar_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        col_width = 1 / len(days)
        
        for i, day in enumerate(days):
            day_label = ctk.CTkLabel(
                header_frame,
                text=day,
                font=ctk.CTkFont(size=14, weight="bold"),
                width=int(self.calendar_frame.winfo_width() * col_width)
            )
            day_label.grid(row=0, column=i, sticky="ew", padx=2, pady=5)
            header_frame.grid_columnconfigure(i, weight=1)
        
        # Create the days grid
        days_frame = ctk.CTkFrame(self.calendar_frame)
        days_frame.pack(fill="both", expand=True)
        
        for i in range(7):
            days_frame.grid_columnconfigure(i, weight=1)
            
            current_date = start_date + datetime.timedelta(days=i)
            lunar_date = LunarDate.from_solar_date(current_date)
            
            day_frame = ctk.CTkFrame(days_frame)
            day_frame.grid(row=0, column=i, sticky="nsew", padx=2, pady=2)
            
            # Date number with highlight for today
            is_today = current_date == self.today
            date_label = ctk.CTkLabel(
                day_frame,
                text=str(current_date.day),
                font=ctk.CTkFont(size=16, weight="bold" if is_today else "normal"),
                fg_color="#3a7ebf" if is_today else "transparent",
                corner_radius=8,
                width=30,
                height=30
            )
            date_label.pack(anchor="nw", padx=10, pady=10)
            
            # Lunar date
            lunar_label = ctk.CTkLabel(
                day_frame,
                text=f"Lunar: {lunar_date.month}/{lunar_date.day}",
                font=ctk.CTkFont(size=12),
                text_color="gray60"
            )
            lunar_label.pack(anchor="nw", padx=10, pady=(0, 10))
            
            # Make the frame expandable
            days_frame.grid_rowconfigure(0, weight=1)
    
    def display_month_view(self):
        """Display the month view"""
        month_frame = ctk.CTkFrame(self.calendar_frame)
        month_frame.pack(fill="both", expand=True)
        
        # Get the calendar for the current month
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        
        # Create header row with day names
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        for i, day in enumerate(days):
            day_label = ctk.CTkLabel(
                month_frame,
                text=day,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            day_label.grid(row=0, column=i, sticky="ew", padx=2, pady=5)
            month_frame.grid_columnconfigure(i, weight=1)
        
        # Create the days grid
        for week_idx, week in enumerate(cal):
            month_frame.grid_rowconfigure(week_idx + 1, weight=1)
            
            for day_idx, day in enumerate(week):
                if day == 0:  # Day is outside current month
                    continue
                
                current_date = datetime.date(self.current_date.year, self.current_date.month, day)
                lunar_date = LunarDate.from_solar_date(current_date)
                
                # Create frame for each day
                day_frame = ctk.CTkFrame(month_frame)
                day_frame.grid(row=week_idx + 1, column=day_idx, sticky="nsew", padx=2, pady=2)
                
                # Date number with highlight for today
                is_today = current_date == self.today
                date_label = ctk.CTkLabel(
                    day_frame,
                    text=str(day),
                    font=ctk.CTkFont(size=16, weight="bold" if is_today else "normal"),
                    fg_color="#3a7ebf" if is_today else "transparent",
                    corner_radius=8,
                    width=30,
                    height=30
                )
                date_label.pack(anchor="nw", padx=5, pady=5)
                
                # Lunar date
                lunar_label = ctk.CTkLabel(
                    day_frame,
                    text=f"{lunar_date.month}/{lunar_date.day}",
                    font=ctk.CTkFont(size=10),
                    text_color="gray60"
                )
                lunar_label.pack(anchor="nw", padx=5, pady=(0, 5))
    
    def display_year_view(self):
        """Display the year view"""
        year_frame = ctk.CTkFrame(self.calendar_frame)
        year_frame.pack(fill="both", expand=True)
        
        # Create a 4x3 grid for months
        for i in range(4):
            year_frame.grid_rowconfigure(i, weight=1)
            for j in range(3):
                year_frame.grid_columnconfigure(j, weight=1)
                
                month_idx = i * 3 + j + 1
                if month_idx > 12:
                    continue
                
                # Create frame for each month
                month_frame = ctk.CTkFrame(year_frame)
                month_frame.grid(row=i, column=j, sticky="nsew", padx=5, pady=5)
                
                # Month name
                month_name = calendar.month_name[month_idx]
                month_label = ctk.CTkLabel(
                    month_frame,
                    text=month_name,
                    font=ctk.CTkFont(size=14, weight="bold")
                )
                month_label.pack(anchor="n", pady=(5, 10))
                
                # Get the calendar for this month
                cal = calendar.monthcalendar(self.current_date.year, month_idx)
                
                # Create mini calendar
                cal_frame = ctk.CTkFrame(month_frame)
                cal_frame.pack(fill="both", expand=True, padx=5, pady=5)
                
                # Day headers (abbreviated)
                days = ["M", "T", "W", "T", "F", "S", "S"]
                for day_idx, day in enumerate(days):
                    day_label = ctk.CTkLabel(
                        cal_frame,
                        text=day,
                        font=ctk.CTkFont(size=10),
                        width=20
                    )
                    day_label.grid(row=0, column=day_idx, sticky="ew")
                    cal_frame.grid_columnconfigure(day_idx, weight=1)
                
                # Days grid
                for week_idx, week in enumerate(cal):
                    cal_frame.grid_rowconfigure(week_idx + 1, weight=1)
                    
                    for day_idx, day in enumerate(week):
                        if day == 0:  # Day is outside current month
                            continue
                        
                        # Check if this is today
                        is_today = (self.today.year == self.current_date.year and 
                                   self.today.month == month_idx and 
                                   self.today.day == day)
                        
                        # Day number
                        day_label = ctk.CTkLabel(
                            cal_frame,
                            text=str(day),
                            font=ctk.CTkFont(size=10),
                            fg_color="#3a7ebf" if is_today else "transparent",
                            corner_radius=5,
                            width=20,
                            height=20
                        )
                        day_label.grid(row=week_idx + 1, column=day_idx, padx=1, pady=1)


def main():
    """Main entry point for the application"""
    app = CalendarApp()


if __name__ == "__main__":
    main()