import os
import json # Only for settings management of nested dict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QGroupBox, QTextEdit, QFileDialog, QMessageBox,
    QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor

from config.settings import FIELD_MAPPING_EXCEL_AND_UI, EXCEL_SHEET_NAME_ACCEPTANCE
from core.settings_manager import SettingsManager
from core.excel_utils import fill_excel_template_acceptance

class AcceptanceTestFillingPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.excel_template_path = ""
        self.input_widgets = {}
        self.settings_manager = SettingsManager("acceptance_filling")

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        excel_selection_group = QGroupBox("选择 Excel 模板文件")
        excel_layout = QHBoxLayout()
        self.excel_path_input = QLineEdit()
        self.excel_path_input.setPlaceholderText("请选择要填充的 Excel 模板文件...")
        self.excel_path_input.setReadOnly(True)
        excel_layout.addWidget(self.excel_path_input)

        select_excel_button = QPushButton("浏览...")
        select_excel_button.clicked.connect(self.select_excel_template)
        excel_layout.addWidget(select_excel_button)

        excel_selection_group.setLayout(excel_layout)
        main_layout.addWidget(excel_selection_group)

        input_group = QGroupBox("请手动填写数据")
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content_widget = QWidget()
        self.fields_grid_layout = QGridLayout(scroll_content_widget)
        self.fields_grid_layout.setHorizontalSpacing(15)
        self.fields_grid_layout.setVerticalSpacing(10)

        self._create_field_widgets()

        scroll_area.setWidget(scroll_content_widget)
        main_layout.addWidget(scroll_area)

        button_layout = QHBoxLayout()
        clear_button = QPushButton("清空所有输入")
        clear_button.clicked.connect(self.clear_all_inputs)
        button_layout.addWidget(clear_button)

        confirm_button = QPushButton("确认并填写 Excel")
        confirm_button.clicked.connect(self.confirm_and_fill_excel)
        button_layout.addWidget(confirm_button)

        main_layout.addLayout(button_layout)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(150)
        main_layout.addWidget(self.log_output)

    def _create_field_widgets(self):
        """Dynamically creates and lays out QLabel and QLineEdit for all fields in QGridLayout"""
        for field_name, config in FIELD_MAPPING_EXCEL_AND_UI.items():
            print(f'--------horst--11111111111--field_name:{field_name}- config:{config}--')
            row, col = config["ui_row_col"]
            print(config["ui_row_col"])
            print(f'--------horst--22222222222--row:{row}- col:{col}--')
            label = QLabel(f"{field_name}:")
            label.setFixedWidth(80)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            line_edit = QLineEdit()
            line_edit.setFixedWidth(150)

            if "colspan" in config and config["colspan"] > 1:
                self.fields_grid_layout.addWidget(label, row, col)
                self.fields_grid_layout.addWidget(line_edit, row, col + 1, 1, config["colspan"] - 1)
            else:
                self.fields_grid_layout.addWidget(label, row, col)
                self.fields_grid_layout.addWidget(line_edit, row, col + 1)

            self.input_widgets[field_name] = line_edit

    def select_excel_template(self):
        """Opens file dialog to select Excel template file"""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "选择 Excel 模板", "", "Excel Files (*.xlsx *.xlsm);;All Files (*)", options=options
        )
        if file_name:
            self.excel_template_path = file_name
            self.excel_path_input.setText(file_name)
            self.log("Excel 模板文件已选择。", clear_prev=True)
            self.save_settings()

    def clear_all_inputs(self):
        """Clears content of all input fields"""
        for line_edit in self.input_widgets.values():
            line_edit.clear()
        self.log("所有输入已清空。", clear_prev=True)
        self.save_settings()

    def confirm_and_fill_excel(self):
        """Triggered by confirm button, gets data from UI and fills Excel"""
        if not self.excel_template_path:
            self.log("错误: 请先选择一个 Excel 模板文件！", is_error=True, clear_prev=True)
            return

        QMessageBox.information(self, "请注意", "请确保您要填充的 Excel 模板文件当前是关闭状态，否则可能无法保存。",
                                QMessageBox.Ok)

        self.log(f"正在从界面获取数据并填充 Excel 表单...", clear_prev=True)

        entered_data = {}
        for field_name, line_edit in self.input_widgets.items():
            entered_data[field_name] = line_edit.text().strip()

        success = fill_excel_template_acceptance(
            self.excel_template_path, entered_data, FIELD_MAPPING_EXCEL_AND_UI,
            EXCEL_SHEET_NAME_ACCEPTANCE, self.log
        )
        if not success:
            QMessageBox.critical(self, "操作失败", "填充 Excel 失败，请查看日志获取详情。")
        self.save_settings()

    def log(self, message: str, is_error: bool = False, clear_prev: bool = False):
        """Displays plain text messages in the log output area, without icons"""
        if clear_prev:
            self.log_output.clear()

        cursor = self.log_output.textCursor()
        format = cursor.charFormat()
        if is_error:
            format.setForeground(Qt.red)
        else:
            format.setForeground(Qt.black)
        cursor.setCharFormat(format)

        self.log_output.append(message)
        self.log_output.ensureCursorVisible()

    def save_settings(self):
        """Saves settings specific to this tab."""
        settings = {
            "excel_template_path": self.excel_path_input.text(),
            "input_data": {k: v.text() for k, v in self.input_widgets.items()}
        }
        self.settings_manager.save_settings("acceptance_filling", settings, self.log)

    def load_settings(self):
        """Loads settings specific to this tab."""
        loaded_settings = self.settings_manager.load_settings(
            "acceptance_filling",
            default_settings={"excel_template_path": "", "input_data": {}},
            log_callback=self.log
        )
        excel_path = loaded_settings.get("excel_template_path", "")
        self.excel_template_path = excel_path
        self.excel_path_input.setText(excel_path)

        loaded_input_data = loaded_settings.get("input_data", {})
        for field_name, line_edit in self.input_widgets.items():
            line_edit.setText(loaded_input_data.get(field_name, ""))