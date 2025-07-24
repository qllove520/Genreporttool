import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QGroupBox, QTextEdit, QFileDialog, QMessageBox,
    QGridLayout
)
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QTextCursor

from core.settings_manager import SettingsManager
from core.excel_worker import ExcelWorker # 确保导入了新的worker

class ZentaoDataChartPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_manager = SettingsManager("data_chart")
        self.excel_worker_thread = None

        self.doc1_path_input = QLineEdit()
        self.doc2_path_input = QLineEdit()
        self.doc3_path_input = QLineEdit()
        self.doc4_path_input = QLineEdit()
        self.target_report_path_input = QLineEdit()
        self.log_output = QTextEdit()

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        paths_group = QGroupBox("选择数据源和目标报告")
        paths_layout = QGridLayout()

        paths_layout.addWidget(QLabel("遗留缺陷列表 (Doc1):"), 0, 0)
        self.doc1_path_input.setPlaceholderText("请选择遗留缺陷列表.xlsx (可选)") # Add "(可选)"
        self.doc1_path_input.setReadOnly(True)
        paths_layout.addWidget(self.doc1_path_input, 0, 1)
        btn_doc1 = QPushButton("浏览...")
        btn_doc1.clicked.connect(lambda: self.select_file(self.doc1_path_input, "Excel Files (*.xlsx)"))
        paths_layout.addWidget(btn_doc1, 0, 2)

        paths_layout.addWidget(QLabel("产品需求列表 (Doc2):"), 1, 0)
        self.doc2_path_input.setPlaceholderText("请选择产品需求列表.xlsx (可选)") # Add "(可选)"
        self.doc2_path_input.setReadOnly(True)
        paths_layout.addWidget(self.doc2_path_input, 1, 1)
        btn_doc2 = QPushButton("浏览...")
        btn_doc2.clicked.connect(lambda: self.select_file(self.doc2_path_input, "Excel Files (*.xlsx)"))
        paths_layout.addWidget(btn_doc2, 1, 2)

        paths_layout.addWidget(QLabel("验收测试用例 (Doc3):"), 2, 0)
        self.doc3_path_input.setPlaceholderText("请选择验收测试用例.xlsx (可选)") # Add "(可选)"
        self.doc3_path_input.setReadOnly(True)
        paths_layout.addWidget(self.doc3_path_input, 2, 1)
        btn_doc3 = QPushButton("浏览...")
        btn_doc3.clicked.connect(lambda: self.select_file(self.doc3_path_input, "Excel Files (*.xlsx)"))
        paths_layout.addWidget(btn_doc3, 2, 2)

        paths_layout.addWidget(QLabel("设备外观图 (Doc4):"), 3, 0)
        self.doc4_path_input.setPlaceholderText("请选择设备外观图.png 或 .jpg (可选)") # Add "(可选)"
        self.doc4_path_input.setReadOnly(True)
        paths_layout.addWidget(self.doc4_path_input, 3, 1)
        btn_doc4 = QPushButton("浏览...")
        btn_doc4.clicked.connect(lambda: self.select_file(self.doc4_path_input,
                                                          "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)",
                                                          is_image=True))
        paths_layout.addWidget(btn_doc4, 3, 2)

        paths_layout.addWidget(QLabel("目标报告 (Target):"), 4, 0)
        self.target_report_path_input.setPlaceholderText("请选择目标报告.xlsx (必填)") # Indicate it's required
        self.target_report_path_input.setReadOnly(True)
        paths_layout.addWidget(self.target_report_path_input, 4, 1)
        btn_target = QPushButton("浏览...")
        btn_target.clicked.connect(
            lambda: self.select_file(self.target_report_path_input, "Excel Files (*.xlsx *.xlsm)"))
        paths_layout.addWidget(btn_target, 4, 2)

        paths_group.setLayout(paths_layout)
        main_layout.addWidget(paths_group)

        control_layout = QHBoxLayout()
        btn_consolidate = QPushButton("开始汇总数据")
        btn_consolidate.clicked.connect(self.consolidate_data)
        control_layout.addWidget(btn_consolidate)

        btn_clear_paths = QPushButton("清空所有路径")
        btn_clear_paths.clicked.connect(self.clear_all_paths)
        control_layout.addWidget(btn_clear_paths)

        main_layout.addLayout(control_layout)

        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(200)
        main_layout.addWidget(self.log_output)

    def select_file(self, line_edit_widget: QLineEdit, filter_str: str, is_image: bool = False):
        """Universal file selection method"""
        options = QFileDialog.Options()
        # Start file dialog from the current path if it exists, otherwise user's home directory
        initial_dir = os.path.dirname(line_edit_widget.text()) if os.path.exists(line_edit_widget.text()) \
                      else os.path.expanduser("~")
        file_name, _ = QFileDialog.getOpenFileName(
            self, "选择文件", initial_dir, filter_str, options=options
        )
        if file_name:
            line_edit_widget.setText(file_name)
            self.log(f"已选择文件: {os.path.basename(file_name)}")
            if is_image:
                self.log(f"  (图片文件: {os.path.basename(file_name)})")
            self.save_settings()

    def clear_all_paths(self):
        """Clears all path input fields"""
        self.doc1_path_input.clear()
        self.doc2_path_input.clear()
        self.doc3_path_input.clear()
        self.doc4_path_input.clear()
        self.target_report_path_input.clear()
        self.log_output.clear()
        self.log("所有路径已清空。", clear_prev=True)
        self.save_settings()

    def consolidate_data(self):
        """Triggers data consolidation function in a separate thread"""
        doc1_path = self.doc1_path_input.text()
        doc2_path = self.doc2_path_input.text()
        doc3_path = self.doc3_path_input.text()
        doc4_path = self.doc4_path_input.text()
        target_report_path = self.target_report_path_input.text()

        # Only target_report_path is mandatory
        if not target_report_path:
            self.log("错误: 目标报告 (Target) 文件路径不能为空！", is_error=True, clear_prev=True)
            QMessageBox.critical(self, "路径缺失", "请选择目标报告文件。")
            return
        if not os.path.exists(target_report_path):
            self.log(f"错误: 目标报告文件 '{os.path.basename(target_report_path)}' 不存在。请检查路径。", is_error=True, clear_prev=True)
            QMessageBox.critical(self, "文件不存在", "目标报告文件不存在，请检查路径。")
            return

        # Check if at least one source document (Doc1-Doc4) is provided
        if not (doc1_path or doc2_path or doc3_path or doc4_path):
            self.log("警告: 未选择任何源文档（遗留缺陷列表、产品需求列表、验收测试用例、设备外观图）。将只保存目标报告文件。", is_error=False, clear_prev=True)
            reply = QMessageBox.question(self, "未选择源文档", "您未选择任何源文档进行汇总。是否仍然继续？\n（这将只打开并保存目标报告文件，不会插入任何数据。）",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                self.log("用户取消操作。", is_error=False)
                return

        if self.excel_worker_thread and self.excel_worker_thread.isRunning():
            QMessageBox.warning(self, "操作进行中", "Excel 处理任务正在运行，请等待其完成。")
            return

        QMessageBox.information(self, "请注意", "请确保所有源文件和目标报告文件当前是关闭状态，否则可能无法进行汇总。",
                                QMessageBox.Ok)

        self.log("开始数据汇总...", clear_prev=True)
        # Assuming the button that triggered this is the "开始汇总数据" button
        self.sender().setEnabled(False) # Disable the button to prevent multiple clicks

        self.excel_worker_thread = ExcelWorker(
            doc1_path, doc2_path, doc3_path, doc4_path, target_report_path
        )
        self.excel_worker_thread.log_signal.connect(self.log)
        self.excel_worker_thread.finished_signal.connect(self._excel_process_finished)
        self.excel_worker_thread.start()

    def _excel_process_finished(self, success, message):
        """Handles the completion of the Excel processing."""
        # Find the consolidate button by object name or text if direct reference is not available
        # It's better to store a direct reference to the button in __init__ if possible
        consolidate_button = self.findChild(QPushButton, "开始汇总数据") # Assuming object name is set or default is used
        if consolidate_button:
            consolidate_button.setEnabled(True) # Re-enable the button
        else:
            # Fallback if button cannot be found by text
            for btn in self.findChildren(QPushButton):
                if btn.text() == "开始汇总数据":
                    btn.setEnabled(True)
                    break

        self.log(f"\n--- 任务完成: {'成功' if success else '失败'} ---")
        self.log(message)
        if success:
            QMessageBox.information(self, "任务完成", message)
        else:
            QMessageBox.critical(self, "任务失败", message)
        self.excel_worker_thread = None

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
            "doc1_path": self.doc1_path_input.text(),
            "doc2_path": self.doc2_path_input.text(),
            "doc3_path": self.doc3_path_input.text(),
            "doc4_path": self.doc4_path_input.text(),
            "target_report_path": self.target_report_path_input.text()
        }
        self.settings_manager.save_settings("data_chart", settings, self.log)

    def load_settings(self):
        """Loads settings specific to this tab."""
        loaded_settings = self.settings_manager.load_settings(
            "data_chart",
            default_settings={
                "doc1_path": "", "doc2_path": "", "doc3_path": "",
                "doc4_path": "", "target_report_path": ""
            },
            log_callback=self.log
        )
        self.doc1_path_input.setText(loaded_settings.get("doc1_path", ""))
        self.doc2_path_input.setText(loaded_settings.get("doc2_path", ""))
        self.doc3_path_input.setText(loaded_settings.get("doc3_path", ""))
        self.doc4_path_input.setText(loaded_settings.get("doc4_path", ""))
        self.target_report_path_input.setText(loaded_settings.get("target_report_path", ""))