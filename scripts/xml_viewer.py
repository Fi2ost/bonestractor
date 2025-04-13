import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import xml.etree.ElementTree as ET
import os # To get the filename for the window title

class SimpleXMLViewerApp:
    def __init__(self, master):
        self.master = master
        master.title("Simple XML Explorer")
        master.geometry("800x600")

        self.tree_frame = ttk.Frame(master)
        self.tree_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(self.tree_frame)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        self.load_button = ttk.Button(master, text="Load XML File", command=self.load_xml)
        self.load_button.pack(pady=10)

        self.status_label = ttk.Label(master, text="Load an XML file to begin.")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)

        self.xml_root = None

    def load_xml(self):
        """Opens a file dialog to select an XML file and loads it into the tree."""
        # Suggest a file, but allow user to choose
        # Example initial file suggestion (can be removed or changed)
        initial_file = "icd10cm_tabular_2025.txt" # Or leave empty: initial_file = ""

        file_path = filedialog.askopenfilename(
            title="Select XML File",
            filetypes=(("XML files", "*.xml"), ("Text files", "*.txt"), ("All files", "*.*")),
            initialfile=initial_file # Suggest the known file
        )

        if not file_path:
            self.status_label.config(text="File loading cancelled.")
            return

        self.tree.delete(*self.tree.get_children()) # Clear previous tree content
        self.xml_root = None

        try:
            # Attempt to parse the selected file
            tree = ET.parse(file_path)
            self.xml_root = tree.getroot()
            self.master.title(f"Simple XML Explorer - {os.path.basename(file_path)}")
            self.populate_tree("", self.xml_root) # Start populating from root
            self.status_label.config(text=f"Loaded: {os.path.basename(file_path)}")

        except ET.ParseError as e:
            messagebox.showerror("XML Parse Error", f"Error parsing XML file:\n{e}")
            self.status_label.config(text="Error parsing XML.")
            self.master.title("Simple XML Explorer") # Reset title on error
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")
            self.status_label.config(text="Error loading file.")
            self.master.title("Simple XML Explorer") # Reset title on error


    def populate_tree(self, parent_node_id, element):
        """Recursively populates the Treeview starting from the given element."""
        display_extra = None
        # Check if this element is a 'chapter'
        if element.tag == 'chapter':
            # Look for a direct child 'desc' element
            desc_element = element.find('desc') # find() gets the first direct child match
            if desc_element is not None and desc_element.text:
                desc_text = desc_element.text.strip()
                if desc_text:
                    # Limit length for display
                    display_extra = (desc_text[:60] + '...') if len(desc_text) > 60 else desc_text

        # Prepare node text: Tag name + attributes
        node_text = f"<{element.tag}"
        if element.attrib:
            attrs = " ".join([f'{k}="{v}"' for k, v in element.attrib.items()])
            node_text += f" {attrs}"
        node_text += ">"

        # Append the description text if found
        if display_extra:
            node_text += f" - {display_extra}"

        # Insert the element node into the tree
        node_id = self.tree.insert(parent_node_id, 'end', text=node_text, open=False)

        # --- Need parent reference check helper ---
        # This function helps check if the parent is a chapter for the desc text handling
        def get_element_parent_tag(el):
            # This is tricky as ElementTree doesn't store parents directly.
            # The workaround adds a temporary attribute.
            try:
                return el.getparent().tag
            except AttributeError:
                return None
        # --- End helper ---

        # Add element's text content if it exists (and isn't handled above)
        element_text = element.text.strip() if element.text else None
        # Avoid adding the chapter description text again if we already added it as 'display_extra'
        # Check if the current tag is 'desc' AND its parent (if accessible via workaround) is 'chapter'
        is_handled_desc = (element.tag == 'desc' and
                           get_element_parent_tag(element) == 'chapter')

        if element_text and not is_handled_desc:
            # Display truncated text as a child node
            truncated_text = (element_text[:75] + '...') if len(element_text) > 75 else element_text
            self.tree.insert(node_id, 'end', text=f'"{truncated_text}"', open=False)

        # Recursively add child elements
        for child in element:
            # Attach parent reference temporarily for the check above
            child.getparent = lambda _el=element: _el
            self.populate_tree(node_id, child)
            del child.getparent # Clean up temporary reference

        # Add element's tail text if it exists
        element_tail = element.tail.strip() if element.tail else None
        if element_tail:
            truncated_tail = (element_tail[:75] + '...') if len(element_tail) > 75 else element_tail
            # Tail text logically appears *after* the element, so insert it under the original parent
            self.tree.insert(parent_node_id, 'end', text=f'... "{truncated_tail}"', open=False)


if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleXMLViewerApp(root)
    root.mainloop()