# gui.py - GUI components and handlers for the Medical Report Extractor

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import logging
import json
import os
# from dataclasses import asdict # Moved import inside function where used
from typing import Optional

# Import necessary components from other modules
from extractor import MedicalReportExtractor
# Import the data model definitions, including the new ProcessedDiagnosis
from data_models import OperativeReport, ProcessedDiagnosis # Make sure ProcessedDiagnosis is imported

logger = logging.getLogger(__name__) # Use module-specific logger

class MedicalReportExtractorApp(tk.Tk):
    """GUI application for Medical Report Extractor."""

    def __init__(self):
        super().__init__()

        self.title("Medical Report Extractor")
        self.geometry("1200x800")
        self.minsize(800, 600)

        self.current_report_text = ""
        # Initialize with None, will hold OperativeReport instance after extraction
        self.current_report_data: Optional[OperativeReport] = None
        self.current_file_path = None

        self.status_var = tk.StringVar() # Define status_var before create_ui

        self.create_menu()
        self.create_ui()
        self.configure_styles()

        self.status_var.set("Ready to extract data from medical reports")


    def configure_styles(self):
        """Configure ttk styles for the application."""
        style = ttk.Style()
        style.theme_use('clam') # Using a theme that usually works well
        style.configure("TNotebook", padding=5)
        style.configure("TNotebook.Tab", padding=[10, 3], font=('Arial', 10))
        style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        style.configure("TButton", padding=5, font=('Arial', 10))
        style.configure("TFrame", background="#f0f0f0") # Light grey background


    def create_menu(self):
        """Create the application menu bar."""
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        # File Menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open Report", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Extracted Data", command=self.save_data, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Edit Menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label="Extract Data", command=self.extract_data, accelerator="Ctrl+E")
        edit_menu.add_command(label="Clear All", command=self.clear_all, accelerator="Ctrl+L")
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)

        # Help Menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="Help", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

        # Bind keyboard shortcuts
        self.bind_all("<Control-o>", lambda event: self.open_file())
        self.bind_all("<Control-s>", lambda event: self.save_data())
        self.bind_all("<Control-e>", lambda event: self.extract_data())
        self.bind_all("<Control-l>", lambda event: self.clear_all())


    def create_ui(self):
        """Create the main user interface components."""
        # Main Frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Paned Window for resizing
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(expand=True, fill=tk.BOTH)

        # --- Left Panel (Input) ---
        left_frame = ttk.Frame(paned_window, padding="5", relief=tk.GROOVE)
        paned_window.add(left_frame, weight=1) # Allow resizing

        ttk.Label(left_frame, text="Paste Report Text Here or Open File:", style="Header.TLabel").pack(pady=(0, 5), anchor=tk.W)
        self.text_input = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, height=10, width=50, font=("Arial", 10))
        self.text_input.pack(expand=True, fill=tk.BOTH, pady=(0, 10))

        # Action buttons below input text
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=(0, 5))

        self.open_button = ttk.Button(button_frame, text="Open File", command=self.open_file)
        self.open_button.pack(side=tk.LEFT, padx=(0, 5))

        self.extract_button = ttk.Button(button_frame, text="Extract Data", command=self.extract_data)
        self.extract_button.pack(side=tk.LEFT, padx=(0, 5))

        self.clear_button = ttk.Button(button_frame, text="Clear All", command=self.clear_all)
        self.clear_button.pack(side=tk.LEFT, padx=(0, 5))

        self.save_button = ttk.Button(button_frame, text="Save Data", command=self.save_data)
        self.save_button.pack(side=tk.LEFT)


        # --- Right Panel (Output Tabs) ---
        right_frame = ttk.Frame(paned_window, padding="5", relief=tk.GROOVE)
        paned_window.add(right_frame, weight=2) # Allow resizing, make it wider initially

        ttk.Label(right_frame, text="Extracted Information:", style="Header.TLabel").pack(pady=(0, 5), anchor=tk.W)

        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(expand=True, fill=tk.BOTH)

        # Create tabs - using ScrolledText for simplicity
        self.tab_patient = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, state=tk.DISABLED, font=("Arial", 10))
        self.tab_admission = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, state=tk.DISABLED, font=("Arial", 10))
        self.tab_provider = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, state=tk.DISABLED, font=("Arial", 10))
        self.diag_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, state=tk.DISABLED, font=("Arial", 10)) # Keep variable name
        self.tab_procedures = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, state=tk.DISABLED, font=("Arial", 10))
        self.tab_misc = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, state=tk.DISABLED, font=("Arial", 10))
        self.tab_json = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, state=tk.DISABLED, font=("Arial", 10))

        self.notebook.add(self.tab_patient, text="Patient")
        self.notebook.add(self.tab_admission, text="Admission/Surgery")
        self.notebook.add(self.tab_provider, text="Providers")
        self.notebook.add(self.diag_text, text="Diagnoses")
        self.notebook.add(self.tab_procedures, text="Procedures")
        self.notebook.add(self.tab_misc, text="Misc")
        self.notebook.add(self.tab_json, text="JSON Output")

        # --- Status Bar ---
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)


    def set_text_widget_content(self, widget, content):
        """Helper to enable, clear, insert, and disable a text widget."""
        widget.config(state=tk.NORMAL)
        widget.delete('1.0', tk.END)
        widget.insert('1.0', content)
        widget.config(state=tk.DISABLED)

    def format_object_for_display(self, obj_instance) -> str:
        """Formats a dataclass instance (like PatientInfo) for display."""
        if not obj_instance:
            return "N/A"
        # Use existing asdict if available, handle potential import issue
        try:
             from dataclasses import asdict
        except ImportError:
             # Handle case where import moved or failed unexpectedly
             logger.error("asdict not available from dataclasses.")
             return str(obj_instance) # Fallback to string representation

        lines = []
        for key, value in asdict(obj_instance).items():
            if value not in [None, "", []]: # Don't display empty fields
                key_formatted = key.replace('_', ' ').title()
                lines.append(f"{key_formatted}: {value}")
        return "\n".join(lines) if lines else "N/A"


    def open_file(self):
        """Open a file dialog to select a report file."""
        filepath = filedialog.askopenfilename(
            title="Open Medical Report File",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                self.current_report_text = f.read()
                self.text_input.delete('1.0', tk.END)
                self.text_input.insert('1.0', self.current_report_text)
                self.current_file_path = filepath
                self.status_var.set(f"Loaded report: {os.path.basename(filepath)}")
                # Clear previous results when loading new file
                self.clear_output_fields()
                self.current_report_data = None
        except Exception as e:
            messagebox.showerror("Error Opening File", f"Failed to read file:\n{e}")
            self.status_var.set("Error loading file.")
            logger.error(f"Error opening file {filepath}: {e}", exc_info=True)


    def extract_data(self):
        """Extract data from the text input and display it."""
        report_text = self.text_input.get("1.0", tk.END).strip()
        if not report_text:
            messagebox.showwarning("Input Required", "Please load or paste report text first.")
            self.status_var.set("No input text provided.")
            return

        self.status_var.set("Extracting data...")
        self.update_idletasks() # Update UI to show status change

        try:
            extractor = MedicalReportExtractor(report_text)
            self.current_report_data = extractor.extract_all() # This now does DB lookups
            self.display_data(self.current_report_data)
            self.status_var.set("Extraction complete.")
            logger.info("Data extraction successful.")
        except Exception as e:
            messagebox.showerror("Extraction Error", f"An error occurred during extraction:\n{e}")
            self.status_var.set("Extraction failed.")
            logger.error(f"Error during extraction: {e}", exc_info=True)


    def display_data(self, report: Optional[OperativeReport]):
        """Display the extracted OperativeReport data in the notebook tabs."""
        self.clear_output_fields() # Clear previous data first

        if not report:
            logger.info("No report data to display.")
            return

        # Patient Tab
        self.set_text_widget_content(self.tab_patient, self.format_object_for_display(report.patient))

        # Admission Tab
        self.set_text_widget_content(self.tab_admission, self.format_object_for_display(report.admission))

        # Provider Tab
        self.set_text_widget_content(self.tab_provider, self.format_object_for_display(report.provider))


        # --- MODIFIED: Diagnoses Tab ---
        self.diag_text.config(state=tk.NORMAL)
        self.diag_text.delete('1.0', tk.END)
        if report.diagnoses and report.diagnoses.processed_diagnoses:
            # Iterate through the list of ProcessedDiagnosis dicts/TypedDicts
            for item in report.diagnoses.processed_diagnoses:
                display_line = f"- {item['original_text']}"
                if item['identified_code']:
                    validity = "(VALID)" if item['is_valid_icd10'] else "(INVALID or Not Found)"
                    db_desc = f" [{item['icd10_description']}]" if item['is_valid_icd10'] and item['icd10_description'] else ""
                    leaf_info = " (Leaf)" if item.get('is_leaf_node') is True else "" # Check optional leaf info
                    display_line += f"  -> Code: {item['identified_code']} {validity}{leaf_info}{db_desc}"
                self.diag_text.insert(tk.END, display_line + "\n")
        else:
            self.diag_text.insert('1.0', "No diagnoses extracted.")
        self.diag_text.config(state=tk.DISABLED)
        # --- END MODIFIED ---


        # Procedures Tab
        self.tab_procedures.config(state=tk.NORMAL)
        self.tab_procedures.delete('1.0', tk.END)
        if report.procedures:
            for proc in report.procedures:
                cpt_str = f" (CPT: {proc.cpt_code})" if proc.cpt_code else " (CPT: N/A)"
                side_str = f" [Side: {proc.side}]" if proc.side else ""
                region_str = f" [Region: {proc.region}]" if proc.region else ""
                self.tab_procedures.insert(tk.END, f"- {proc.name}{cpt_str}{side_str}{region_str}\n")
        else:
            self.tab_procedures.insert('1.0', "No procedures extracted.")
        self.tab_procedures.config(state=tk.DISABLED)

        # Misc Tab
        misc_lines = []
        if report.complications: misc_lines.append(f"Complications: {report.complications}")
        if report.estimated_blood_loss: misc_lines.append(f"Estimated Blood Loss: {report.estimated_blood_loss} ml")
        if report.implants: misc_lines.append(f"Implants: {report.implants}")
        if report.recommendations: misc_lines.append(f"Recommendations: {report.recommendations}")
        self.set_text_widget_content(self.tab_misc, "\n".join(misc_lines) if misc_lines else "N/A")

        # JSON Tab
        try:
             # Need to import asdict here if not imported globally
            from dataclasses import asdict
            json_output = json.dumps(asdict(report), indent=4)
            self.set_text_widget_content(self.tab_json, json_output)
        except Exception as e:
            logger.error(f"Error generating JSON: {e}", exc_info=True)
            self.set_text_widget_content(self.tab_json, f"Error generating JSON:\n{e}")


    def clear_output_fields(self):
        """Clears all output text widgets."""
        widgets = [
            self.tab_patient, self.tab_admission, self.tab_provider,
            self.diag_text, self.tab_procedures, self.tab_misc, self.tab_json
        ]
        for widget in widgets:
            widget.config(state=tk.NORMAL)
            widget.delete('1.0', tk.END)
            widget.config(state=tk.DISABLED)


    def clear_all(self):
        """Clears input text and all output fields."""
        self.text_input.delete('1.0', tk.END)
        self.clear_output_fields()
        self.current_report_text = ""
        self.current_report_data = None
        self.current_file_path = None
        self.status_var.set("Cleared all fields.")
        logger.info("Cleared all input and output fields.")


    def save_data(self):
        """Save the extracted data to a JSON file."""
        if not self.current_report_data:
            messagebox.showwarning("No Data", "No data has been extracted yet.")
            self.status_var.set("No data to save.")
            return

        # Suggest filename based on input file or default
        initial_filename = "extracted_data.json"
        if self.current_file_path:
            base = os.path.basename(self.current_file_path)
            initial_filename = os.path.splitext(base)[0] + "_extracted.json"

        filepath = filedialog.asksaveasfilename(
            title="Save Extracted Data as JSON",
            defaultextension=".json",
            initialfile=initial_filename,
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )
        if not filepath:
            self.status_var.set("Save cancelled.")
            return

        try:
            # Need to import asdict here if not imported globally
            from dataclasses import asdict
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.current_report_data), f, indent=4)
            self.status_var.set(f"Data saved to {os.path.basename(filepath)}")
            logger.info(f"Extracted data saved to {filepath}")
        except Exception as e:
            messagebox.showerror("Error Saving File", f"Failed to save data:\n{e}")
            self.status_var.set("Error saving data.")
            logger.error(f"Error saving data to {filepath}: {e}", exc_info=True)


    def show_about(self):
        """Show information about the application."""
        # ... (keep existing implementation) ...
        about_text = """Medical Report Extractor v1.1 (Modular)\n\nA tool for extracting structured data from medical operative reports.\nThis application uses regular expressions and pattern matching to\nidentify and extract key information from medical reports.\n\nFeatures:\n- Patient demographics extraction\n- Procedure and diagnosis identification\n- CPT code detection\n- Anatomical side and region recognition\n- JSON export capability\n\nCreated by: Medical Informatics Team, 2025\nRefactored by: AI Assistant\n        """
        messagebox.showinfo("About Medical Report Extractor", about_text)


    def show_help(self):
        """Show help information for using the application."""
        # ... (keep existing implementation) ...
        help_text = """Medical Report Extractor - Help\n\nUsing the application:\n\n1. Load a report:\n   - Click "Open File" or use File -> Open Report\n   - Or, paste text directly into the left panel\n\n2. Extract data:\n   - Click "Extract Data" or use Edit -> Extract Data\n   - Extracted info appears in the tabs on the right\n\n3. Review extracted data:\n   - Navigate tabs for categorized data\n   - JSON tab shows the complete structured output\n\n4. Save results:\n   - Click "Save Data" or use File -> Save Extracted Data\n   - Exports data as a JSON file\n\nTips:\n- Consistent report formatting yields better results.\n- Use Edit -> Clear All to reset everything.\n        """
        messagebox.showinfo("Help", help_text)


# Example of how to run if this were the main script
# Normally, main.py would handle this
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO) # Basic logging for standalone test
#     app = MedicalReportExtractorApp()
#     app.mainloop()