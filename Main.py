import sqlite3
import sys
import os
from datetime import datetime
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QVBoxLayout, QTableWidget, QFileDialog, QTableWidgetItem, QDialog, QMessageBox
from tab_create import Ui_Form as Ui_TabCreate
from tab_edit import Ui_Form as Ui_TabEdit


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
        self.setRowCount(0)
        self.cursor.execute('SELECT filename, create_date, add_date, file_extension, size FROM files')
        rows = self.cursor.fetchall()

        for row in rows:
            if row:
                self.insertRow(self.rowCount())
                self.setItem(self.rowCount() - 1, 0, QTableWidgetItem(row[0]))
                self.setItem(self.rowCount() - 1, 1, QTableWidgetItem(row[1]))
                self.setItem(self.rowCount() - 1, 2, QTableWidgetItem(row[2]))
                self.setItem(self.rowCount() - 1, 3, QTableWidgetItem(row[3]))
                self.setItem(self.rowCount() - 1, 4, QTableWidgetItem(str(row[4])))

    def add_files_to_table(self):
        options = QFileDialog.Options()
        file_names, _ = QFileDialog.getOpenFileNames(self, "Select files", "", "All Files (*)", options=options)

        if file_names:
            for file_name in file_names:
                try:
                    if not file_name:
                        continue

                    file_size = self.get_file_size(file_name)
                    file_extension = os.path.splitext(file_name)[1]

                    base_name = os.path.basename(file_name)
                    file_name_only = os.path.splitext(base_name)[0]

                    create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    add_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    self.cursor.execute(
                        'INSERT INTO files (filename, create_date, add_date, file_extension, size) VALUES (?, ?, ?, ?, ?)',
                        (file_name_only, create_date, add_date, file_extension, file_size))
                    self.conn.commit()

                    self.add_file(file_name_only, create_date, add_date, file_extension, file_size)

                except Exception as e:
                    print(f"Error adding file '{file_name}': {e}")  # Log the error

    def add_file(self, file_name, create_date, add_date, file_extension, file_size):
        row_position = self.rowCount()
        self.insertRow(row_position)
        self.setItem(row_position, 0, QTableWidgetItem(file_name))
        self.setItem(row_position, 1, QTableWidgetItem(create_date))
        self.setItem(row_position, 2, QTableWidgetItem(add_date))
        self.setItem(row_position, 3, QTableWidgetItem(file_extension))
        self.setItem(row_position, 4, QTableWidgetItem(str(file_size)))

    def clear_database(self):
        try:
            self.cursor.execute("DELETE FROM files")
            self.conn.commit()
            self.load_data()
            print("Database cleared successfully.")
        except Exception as e:
            print(f"Error clearing the database: {e}")

    def get_file_size(self, file_name):
        return os.path.getsize(file_name)

    def close_db(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def delete_database(self):
        self.close_db()
        if os.path.exists(self.db_name):
            os.remove(self.db_name)


class MyApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyApp, self).__init__()
        uic.loadUi('main.ui', self)

        self.tab_widget = self.findChild(QtWidgets.QTabWidget, 'tabWidget')
        self.tab_widget.tabCloseRequested.connect(self.close_tab)

        self.layout = QVBoxLayout(self.tab_widget.widget(0))
        self.file_table_widget = FileTableWidget(self.tab_widget.widget(0), db_name='default_folder.db')
        self.layout.addWidget(self.file_table_widget)

        self.add_button = self.findChild(QtWidgets.QPushButton, 'fileaddButton')
        self.add_button.clicked.connect(self.add_files_to_active_table)

        self.tabcreateButton = self.findChild(QtWidgets.QPushButton, 'tabcreateButton')
        self.tabcreateButton.clicked.connect(self.open_tab_create_window)

        self.actionClear_database = self.findChild(QtWidgets.QAction, 'actionClear_database')
        self.actionClear_database.triggered.connect(self.clear_active_tab_database)

        self.tabeditButton = self.findChild(QtWidgets.QPushButton, 'tabeditButton')
        self.tabeditButton.clicked.connect(self.open_tab_edit_window)

    def add_files_to_active_table(self):
        current_index = self.tab_widget.currentIndex()
        current_tab = self.tab_widget.widget(current_index)

        table_widget = current_tab.findChild(FileTableWidget)

        if table_widget:
            table_widget.add_files_to_table()

    def open_tab_create_window(self):
        self.tab_create_window = TabCreateWindow(self.tab_widget)
        self.tab_create_window.show()

    def clear_active_tab_database(self):
        current_index = self.tab_widget.currentIndex()
        current_tab = self.tab_widget.widget(current_index)

        table_widget = current_tab.findChild(FileTableWidget)
        if table_widget:
            table_widget.clear_database()

    def open_tab_edit_window(self):
        current_index = self.tab_widget.currentIndex()
        current_tab_text = self.tab_widget.tabText(current_index)

        self.tab_edit_window = TabEditWindow(current_tab_text, current_index, self.tab_widget)
        self.tab_edit_window.exec_()

    def close_tab(self, index):
        if index < 0:
            return

        tab_widget = self.tab_widget.widget(index)

        if tab_widget:
            table_widget = tab_widget.findChild(FileTableWidget)
            if not table_widget:
                print("FileTableWidget not found.")
                return
            reply = QMessageBox.question(self, 'Confirmation',
                                         "Are you sure you want to delete this tab and its database?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    self.tab_widget.removeTab(index)
                    table_widget.delete_database()
                except Exception as e:
                    print(f"Error deleting database or removing tab: {e}")


class TabCreateWindow(QtWidgets.QDialog):
    def __init__(self, tab_widget):
        super(TabCreateWindow, self).__init__()
        self.ui = Ui_TabCreate()
        self.ui.setupUi(self)
        self.tab_widget = tab_widget

        self.ui.createButton.clicked.connect(self.create_new_tab)
        self.ui.closeButton.clicked.connect(self.close)

    def create_new_tab(self):
        tab_name = self.ui.lineEdit.text()
        if tab_name:
            new_tab = QtWidgets.QWidget()
            layout = QVBoxLayout(new_tab)

            file_table_widget = FileTableWidget(new_tab, db_name=f"{tab_name}.db")
            layout.addWidget(file_table_widget)

            self.tab_widget.addTab(new_tab, tab_name)
            self.close()
        else:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please enter a tab name.")


class TabEditWindow(QDialog):
    def __init__(self, current_tab_text, tab_index, tab_widget):
        super(TabEditWindow, self).__init__()
        self.ui = Ui_TabEdit()
        self.ui.setupUi(self)
        self.tab_widget = tab_widget
        self.current_index = tab_index

        self.ui.lineEdit.setText(current_tab_text)

        self.ui.changeButton.clicked.connect(self.change_tab_name)
        self.ui.closeButton.clicked.connect(self.close)

    def change_tab_name(self):
        new_tab_name = self.ui.lineEdit.text()
        if new_tab_name:
            self.tab_widget.setTabText(self.current_index, new_tab_name)
            self.close()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
