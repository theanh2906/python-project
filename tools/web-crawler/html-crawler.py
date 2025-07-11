import concurrent.futures
import datetime
import json
import logging
import os
from tkinter import filedialog, messagebox
from typing import List, Optional

import customtkinter as ctk  # Add customtkinter import
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# JsonAttributeConfig = {
#     "JSONAttribute": str,
#     "Selector": str,
#     "GetElementContent": bool,
#     "ElementAttribute": str
# }
class JsonAttributeConfig:
    def __init__(self, json_attribute: str, selector: str, get_element_content: bool, element_attribute: str):
        self.json_attribute = json_attribute
        self.selector = selector
        self.get_element_content = get_element_content
        self.element_attribute = element_attribute

    def __repr__(self):
        return {
            "json_attribute": self.json_attribute,
            "selector": self.selector,
            "get_element_content": self.get_element_content,
            "element_attribute": self.element_attribute
        }.__str__()


class URLListConfig:
    def __init__(self, selector: str, get_element_content: bool, element_attribute: str):
        self.selector = selector
        self.get_element_content = get_element_content
        self.element_attribute = element_attribute

    def __repr__(self):
        return {
            "selector": self.selector,
            "get_element_content": self.get_element_content,
            "element_attribute": self.element_attribute
        }.__str__()


class HTMLCrawler:
    def __init__(self, timeout: int = 10, user_agent: str = None):
        """
        Initialize the HTML crawler

        Args:
            timeout (int): Request timeout in seconds
            user_agent (str): Custom user agent string
        """
        self.timeout = timeout
        self.headers = {
            'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_html_from_url(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from a URL

        Args:
            url (str): URL to fetch

        Returns:
            Optional[str]: HTML content or None if failed
        """
        try:
            logger.info(f"Fetching HTML from URL: {url}")
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching URL {url}: {str(e)}")
            return None

    def get_html_from_file(self, file_path: str) -> Optional[str]:
        """
        Read HTML content from a local file

        Args:
            file_path (str): Path to the HTML file

        Returns:
            Optional[str]: HTML content or None if failed
        """
        try:
            logger.info(f"Reading HTML from file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except IOError as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return None

    def extract_text_by_selector(self, html: str, selector: str) -> List[str]:
        """
        Extract text from HTML using CSS selector

        Args:
            html (str): HTML content
            selector (str): CSS selector

        Returns:
            List[str]: List of extracted text strings
        """
        try:
            logger.info(f"Extracting text using selector: {selector} (e.g., '.panel-header > a')")
            soup = BeautifulSoup(html, 'html.parser')
            elements = soup.select(selector) if selector else soup.select(
                '*')  # BeautifulSoup already supports jQuery-like selectors

            if not elements:
                logger.warning(f"No elements found with selector: {selector}")
                return []

            return [element.get_text(strip=True) for element in elements]
        except Exception as e:
            logger.error(f"Error extracting text with selector {selector}: {str(e)}")
            return []

    def extract_by_selector(self, html: str, selector: str, get_element_content: bool, element_attribute: str = "") -> List[str]:
        """
        Extract content or attribute from HTML using CSS selector

        Args:
            html (str): HTML content
            selector (str): CSS selector
            get_element_content (bool): Whether to get element content or attribute
            element_attribute (str): Attribute name to extract if get_element_content is False

        Returns:
            List[str]: List of extracted content or attribute values
        """
        try:
            logger.info(f"Extracting {'content' if get_element_content else f'attribute {element_attribute}'} using selector: {selector}")
            soup = BeautifulSoup(html, 'html.parser')
            elements = soup.select(selector) if selector else soup.select('*')

            if not elements:
                logger.warning(f"No elements found with selector: {selector}")
                return []

            if get_element_content:
                return [element.get_text(strip=True) for element in elements]
            else:
                return [element.get(element_attribute, "") for element in elements]
        except Exception as e:
            logger.error(f"Error extracting with selector {selector}: {str(e)}")
            return []

    def save_to_file(self, content: List[str], output_file: str) -> bool:
        """
        Save extracted content to a file

        Args:
            content (List[str]): Content to save
            output_file (str): Output file path

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Saving content to file: {output_file}")
            with open(output_file, 'w', encoding='utf-8') as file:
                for item in content:
                    file.write(f"{item}\n")
            return True
        except IOError as e:
            logger.error(f"Error saving to file {output_file}: {str(e)}")
            return False

    def save_to_json_file(self, content: List[dict], output_file: str) -> bool:
        """
        Save extracted content to a JSON file

        Args:
            content (List[dict]): Content to save as JSON
            output_file (str): Output file path

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Saving content to JSON file: {output_file}")
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(content, file, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            logger.error(f"Error saving to JSON file {output_file}: {str(e)}")
            return False

    def crawl(self, source: str, selector: str, is_url: bool = True, output_file: Optional[str] = None) -> List[str]:
        """
        Main crawling function

        Args:
            source (str): URL or file path
            selector (str): CSS selector
            is_url (bool): True if source is URL, False if local file
            output_file (Optional[str]): Path to save results

        Returns:
            List[str]: Extracted text
        """
        # Get HTML content
        html = self.get_html_from_url(source) if is_url else self.get_html_from_file(source)
        if not html:
            return []

        # Extract text using selector  
        results = self.extract_text_by_selector(html, selector)

        # Save to file if specified
        if output_file and results:
            self.save_to_file(results, output_file)

        return results

    def analyze_json_template(template_path: str) -> tuple[Optional[URLListConfig], list[JsonAttributeConfig]]:
        """
        Analyze the JSON template file to extract relevant information.
        Validates the JSON structure to ensure it contains the required fields.

        Args:
            template_path (str): Path to the JSON template file

        Returns:
            tuple: A tuple containing (URLListConfig or None, list of JsonAttributeConfig)
        """
        try:
            with open(template_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)

                # Validate JSON structure
                if not isinstance(json_data, dict):
                    logger.error(f"Invalid JSON format: Root element must be an object")
                    return None, []

                # Check for JsonAttributeConfig
                if "JsonAttributeConfig" not in json_data:
                    logger.error(f"Invalid JSON format: Missing 'JsonAttributeConfig' key")
                    return None, []

                if not isinstance(json_data.get("JsonAttributeConfig"), list):
                    logger.error(f"Invalid JSON format: 'JsonAttributeConfig' must be an array")
                    return None, []

                # Validate each JsonAttributeConfig item
                for i, item in enumerate(json_data.get("JsonAttributeConfig", [])):
                    if not isinstance(item, dict):
                        logger.error(f"Invalid JSON format: Item {i} in 'JsonAttributeConfig' must be an object")
                        return None, []

                    # Check required fields
                    required_fields = ["json_attribute", "selector", "get_element_content"]
                    for field in required_fields:
                        if field not in item:
                            logger.error(f"Invalid JSON format: Item {i} in 'JsonAttributeConfig' missing required field '{field}'")
                            return None, []

                # Extract URLList configuration if it exists
                url_list_config = None
                if "URLList" in json_data:
                    if not isinstance(json_data.get("URLList"), dict):
                        logger.error(f"Invalid JSON format: 'URLList' must be an object")
                        return None, []

                    # Check required fields for URLList
                    required_fields = ["selector", "get_element_content"]
                    for field in required_fields:
                        if field not in json_data.get("URLList"):
                            logger.error(f"Invalid JSON format: 'URLList' missing required field '{field}'")
                            return None, []

                    url_list_config = URLListConfig(**json_data.get("URLList"))
                    logger.info(f"Found URLList configuration: {url_list_config}")

                # Extract JsonAttributeConfig array
                json_attributes_config = [JsonAttributeConfig(**item) for item in
                                          json_data.get("JsonAttributeConfig", [])]

                return url_list_config, json_attributes_config
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Error reading JSON template {template_path}: {str(e)}")
            return None, []

    def crawl_with_pagination(self, url_template: str, selector: str, start_page: int, end_page: int,
                              output_file: Optional[str] = None) -> List[str]:
        """
        Crawl multiple pages by replacing a placeholder in the URL with page numbers

        Args:
            url_template (str): URL with {page} placeholder
            selector (str): CSS selector
            start_page (int): Starting page number
            end_page (int): Ending page number
            output_file (Optional[str]): Path to save results

        Returns:
            List[str]: Combined extracted text from all pages
        """
        all_results = []

        # Log pagination crawl start
        logger.info(f"Starting pagination crawl from page {start_page} to {end_page}")

        # Loop through each page
        for page_num in range(start_page, end_page + 1):
            # Replace placeholder with current page number
            current_url = url_template.format(page=page_num)
            logger.info(f"Crawling page {page_num}/{end_page}: {current_url}")

            # Get HTML content for current page
            html = self.get_html_from_url(current_url)
            if not html:
                logger.warning(f"Failed to fetch page {page_num}")
                continue

            # Extract text using selector
            page_results = self.extract_text_by_selector(html, selector)

            if page_results:
                logger.info(f"Found {len(page_results)} results on page {page_num}")
                all_results.extend(page_results)
            else:
                logger.warning(f"No results found on page {page_num}")

        # Save all results to file if specified
        if output_file and all_results:
            self.save_to_file(all_results, output_file)

        return all_results

    def crawl_with_json_config(self, source: str, json_attributes_config: List[JsonAttributeConfig], 
                              is_url: bool = True, output_file: Optional[str] = None,
                              is_pagination: bool = False, start_page: int = 1, end_page: int = 1,
                              url_list_config: Optional[URLListConfig] = None) -> List[dict]:
        """
        Crawl with JSON configuration

        Args:
            source (str): URL or file path (with {page} placeholder if is_pagination is True)
            json_attributes_config (List[JsonAttributeConfig]): List of JSON attribute configurations
            is_url (bool): True if source is URL, False if local file
            output_file (Optional[str]): Path to save results
            is_pagination (bool): Whether to use pagination
            start_page (int): Starting page number (only used if is_pagination is True)
            end_page (int): Ending page number (only used if is_pagination is True)
            url_list_config (Optional[URLListConfig]): Configuration for the first phase URL list crawling

        Returns:
            List[dict]: List of dictionaries with extracted data
        """
        all_results = []

        # Check if we need to do two-phase crawling
        if url_list_config and is_url:
            logger.info("Starting two-phase crawling with URLList configuration")

            # Initialize empty list for all URLs
            all_urls = []

            # Phase 1: Crawl the URL list
            if is_pagination:
                logger.info(f"Using pagination for first phase from page {start_page} to {end_page}")

                # Loop through each page to collect URLs
                for page_num in range(start_page, end_page + 1):
                    # Replace placeholder with current page number
                    current_url = source.format(page=page_num)
                    logger.info(f"Crawling page {page_num}/{end_page} for URLs: {current_url}")

                    # Get HTML content for current page
                    html = self.get_html_from_url(current_url)
                    if not html:
                        logger.warning(f"Failed to fetch page {page_num}")
                        continue

                    # Extract URLs from this page
                    page_urls = self.extract_by_selector(
                        html, 
                        url_list_config.selector, 
                        url_list_config.get_element_content, 
                        url_list_config.element_attribute
                    )

                    if page_urls:
                        logger.info(f"Found {len(page_urls)} URLs on page {page_num}")
                        all_urls.extend(page_urls)
                    else:
                        logger.warning(f"No URLs found on page {page_num}")
            else:
                # Single page mode
                html = self.get_html_from_url(source)
                if not html:
                    logger.error(f"Failed to fetch URL list from {source}")
                    return []

                # Extract URLs using the URLList configuration
                all_urls = self.extract_by_selector(
                    html, 
                    url_list_config.selector, 
                    url_list_config.get_element_content, 
                    url_list_config.element_attribute
                )

            # Check if we found any URLs
            if not all_urls:
                logger.warning(f"No URLs found using selector: {url_list_config.selector}")
                return []

            logger.info(f"Found a total of {len(all_urls)} URLs for second phase crawling")

            # Phase 2: Crawl each URL in the list
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, len(all_urls))) as executor:
                # Define a function to process a single URL
                def process_url(url):
                    logger.info(f"Crawling URL: {url}")

                    # Get HTML content for the URL
                    url_html = self.get_html_from_url(url)
                    if not url_html:
                        logger.warning(f"Failed to fetch URL: {url}")
                        return []

                    # Process the HTML
                    url_results = self._process_html_with_config(url_html, json_attributes_config)

                    if url_results:
                        logger.info(f"Found {len(url_results)} results from URL: {url}")
                        return url_results
                    else:
                        logger.warning(f"No results found from URL: {url}")
                        return []

                # Submit all URLs to the thread pool
                future_to_url = {executor.submit(process_url, url): url for url in all_urls}

                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        url_results = future.result()
                        all_results.extend(url_results)
                    except Exception as e:
                        logger.error(f"Error processing URL {url}: {str(e)}")

        elif is_pagination and is_url:
            # Pagination mode with multi-threading
            logger.info(f"Starting pagination crawl with JSON config from page {start_page} to {end_page}")

            # Define a function to process a single page
            def process_page(page_num):
                # Replace placeholder with current page number
                current_url = source.format(page=page_num)
                logger.info(f"Crawling page {page_num}/{end_page}: {current_url}")

                # Get HTML content for current page
                html = self.get_html_from_url(current_url)
                if not html:
                    logger.warning(f"Failed to fetch page {page_num}")
                    return []

                # Process the page
                page_results = self._process_html_with_config(html, json_attributes_config)

                if page_results:
                    logger.info(f"Found {len(page_results)} results on page {page_num}")
                    return page_results
                else:
                    logger.warning(f"No results found on page {page_num}")
                    return []

            # Use a thread pool to process pages in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, end_page - start_page + 1)) as executor:
                # Submit all pages to the thread pool
                future_to_page = {executor.submit(process_page, page_num): page_num 
                                 for page_num in range(start_page, end_page + 1)}

                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_page):
                    page_num = future_to_page[future]
                    try:
                        page_results = future.result()
                        all_results.extend(page_results)
                    except Exception as e:
                        logger.error(f"Error processing page {page_num}: {str(e)}")
        else:
            # Single page/file mode
            # Get HTML content
            html = self.get_html_from_url(source) if is_url else self.get_html_from_file(source)
            if not html:
                return []

            # Process the HTML
            all_results = self._process_html_with_config(html, json_attributes_config)

        # Save results to JSON file if specified
        if output_file and all_results:
            if not output_file.lower().endswith('.json'):
                output_file += '.json'
            self.save_to_json_file(all_results, output_file)

        return all_results

    def _process_html_with_config(self, html: str, json_attributes_config: List[JsonAttributeConfig]) -> List[dict]:
        """
        Process HTML with JSON configuration

        Args:
            html (str): HTML content
            json_attributes_config (List[JsonAttributeConfig]): List of JSON attribute configurations

        Returns:
            List[dict]: List of dictionaries with extracted data
        """
        # Create a dictionary to store results for each selector
        selector_results = {}

        # Extract data for each attribute configuration
        for config in json_attributes_config:
            selector_results[config.json_attribute] = self.extract_by_selector(
                html, 
                config.selector, 
                config.get_element_content, 
                config.element_attribute
            )

        # Find the maximum number of results
        max_results = max([len(results) for results in selector_results.values()], default=0)

        # Create a list of dictionaries, one for each result
        result_list = []
        for i in range(max_results):
            result_dict = {}
            for attr, values in selector_results.items():
                result_dict[attr] = values[i] if i < len(values) else ""
            result_list.append(result_dict)

        return result_list


class HTMLCrawlerGUI:
    def __init__(self):
        # Set up customtkinter appearance
        ctk.set_appearance_mode("System")  # Options: "System", "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"

        # Create the main window with customtkinter
        self.window = ctk.CTk()
        self.window.title("HTML Crawler")
        self.window.geometry("800x600")
        self.json_attributes: list[JsonAttributeConfig]

        # Create crawler instance
        self.crawler = HTMLCrawler()

        # Track paging mode state
        self.paging_mode = False

        # Track crawling state
        self.is_crawling = False

        # Create main frame
        self.main_frame = ctk.CTkFrame(self.window, corner_radius=10)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Create input fields
        self.create_input_fields()

        # Create buttons
        self.create_buttons()

        # Create result area
        self.create_result_area()

        self.window.mainloop()

    def create_input_fields(self):
        # Input frame
        input_frame = ctk.CTkFrame(self.main_frame)
        input_frame.pack(fill="x", padx=10, pady=10)

        # Title for input section
        ctk.CTkLabel(input_frame, text="Input Parameters", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(0, 10))

        # Create two columns
        left_column = ctk.CTkFrame(input_frame)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 5))

        right_column = ctk.CTkFrame(input_frame)
        right_column.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # Left Column - URL and File inputs
        # URL input
        ctk.CTkLabel(left_column, text="URL:").pack(anchor="w", padx=10, pady=(10, 0))
        self.url_entry = ctk.CTkEntry(left_column, height=30, placeholder_text="Enter URL to crawl")
        self.url_entry.pack(fill="x", padx=10, pady=(0, 10))

        # Paging mode switch
        paging_frame = ctk.CTkFrame(left_column)
        paging_frame.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(paging_frame, text="Paging Mode:").pack(side="left", padx=(0, 10))
        self.paging_switch = ctk.CTkSwitch(
            paging_frame,
            text="",
            command=self.toggle_paging_mode,
            onvalue=True,
            offvalue=False
        )
        self.paging_switch.pack(side="left")

        # Help text for paging mode
        self.paging_help = ctk.CTkLabel(
            paging_frame,
            text="Use {page} in URL as placeholder",
            font=ctk.CTkFont(size=10),
            text_color="gray60"
        )
        self.paging_help.pack(side="left", padx=10)

        # Paging options frame (initially hidden)
        self.paging_options_frame = ctk.CTkFrame(left_column)

        # Add paging range inputs
        paging_ranges_frame = ctk.CTkFrame(self.paging_options_frame)
        paging_ranges_frame.pack(fill="x", pady=(0, 5))

        # Start page
        ctk.CTkLabel(paging_ranges_frame, text="Start Page:").pack(side="left", padx=(0, 5))
        self.start_page_entry = ctk.CTkEntry(paging_ranges_frame, width=60, height=25)
        self.start_page_entry.insert(0, "1")
        self.start_page_entry.pack(side="left", padx=(0, 15))

        # End page
        ctk.CTkLabel(paging_ranges_frame, text="End Page:").pack(side="left", padx=(0, 5))
        self.end_page_entry = ctk.CTkEntry(paging_ranges_frame, width=60, height=25)
        self.end_page_entry.insert(0, "5")
        self.end_page_entry.pack(side="left")

        # Example URL with placeholder
        ctk.CTkLabel(
            self.paging_options_frame,
            text="Example: https://example.com/page/{page}",
            font=ctk.CTkFont(size=10),
            text_color="gray60"
        ).pack(anchor="w")

        # JSON config file input with browse button
        ctk.CTkLabel(left_column, text="JSON Config File:").pack(anchor="w", padx=10, pady=(5, 0))
        template_frame = ctk.CTkFrame(left_column)
        template_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Template entry and browse button
        self.config_file = ctk.CTkEntry(template_frame, height=30, placeholder_text="Select local JSON config file")
        self.config_file.pack(side="left", fill="x", expand=True)
        self.template_upload_button = ctk.CTkButton(
            template_frame,
            text="Browse",
            command=self.browse_file,
            width=100,
            height=30,
            fg_color="#3a7ebf",
        )
        self.template_upload_button.pack(side="right", padx=5)

        # Generate example config button
        self.generate_config_button = ctk.CTkButton(
            template_frame,
            text="Generate Template",
            command=self.generate_example_config,
            width=150,
            height=30,
            fg_color="#3a7ebf",
        )
        self.generate_config_button.pack(side="right", padx=5)

        # Right Column - Other inputs
        # Selector input
        ctk.CTkLabel(right_column, text="CSS Selector:").pack(anchor="w", padx=10, pady=(10, 0))
        self.selector_entry = ctk.CTkEntry(right_column, height=30, placeholder_text="e.g., .article h2, div.content p")
        self.selector_entry.pack(fill="x", padx=10, pady=(0, 10))

        # Output file input
        ctk.CTkLabel(right_column, text="Output File:").pack(anchor="w", padx=10, pady=(5, 0))
        self.output_entry = ctk.CTkEntry(right_column, height=30, placeholder_text="Path to save results (optional)")
        self.output_entry.pack(fill="x", padx=10, pady=(0, 10))

        # Timeout input
        ctk.CTkLabel(right_column, text="Timeout (sec):").pack(anchor="w", padx=10, pady=(5, 0))
        self.timeout_entry = ctk.CTkEntry(right_column, height=30)
        self.timeout_entry.insert(0, "10")
        self.timeout_entry.pack(fill="x", padx=10, pady=(0, 10))

    def create_buttons(self):
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(pady=15)

        # Create buttons with customtkinter styling
        self.crawl_button = ctk.CTkButton(
            button_frame,
            text="Crawl",
            command=self.crawl,
            width=150,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2d7d46",
            hover_color="#266f3c"
        )
        self.crawl_button.pack(side="left", padx=10)

        self.crawl_config_button = ctk.CTkButton(
            button_frame,
            text="Crawl with config",
            command=self.crawl_with_json_config,
            width=200,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2d7d46",
            hover_color="#266f3c"
        )
        self.crawl_config_button.pack(side="left", padx=10)

        self.export_button = ctk.CTkButton(
            button_frame,
            text="Export Results",
            command=self.export_results,
            width=150,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.export_button.pack(side="left", padx=10)

        self.clear_button = ctk.CTkButton(
            button_frame,
            text="Clear",
            command=self.clear_all,
            width=150,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#d1335b",
            hover_color="#b32a4e"
        )
        self.clear_button.pack(side="left", padx=10)

    def disable_ui(self):
        """Disable all UI elements during crawling"""
        logger.info("Disabling UI elements during crawling")
        self.is_crawling = True

        # Disable input fields
        self.url_entry.configure(state="disabled")
        self.selector_entry.configure(state="disabled")
        self.output_entry.configure(state="disabled")
        self.timeout_entry.configure(state="disabled")
        self.config_file.configure(state="disabled")

        # Disable paging mode switch and related inputs
        self.paging_switch.configure(state="disabled")
        if self.paging_mode:
            self.start_page_entry.configure(state="disabled")
            self.end_page_entry.configure(state="disabled")

        # Disable buttons
        self.template_upload_button.configure(state="disabled")
        self.crawl_button.configure(state="disabled")
        self.crawl_config_button.configure(state="disabled")
        self.export_button.configure(state="disabled")
        self.clear_button.configure(state="disabled")

    def enable_ui(self):
        """Enable all UI elements after crawling is complete"""
        logger.info("Enabling UI elements after crawling")
        self.is_crawling = False

        # Enable input fields
        self.url_entry.configure(state="normal")
        self.selector_entry.configure(state="normal")
        self.output_entry.configure(state="normal")
        self.timeout_entry.configure(state="normal")
        self.config_file.configure(state="normal")

        # Enable paging mode switch and related inputs
        self.paging_switch.configure(state="normal")
        if self.paging_mode:
            self.start_page_entry.configure(state="normal")
            self.end_page_entry.configure(state="normal")

        # Enable buttons
        self.template_upload_button.configure(state="normal")
        self.crawl_button.configure(state="normal")
        self.crawl_config_button.configure(state="normal")
        self.export_button.configure(state="normal")
        self.clear_button.configure(state="normal")

    def create_result_area(self):
        # Results section label
        ctk.CTkLabel(
            self.main_frame,
            text="Results",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5), anchor="w", padx=10)

        # Results container
        result_frame = ctk.CTkFrame(self.main_frame)
        result_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Replace ScrolledText with CTkTextbox
        self.result_area = ctk.CTkTextbox(
            result_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
        )
        self.result_area.pack(fill="both", expand=True, padx=10, pady=10)
        self.result_area.configure(state="disabled")

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select JSON Config File",
            filetypes=[("JSON files", "*.json")]
        )
        if filename and filename.endswith(".json"):
            try:
                # Validate JSON format before accepting the file
                with open(filename, 'r', encoding='utf-8') as file:
                    json.load(file)  # This will raise an exception if JSON is invalid

                self.config_file.delete(0, "end")
                self.config_file.insert(0, filename)
                self.json_attributes = HTMLCrawler.analyze_json_template(filename)
                logger.info(f"Loaded JSON config file: {filename}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON format in file {filename}: {str(e)}")
                messagebox.showerror("Invalid JSON", f"The selected file contains invalid JSON format:\n{str(e)}")
            except Exception as e:
                logger.error(f"Error loading file {filename}: {str(e)}")
                messagebox.showerror("Error", f"Error loading file:\n{str(e)}")

    def generate_example_config(self):
        """
        Generate an example config.json file in the same directory as the tool.
        If the file exists and is not in the correct format, replace it with a new one.
        If the file exists and is in the correct format, do nothing.
        """
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(script_dir, "config.json")

        # Define the example config template
        example_config = {
            "URLList": {
                "selector": "div.info_chuyengia > a",
                "get_element_content": False,
                "element_attribute": "href"
            },
            "JsonAttributeConfig": [
                {
                    "json_attribute": "Name",
                    "selector": "h1.cl_brand",
                    "get_element_content": True,
                    "element_attribute": ""
                },
                {
                    "json_attribute": "Experience",
                    "selector": "div#collapsekinhnghiemct",
                    "get_element_content": True,
                    "element_attribute": ""
                }
            ],
        }

        # Check if the file already exists
        file_exists = os.path.exists(config_file_path)

        if file_exists:
            try:
                # Try to load the existing file to validate its format
                with open(config_file_path, 'r', encoding='utf-8') as file:
                    json.load(file)

                # If we get here, the file is valid JSON
                logger.info(f"Config file in tool directory already exists and is valid. No changes made.")
                messagebox.showinfo("Config Template", f"Config file in tool directory already exists and is valid. No changes made.")
                return
            except json.JSONDecodeError:
                # File exists but is not valid JSON, so we'll replace it
                logger.warning(f"Config file in tool directory exists but is not valid JSON. Replacing with template.")
                messagebox.showwarning("Config Template", f"Config file in tool directory exists but is not valid JSON. Replacing with template.")
            except FileNotFoundError:
                # File was reported as existing but was deleted (race condition)
                logger.warning(f"Config file in tool directory was reported as existing but cannot be found. Creating new file.")
                file_exists = False
            except Exception as e:
                # Some other error occurred
                logger.error(f"Error checking existing config file in tool directory: {str(e)}")
                messagebox.showerror("Error", f"Error checking existing config file in tool directory: {str(e)}")
                return

        # Create or replace the config file
        try:
            with open(config_file_path, 'w', encoding='utf-8') as file:
                json.dump(example_config, file, indent=2, ensure_ascii=False)

            logger.info(f"Generated example config file in tool directory: {config_file_path}")
            messagebox.showinfo("Config Template", f"Generated example config file in tool directory:\n{config_file_path}")
        except Exception as e:
            logger.error(f"Error generating example config file in tool directory: {str(e)}")
            messagebox.showerror("Error", f"Error generating example config file in tool directory: {str(e)}")

    # This function is no longer needed as we always enable the template upload button
    def check_template_upload_button_state(self):
        self.template_upload_button.configure(state="normal")

    def toggle_paging_mode(self):
        """Toggle between single page and pagination mode"""
        self.paging_mode = self.paging_switch.get()

        if self.paging_mode:
            # Show pagination options
            self.paging_options_frame.pack(fill="x", padx=10, pady=(0, 10))
        else:
            # Hide pagination options
            self.paging_options_frame.pack_forget()

        logger.info(f"Paging mode: {'Enabled' if self.paging_mode else 'Disabled'}")

    def clear_all(self):
        self.url_entry.delete(0, "end")
        self.config_file.delete(0, "end")
        self.selector_entry.delete(0, "end")
        self.output_entry.delete(0, "end")

        # Clear the Results text area
        self.result_area.configure(state="normal")
        self.result_area.delete("0.0", "end")
        self.result_area.configure(state="disabled")

        self.timeout_entry.delete(0, "end")
        self.timeout_entry.insert(0, "10")

        # Reset pagination inputs
        self.start_page_entry.delete(0, "end")
        self.start_page_entry.insert(0, "1")
        self.end_page_entry.delete(0, "end")
        self.end_page_entry.insert(0, "5")

        # Turn off paging mode
        self.paging_switch.deselect()
        self.toggle_paging_mode()

    def crawl(self):
        # Check if already crawling
        if self.is_crawling:
            return

        # Clear previous results
        self.result_area.configure(state="normal")
        self.result_area.delete("0.0", "end")

        url = self.url_entry.get()
        selector = self.selector_entry.get()
        output = self.output_entry.get()

        try:
            timeout = int(self.timeout_entry.get())
        except ValueError:
            self.result_area.insert("end", "Error: Timeout must be a number\n")
            self.result_area.configure(state="disabled")
            return

        # Validate inputs
        if not selector:
            self.result_area.insert("end", "Error: CSS selector is required\n")
            self.result_area.configure(state="disabled")
            return

        if not url:
            self.result_area.insert("end", "Error: URL is required\n")
            self.result_area.configure(state="disabled")
            return

        # Set crawler timeout
        self.crawler.timeout = timeout

        # Check if we're in paging mode or standard mode
        if self.paging_mode:
            # Pagination mode validation - URL is required with {page} placeholder
            if "{page}" not in url:
                self.result_area.insert("end", "Error: URL must contain {page} placeholder in paging mode\n")
                self.result_area.configure(state="disabled")
                return

            # Get and validate start and end page values
            try:
                start_page = int(self.start_page_entry.get())
                end_page = int(self.end_page_entry.get())

                if start_page <= 0 or end_page <= 0:
                    self.result_area.insert("end", "Error: Page numbers must be positive integers\n")
                    self.result_area.configure(state="disabled")
                    return

                if start_page > end_page:
                    self.result_area.insert("end", "Error: Start page cannot be greater than end page\n")
                    self.result_area.configure(state="disabled")
                    return
            except ValueError:
                self.result_area.insert("end", "Error: Page numbers must be integers\n")
                self.result_area.configure(state="disabled")
                return

            # Inform user of pagination crawl starting
            self.result_area.insert("end", f"Starting pagination crawl from page {start_page} to {end_page}...\n\n")

            # Disable UI elements during crawling
            self.disable_ui()

            # Perform pagination crawl in a separate thread
            import threading

            def crawl_thread():
                try:
                    results = self.crawler.crawl_with_pagination(url, selector, start_page, end_page, output)

                    # Update UI with results
                    self.result_area.configure(state="normal")

                    # Display a summary
                    if results:
                        self.result_area.insert("end", f"Found {len(results)} results across {end_page - start_page + 1} pages.\n\n")

                        # Display results
                        for result in results:
                            self.result_area.insert("end", f"{result}\n")

                        # Show count
                        self.result_area.insert("end", f"\nTotal: {len(results)} items found\n")

                        # If output file was specified, show save confirmation
                        if output:
                            self.result_area.insert("end", f"Results saved to: {output}\n")
                    else:
                        self.result_area.insert("end", "No results found across pages.\n")
                except Exception as e:
                    logger.error(f"Error during crawling: {str(e)}")
                    self.result_area.configure(state="normal")
                    self.result_area.insert("end", f"Error during crawling: {str(e)}\n")
                finally:
                    # Re-enable UI elements after crawling is complete
                    self.enable_ui()
                    self.result_area.configure(state="disabled")

            # Start crawling in a separate thread
            thread = threading.Thread(target=crawl_thread)
            thread.daemon = True
            thread.start()
        else:
            # Standard mode - URL only
            # Inform user of crawl starting
            self.result_area.insert("end", "Starting crawl...\n\n")

            # Disable UI elements during crawling
            self.disable_ui()

            # Perform standard crawl in a separate thread
            import threading

            def crawl_thread():
                try:
                    results = self.crawler.crawl(url, selector, True, output)

                    # Update UI with results
                    self.result_area.configure(state="normal")

                    # Display a summary
                    if results:
                        # Display results
                        for result in results:
                            self.result_area.insert("end", f"{result}\n")

                        # Show count
                        self.result_area.insert("end", f"\nTotal: {len(results)} items found\n")

                        # If output file was specified, show save confirmation
                        if output:
                            self.result_area.insert("end", f"Results saved to: {output}\n")
                    else:
                        self.result_area.insert("end", "No results found\n")
                except Exception as e:
                    logger.error(f"Error during crawling: {str(e)}")
                    self.result_area.configure(state="normal")
                    self.result_area.insert("end", f"Error during crawling: {str(e)}\n")
                finally:
                    # Re-enable UI elements after crawling is complete
                    self.enable_ui()
                    self.result_area.configure(state="disabled")

            # Start crawling in a separate thread
            thread = threading.Thread(target=crawl_thread)
            thread.daemon = True
            thread.start()

        # Disable the result area while crawling
        self.result_area.configure(state="disabled")

    def crawl_with_json_config(self):
        # Check if already crawling
        if self.is_crawling:
            return

        # Clear previous results
        self.result_area.configure(state="normal")
        self.result_area.delete("0.0", "end")

        # Get inputs
        url = self.url_entry.get()
        output = self.output_entry.get()
        config_file_path = self.config_file.get()

        try:
            timeout = int(self.timeout_entry.get())
        except ValueError:
            self.result_area.insert("end", "Error: Timeout must be a number\n")
            self.result_area.configure(state="disabled")
            return

        # Validate inputs
        if not config_file_path:
            self.result_area.insert("end", "Error: JSON configuration file is required\n")
            self.result_area.configure(state="disabled")
            return

        if not url:
            self.result_area.insert("end", "Error: URL is required\n")
            self.result_area.configure(state="disabled")
            return

        # Load JSON configuration
        url_list_config, json_attributes_config = HTMLCrawler.analyze_json_template(config_file_path)
        if not json_attributes_config:
            self.result_area.insert("end", f"Error: Failed to load JSON configuration from {config_file_path}\n")
            self.result_area.configure(state="disabled")
            return

        # Log if URLList configuration is found
        if url_list_config:
            self.result_area.insert("end", f"Found URLList configuration. Will perform two-phase crawling.\n")
            logger.info(f"Found URLList configuration: {url_list_config}")

        # Set crawler timeout
        self.crawler.timeout = timeout

        # Check if we're in paging mode or standard mode
        if self.paging_mode:
            # Pagination mode validation - URL is required with {page} placeholder
            if "{page}" not in url:
                self.result_area.insert("end", "Error: URL must contain {page} placeholder in paging mode\n")
                self.result_area.configure(state="disabled")
                return

            # Get and validate start and end page values
            try:
                start_page = int(self.start_page_entry.get())
                end_page = int(self.end_page_entry.get())

                if start_page <= 0 or end_page <= 0:
                    self.result_area.insert("end", "Error: Page numbers must be positive integers\n")
                    self.result_area.configure(state="disabled")
                    return

                if start_page > end_page:
                    self.result_area.insert("end", "Error: Start page cannot be greater than end page\n")
                    self.result_area.configure(state="disabled")
                    return
            except ValueError:
                self.result_area.insert("end", "Error: Page numbers must be integers\n")
                self.result_area.configure(state="disabled")
                return

            # Inform user of pagination crawl starting
            self.result_area.insert("end", f"Starting pagination crawl with JSON config from page {start_page} to {end_page}...\n\n")

            # Disable UI elements during crawling
            self.disable_ui()

            # Perform pagination crawl with JSON config
            import threading

            def crawl_thread():
                try:
                    results = self.crawler.crawl_with_json_config(
                        url, 
                        json_attributes_config, 
                        True, 
                        output, 
                        True, 
                        start_page, 
                        end_page,
                        url_list_config
                    )

                    # Update UI with results
                    self.result_area.configure(state="normal")
                    if results:
                        self.result_area.insert("end", f"Found {len(results)} results across {end_page - start_page + 1} pages.\n\n")
                        self.display_json_results(results)
                    else:
                        self.result_area.insert("end", "No results found across pages.\n")

                    # If output file was specified, show save confirmation
                    if output:
                        output_file = output if output.lower().endswith('.json') else output + '.json'
                        self.result_area.insert("end", f"Results saved to: {output_file}\n")
                except Exception as e:
                    logger.error(f"Error during crawling with JSON config: {str(e)}")
                    self.result_area.configure(state="normal")
                    self.result_area.insert("end", f"Error during crawling: {str(e)}\n")
                finally:
                    # Re-enable UI elements after crawling is complete
                    self.enable_ui()
                    self.result_area.configure(state="disabled")

            # Start crawling in a separate thread
            thread = threading.Thread(target=crawl_thread)
            thread.daemon = True
            thread.start()
        else:
            # Standard mode - URL only
            # Inform user of crawl starting
            self.result_area.insert("end", "Starting crawl with JSON config...\n\n")

            # Disable UI elements during crawling
            self.disable_ui()

            # Perform standard crawl with JSON config
            import threading

            def crawl_thread():
                try:
                    results = self.crawler.crawl_with_json_config(
                        url, 
                        json_attributes_config, 
                        True, 
                        output,
                        url_list_config=url_list_config
                    )

                    # Update UI with results
                    self.result_area.configure(state="normal")
                    if results:
                        self.result_area.insert("end", f"Found {len(results)} results.\n\n")
                        self.display_json_results(results)
                    else:
                        self.result_area.insert("end", "No results found.\n")

                    # If output file was specified, show save confirmation
                    if output:
                        output_file = output if output.lower().endswith('.json') else output + '.json'
                        self.result_area.insert("end", f"Results saved to: {output_file}\n")
                except Exception as e:
                    logger.error(f"Error during crawling with JSON config: {str(e)}")
                    self.result_area.configure(state="normal")
                    self.result_area.insert("end", f"Error during crawling: {str(e)}\n")
                finally:
                    # Re-enable UI elements after crawling is complete
                    self.enable_ui()
                    self.result_area.configure(state="disabled")

            # Start crawling in a separate thread
            thread = threading.Thread(target=crawl_thread)
            thread.daemon = True
            thread.start()

        # Disable the result area while crawling
        self.result_area.configure(state="disabled")

    def display_json_results(self, results: List[dict]):
        """Display JSON results in the result area"""
        for result in results:
            self.result_area.insert("end", json.dumps(result, indent=2, ensure_ascii=False) + "\n\n")

    def export_results(self):
        # Get the content from the result area
        content = self.result_area.get("0.0", "end")
        if not content.strip():
            return

        # Determine if we have JSON results
        is_json = False
        try:
            # Try to find JSON objects in the content
            import re
            json_pattern = r'\{[^{}]*\}'
            json_matches = re.findall(json_pattern, content)
            if json_matches:
                # Try to parse the first match as JSON
                json.loads(json_matches[0])
                is_json = True
        except json.JSONDecodeError:
            is_json = False

        # Get output file path
        output_file = self.output_entry.get()
        if not output_file:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{timestamp}-output.{'json' if is_json else 'txt'}"
        elif is_json and not output_file.lower().endswith('.json'):
            output_file += '.json'

        # Export results
        if is_json:
            # Extract all JSON objects from the content
            try:
                # Parse each JSON object and combine them into a list
                json_objects = []
                for match in json_matches:
                    try:
                        json_obj = json.loads(match)
                        json_objects.append(json_obj)
                    except json.JSONDecodeError:
                        continue

                # Save the JSON objects to a file
                if self.crawler.save_to_json_file(json_objects, output_file):
                    self.result_area.configure(state="normal")
                    self.result_area.insert("end", f"\nResults exported to {output_file}\n")
                    self.result_area.configure(state="disabled")
                else:
                    self.result_area.configure(state="normal")
                    self.result_area.insert("end", f"\nError exporting results\n")
                    self.result_area.configure(state="disabled")
            except Exception as e:
                logger.error(f"Error exporting JSON results: {str(e)}")
                self.result_area.configure(state="normal")
                self.result_area.insert("end", f"\nError exporting results: {str(e)}\n")
                self.result_area.configure(state="disabled")
        else:
            # Export as plain text
            results = content.splitlines()
            if self.crawler.save_to_file(results, output_file):
                self.result_area.configure(state="normal")
                self.result_area.insert("end", f"\nResults exported to {output_file}\n")
                self.result_area.configure(state="disabled")
            else:
                self.result_area.configure(state="normal")
                self.result_area.insert("end", f"\nError exporting results\n")
                self.result_area.configure(state="disabled")


def main():
    HTMLCrawlerGUI()


if __name__ == "__main__":
    main()
