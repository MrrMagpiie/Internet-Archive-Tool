
import json

from PyQt6.QtWidgets import (
     QWidget, QVBoxLayout, QHBoxLayout,QScrollArea, 
    QPushButton, QLineEdit, QTabWidget,
    QLabel, QComboBox, QFormLayout,
    QSplitter,QListWidget, QStackedWidget,
    QMenuBar,QSizePolicy,
)

from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt6.QtGui import QAction
#from config import SCHEMAS_PATH
from view.components import Page
#from view.pages.SchemaBuilderPage import SchemaBuilderPage

class MetadataPage(Page):
    load_documents = pyqtSignal()
    db_metadata = pyqtSignal(str,str) #doc_id
    new_format_window = pyqtSignal(bool)

    def __init__(self, parent):
        super().__init__(parent)
        self.docs_dict = {}
        self.doc_list = QListWidget()
        self.db_data = {}
        self.current_doc_id = None
        self.form_widgets = {}
        
        #self.create_layout()
'''    
    @pyqtSlot(dict) # db_data
    def load_documents(self, db_data):
        """Receives the full manifest from the ProcessManager and populates the list."""
        #self.doc_list.clear()
        self.db_data = db_data
        for doc_id in db_data:
            Doc = db_data[doc_id]
            self.docs_dict[doc_id] = Doc.metadata_file
            if Doc.metadata_file == None and len(self.doc_list.findItems(doc_id,Qt.MatchFlag.MatchExactly)) == 0:
                self.doc_list.addItem(doc_id)
            

    @pyqtSlot()
    def _load_metadata_formats(self):
        with open(SCHEMAS_PATH /'metadataDef.json','r') as f:
            self.metadata_formats = json.load(f)
        self.doc_type_combo.clear()
        for key in self.metadata_formats.keys():
            self.doc_type_combo.addItem(key, self.metadata_formats[key])

    def create_layout(self):
        
        main_layout = QVBoxLayout(self)

        # --- Menu Bar ---
        menu = QMenuBar()
        menu_policy = menu.sizePolicy()
        menu_policy.setVerticalPolicy(QSizePolicy.Policy.Fixed)
        menu.setSizePolicy(menu_policy)
        
        
        formats_menu = menu.addMenu("Manage Formats")
        new_action = QAction("New Format", self)
        new_action.triggered.connect(self._new_format_window)

        edit_action = QAction("Edit Format", self)
        edit_action.triggered.connect(lambda: self._new_format_window(True))
        
        remove_action = QAction("Remove Format", self)

        formats_menu.addAction(new_action)
        formats_menu.addAction(edit_action)
        formats_menu.addAction(remove_action)

        main_layout.addWidget(menu)

        # --------------- Core Component --------------  
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("Documents needing metadata:"))
        
        left_layout.addWidget(self.doc_list)
        splitter.addWidget(left_panel)
        
        self.right_panel = QWidget()
        right_panel_layout = QVBoxLayout(self.right_panel)
        
        self.doc_type_combo = QComboBox()
        self._load_metadata_formats()
        
        self.stack = QStackedWidget()
        
        self.empty_page = QWidget()
        self.type_selection_page = self._create_type_selection_page()
        self.form_page = self._create_form_page()
        self.requirements_page = self._create_requirements_page()

        self.stack.addWidget(self.empty_page)
        self.stack.addWidget(self.type_selection_page)
        self.stack.addWidget(self.form_page)
        self.stack.addWidget(self.requirements_page)
        
        self.selected_label = QLabel('Select a Document')
        right_panel_layout.addWidget(self.selected_label)
        right_panel_layout.addWidget(self.stack)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([200, 500])

        # --- Connections ---
        self.doc_list.currentItemChanged.connect(self._on_doc_selected)       

    def _on_doc_selected(self, current_item, previous_item):
        """When a document is selected, show the correct view in the stack."""
        if not current_item:
            return

        self.current_doc_id = current_item.text()
        self.selected_label.setText(f'Currently Selected: {self.current_doc_id}')
        if self.docs_dict[self.current_doc_id] is None:
            self.stack.setCurrentWidget(self.type_selection_page)
        else:
            self._build_form()
            self.stack.setCurrentWidget(self.form_page)
            self._populate_form()

    def _create_type_selection_page(self):
        """Creates the simple page for choosing a document type."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("This document has no metadata. Please select a type:"))
        layout.addWidget(self.doc_type_combo)
        select_btn = QPushButton('Select')
        select_btn.clicked.connect(self._metadata_type_selected)
        layout.addWidget(select_btn)
        layout.addStretch()
        return page

    def _create_requirements_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel('All required* fields must be filled'))
        return_brn = QPushButton('Return')
        return_brn.clicked.connect(lambda:self.stack.setCurrentWidget(self.form_page))
        layout.addWidget(return_brn)

        return page

    def _metadata_type_selected(self):
        self.db_data[self.current_doc_id].metadata_file_type = self.doc_type_combo.currentData()
        self._build_form()
        self.stack.setCurrentWidget(self.form_page)
        self._populate_form()

    def _create_form_page(self):
        """Creates the full metadata editing form page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        form_container = QWidget()
        self.form_layout = QFormLayout(form_container)
        save_button = QPushButton("Save Metadata")
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(form_container)
        
        layout.addWidget(scroll_area)
        layout.addWidget(save_button)
        
        save_button.clicked.connect(self._on_save)
        return page

    def _build_form(self):
        """Dynamically builds the input form based on the selected JSON schema."""
        if not self.current_doc_id:
            # If no document is selected, do nothing.
            return
        self._clear_layout(self.form_layout)
        self.form_widgets = {}
        
        schema_path = self.db_data[self.current_doc_id].metadata_file_type
        if not schema_path: return

        try:
            self.current_schema = self._load_and_resolve_schema(schema_path)
        except Exception as e:
            print(f"Error loading schema: {e}")
            return
            
        required_fields = self.current_schema.get("required", [])

        def add_field_widget(name,details):
            label_text = details.get("title", name.replace('_', ' ').title())
            if name in required_fields:
                label_text += " *"
            
            input_widget = None

            # --- Check for "enum" to create a QComboBox ---
            if "enum" in details:
                input_widget = QComboBox()
                input_widget.addItems(details["enum"])
                
                # Set the default value for the dropdown
                if "default" in details:
                    input_widget.setCurrentText(str(details["default"]))

            # --- Fallback for regular strings to create a QLineEdit ---
            elif details.get("type") == "string":
                input_widget = QLineEdit()
                
                # Set the default value for the text field
                if "default" in details:
                    input_widget.setText(str(details["default"]))

            # --- Fallback for arrays of strings ---
            elif details.get("type") == "array" and details.get("items", {}).get("type") == "string":
                input_widget = QLineEdit()
                input_widget.setPlaceholderText("Enter values separated by commas")
                
                # Set the default value for the array field
                if "default" in details and isinstance(details["default"], list):
                    # Join the list into a comma-separated string
                    input_widget.setText(", ".join(details["default"]))
            self.form_widgets[name] = input_widget
            self.form_layout.addRow(label_text, input_widget)
        
        for field_name in required_fields:
            if field_name in self.current_schema.get("properties", {}):
                details = self.current_schema["properties"][field_name]
                add_field_widget(field_name, details)
        
        # --- Pass 2: Add all optional fields ---
        for field_name, details in self.current_schema.get("properties", {}).items():
            if field_name not in required_fields:
                add_field_widget(field_name, details)
            
    def _populate_form(self):
        """Fills the currently displayed form with data from the selected document."""
        if not self.current_doc_id: return
        doc = self.db_data[self.current_doc_id]
        if not doc.metadata_file: return

        with open(doc.metadata_file,"r") as f:
            metadata = json.load(f)
        # Loop through the form widgets we created
        for name, widget in self.form_widgets.items():
            # Get the value from the Document object's to_dict representation
            value = metadata.get(name)
            if value:
                if isinstance(value, list):
                    widget.setText(", ".join(value))
                else:
                    widget.setText(str(value))

    def _on_save(self):
        required_fields = self.current_schema.get("required", [])
        """Reads data from the form, creates a metadata dict, and saves it."""
        if not self.current_doc_id:
            return
        Doc = self.db_data.get(self.current_doc_id)
        if not Doc:
            return
        metadata = {}
        for name, widget in self.form_widgets.items():
            value = None
            if isinstance(widget, QComboBox):
                value = widget.currentText()
            elif isinstance(widget, QLineEdit):
                    value = widget.text()
            
            if name in required_fields and (value == '' or value is None):
                self.stack.setCurrentWidget(self.requirements_page)
                return
            elif value is not None and value != "":
                    metadata[name] = value  
        with open(Doc.path/'metadata.json', 'w') as f:
            json.dump(metadata,f)
        self.db_metadata.emit(Doc.doc_id,Doc.metadata_file_type)
        print(f"Saved and emitted updates for {self.current_doc_id}")
        self.stack.setCurrentWidget(self.empty_page)
        self.doc_list.clearSelection()

    def _load_and_resolve_schema(self, schema_path):
        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Could not load/parse schema: {e}")
        return schema

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _new_format_window(self, edit = False):
        self.format_window=self.parent.SchemaBuilderPage(edit)
        self.format_window.show()

    def _new_window(self,widget):
        self.newWindow = QWidget()
        window_layout = QVBoxLayout(self.newWindow)
        window_layout.addWidget(widget)
        self.newWindow.setGeometry(400, 400, 600, 600)
        self.newWindow.show()
    '''