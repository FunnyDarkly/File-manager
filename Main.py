import sqlite3
import sys
from datetime import datetime
from os.path import getsize, basename, splitext
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QVBoxLayout, QTableWidget, QFileDialog, QTableWidgetItem, QDialog
from tab_create import Ui_Form
from tab_edit import Ui_TabEdit  # Import the UI for editing the tab name


class FileTableWidget(QTableWidget):
    def __init__(self, parent=None, db_name='files_data.db'):
        super(FileTableWidget, self).__init__(parent)

        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(['Filename', 'Create date', 'Add date', 'File extension', 'Size'])
        self.setSortingEnabled(True)

        self.db_name = db_name
        self.init_db()
        self.load_data()

    def init_db(self):
        """Initialize SQLite database."""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            create_date DATETIME NOT NULL,
            add_date DATETIME NOT NULL,
            file_extension TEXT NOT NULL,
            size INTEGER NOT NULL
        )
        ''')
        self.conn.commit()

    def load_data(self):
        """Load data from the database into the table."""
        self.setRowCount(0)
        self.cursor.execute('SELECT filename, create_date, add_date, file_extension, size FROM files')
        rows = self.cursor.fetchall()

        for row in rows:
            if row:  # Ensure the row is not empty
                self.insertRow(self.rowCount())
                self.setItem(self.rowCount() - 1, 0, QTableWidgetItem(row[0]))
                self.setItem(self.rowCount() - 1, 1, QTableWidgetItem(row[1]))
                self.setItem(self.rowCount() - 1, 2, QTableWidgetItem(row[2]))
                self.setItem(self.rowCount() - 1, 3, QTableWidgetItem(row[3]))
                self.setItem(self.rowCount() - 1, 4, QTableWidgetItem(str(row[4])))

    def add_files_to_table(self):
        """Open a file dialog to select multiple files and add them to the table and database."""
        options = QFileDialog.Options()
        file_names, _ = QFileDialog.getOpenFileNames(self, "Select files", "", "All Files (*)", options=options)

        if file_names:
            for file_name in file_names:
                try:
                    if not file_name:  # Check if the file name is empty
                        continue

                    file_size = self.get_file_size(file_name)  # Get the file size
                    file_extension = splitext(file_name)[1]  # Get file extension

                    # Extract only the filename without path or extension
                    base_name = basename(file_name)  # Get the full filename with extension
                    file_name_only = splitext(base_name)[0]  # Remove the extension

                    create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    add_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Insert into the database
                    self.cursor.execute(
                        'INSERT INTO files (filename, create_date, add_date, file_extension, size) VALUES (?, ?, ?, ?, ?)',
                        (file_name_only, create_date, add_date, file_extension, file_size))
                    self.conn.commit()

                    # Add to the table
                    self.add_file(file_name_only, create_date, add_date, file_extension, file_size)

                except Exception as e:
                    print(f"Error adding file '{file_name}': {e}")  # Log the error

    def add_file(self, file_name, create_date, add_date, file_extension, file_size):
        """Add a file to the table."""
        row_position = self.rowCount()
        self.insertRow(row_position)
        self.setItem(row_position, 0, QTableWidgetItem(file_name))  # Set filename
        self.setItem(row_position, 1, QTableWidgetItem(create_date))  # Set create date
        self.setItem(row_position, 2, QTableWidgetItem(add_date))  # Set add date
        self.setItem(row_position, 3, QTableWidgetItem(file_extension))  # Set file extension
        self.setItem(row_position, 4, QTableWidgetItem(str(file_size)))  # Set size

    def clear_database(self):
        """Clear the database of the associated table."""
        try:
            self.cursor.execute("DELETE FROM files")  # Remove all entries from the table
            self.conn.commit()
            self.load_data()  # Reload data to reflect changes in the table
            print("Database cleared successfully.")
        except Exception as e:
            print(f"Error clearing the database: {e}")

    def get_file_size(self, file_name):
        """Get the size of the file."""
        return getsize(file_name)

    def close_db(self):
        """Close the database connection."""
        self.conn.close()



class MyApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyApp, self).__init__()
        uic.loadUi('main.ui', self)  # Adjust the filename

        self.tab_widget = self.findChild(QtWidgets.QTabWidget, 'tabWidget')  # Adjust the object name
        self.tab_widget.tabCloseRequested.connect(lambda index: self.tab_widget.removeTab(index))

        self.layout = QVBoxLayout(self.tab_widget.widget(0))  # Use QVBoxLayout for alignment
        self.file_table_widget = FileTableWidget(self.tab_widget.widget(0), db_name='default_folder.db')  # Unique DB
        self.layout.addWidget(self.file_table_widget)

        self.add_button = self.findChild(QtWidgets.QPushButton, 'fileaddButton')  # Adjust name as needed
        self.add_button.clicked.connect(self.add_files_to_active_table)

        self.tabcreateButton = self.findChild(QtWidgets.QPushButton, 'tabcreateButton')
        self.tabcreateButton.clicked.connect(self.open_tab_create_window)

        self.actionClear_database = self.findChild(QtWidgets.QAction, 'actionClear_database')
        self.actionClear_database.triggered.connect(self.clear_active_tab_database)

        self.tabeditButton = self.findChild(QtWidgets.QPushButton, 'tabeditButton')  # Add this line
        self.tabeditButton.clicked.connect(self.open_tab_edit_window)  # Connect to the new method

    def add_files_to_active_table(self):
        # Get the currently selected tab's widget
        current_index = self.tab_widget.currentIndex()
        current_tab = self.tab_widget.widget(current_index)

        # Find the FileTableWidget within the current tab
        table_widget = current_tab.findChild(FileTableWidget)  # Ensure we find the correct class

        if table_widget:
            table_widget.add_files_to_table()  # Call the method to add files to the correct table

    def open_tab_create_window(self):
        self.tab_create_window = TabCreateWindow(self.tab_widget)  # Pass the QTabWidget reference
        self.tab_create_window.show()

    def clear_active_tab_database(self):
        # Get the currently selected tab's widget
        current_index = self.tab_widget.currentIndex()
        current_tab = self.tab_widget.widget(current_index)

        # Find the FileTableWidget within the current tab and clear the database
        table_widget = current_tab.findChild(FileTableWidget)
        if table_widget:
            table_widget.clear_database()

    def open_tab_edit_window(self):
        """Open the 'tab_edit' window to edit the current tab name."""
        current_index = self.tab_widget.currentIndex()  # Get the currently selected tab index
        current_tab_text = self.tab_widget.tabText(current_index)  # Get the current tab name

        self.tab_edit_window = TabEditWindow(current_tab_text, current_index, self.tab_widget)  # Create edit window
        self.tab_edit_window.exec_()  # Show the dialog



class TabCreateWindow(QtWidgets.QDialog):
    def __init__(self, tab_widget):
        super(TabCreateWindow, self).__init__()
        self.ui = Ui_Form()  # Initialize the generated form class
        self.ui.setupUi(self)  # Set up the UI
        self.tab_widget = tab_widget  # Save the reference to the main QTabWidget

        # Connect the createButton to create a new tab
        self.ui.createButton.clicked.connect(self.create_new_tab)  # Ensure createButton is correctly named
        self.ui.closeButton.clicked.connect(self.close)

    def create_new_tab(self):
        tab_name = self.ui.lineEdit.text()  # Get the text from the QLineEdit
        if tab_name:
            new_tab = QtWidgets.QWidget()  # Create a new widget for the tab
            layout = QVBoxLayout(new_tab)  # Create a layout for the tab

            # Create a new QTableWidget with a unique DB name
            unique_db_name = f"{tab_name}_data.db"  # Unique database name for each tab
            file_table_widget = FileTableWidget(new_tab, db_name=unique_db_name)
            layout.addWidget(file_table_widget)  # Add the table widget to the tab's layout

            self.tab_widget.addTab(new_tab, tab_name)  # Add the new tab with the specified name
            self.close()  # Close the tab_create window after creating the tab
        else:
            # Optional: Add error handling for empty tab name
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please enter a tab name.")


class TabEditWindow(QDialog):
    def __init__(self, current_tab_text, tab_index, tab_widget):
        super(TabEditWindow, self).__init__()
        self.ui = Ui_TabEdit()  # Assuming Ui_TabEdit is generated from your .ui file
        self.ui.setupUi(self)  # Set up the UI
        self.tab_widget = tab_widget  # Reference to the main QTabWidget
        self.current_index = tab_index

        # Set the current tab text into the line edit
        self.ui.lineEdit.setText(current_tab_text)

        # Connect buttons
        self.ui.changeButton.clicked.connect(self.change_tab_name)
        self.ui.closeButton.clicked.connect(self.close)

    def change_tab_name(self):
        new_tab_name = self.ui.lineEdit.text()  # Get new name from QLineEdit
        if new_tab_name:  # Ensure that the new name is not empty
            self.tab_widget.setTabText(self.current_index, new_tab_name)  # Change the tab name
            self.close()  # Close the edit window



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()  # Show the main application window
    sys.exit(app.exec_())
