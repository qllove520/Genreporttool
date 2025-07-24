import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QFileDialog, QMessageBox, QProgressDialog, QGroupBox, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor

from core.selenium_worker import SeleniumWorker
from core.settings_manager import SettingsManager
from config.settings import DOWNLOAD_DIR, HEADLESS_MODE_DEFAULT, TEST_REPORT_ID_DEFAULT # Import new settings

class ZentaoExportPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker_thread = None
        self.progress_dialog = None
        self.settings_manager = SettingsManager("zentao_export") # Specific settings file prefix

        self.init_ui()
        self.load_settings() # Load settings after UI init

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 禅道登录信息 GroupBox
        login_group_box = QGroupBox("禅道登录信息")
        login_layout = QVBoxLayout()
        self.account_input = self._create_input_field(login_layout, "账号:", "")
        self.account_input.setPlaceholderText("请输入禅道账号")
        self.password_input = self._create_input_field(login_layout, "密码:", "", is_password=True)
        self.password_input.setPlaceholderText("请输入禅道密码")

        # 新增无头模式复选框
        self.headless_checkbox = QCheckBox("无头模式 (不显示浏览器界面)")
        self.headless_checkbox.setChecked(HEADLESS_MODE_DEFAULT) # Set default from settings
        login_layout.addWidget(self.headless_checkbox)

        login_group_box.setLayout(login_layout)
        main_layout.addWidget(login_group_box)

        # 全局参数设置 GroupBox
        global_settings_group_box = QGroupBox("全局参数设置")
        global_settings_layout = QVBoxLayout()
        self.product_name_input = self._create_input_field(global_settings_layout, "产品名称:", "")
        self.product_name_input.setPlaceholderText("请输入产品名称关键字，例如\"2600F\"")

        # 新增测试单号输入框和保存按钮
        test_report_id_layout = QHBoxLayout()
        self.test_report_id_label = QLabel("测试单号:")
        self.test_report_id_input = QLineEdit(TEST_REPORT_ID_DEFAULT) # Set default from settings
        self.test_report_id_input.setPlaceholderText("请输入测试单号，例如\"11111111111\"")
        self.save_test_report_id_button = QPushButton("保存测试单号")
        self.save_test_report_id_button.clicked.connect(self._save_test_report_id)
        test_report_id_layout.addWidget(self.test_report_id_label)
        test_report_id_layout.addWidget(self.test_report_id_input)
        test_report_id_layout.addWidget(self.save_test_report_id_button)
        global_settings_layout.addLayout(test_report_id_layout)

        # 下载目录
        download_dir_layout = QHBoxLayout()
        self.download_dir_label = QLabel("下载目录:")
        self.download_dir_display = QLineEdit(DOWNLOAD_DIR)
        self.download_dir_display.setReadOnly(True)
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self._browse_download_dir)
        download_dir_layout.addWidget(self.download_dir_label)
        download_dir_layout.addWidget(self.download_dir_display)
        download_dir_layout.addWidget(self.browse_button)
        global_settings_layout.addLayout(download_dir_layout)

        global_settings_group_box.setLayout(global_settings_layout)
        main_layout.addWidget(global_settings_group_box)

        # 开始导出按钮
        button_layout = QHBoxLayout()
        self.export_button = QPushButton("开始导出")
        self.export_button.setFixedHeight(40)
        self.export_button.clicked.connect(self._start_export)
        button_layout.addWidget(self.export_button)
        main_layout.addLayout(button_layout)

        # 日志输出区域
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #f0f0f0; color: #333; font-family: 'Consolas', 'Monospace';")
        main_layout.addWidget(self.log_output)

    def _create_input_field(self, layout, label_text, default_text="", is_password=False):
        """Helper to create labeled input fields."""
        h_layout = QHBoxLayout()
        label = QLabel(label_text)
        line_edit = QLineEdit(default_text)
        if is_password:
            line_edit.setEchoMode(QLineEdit.Password)
        h_layout.addWidget(label)
        h_layout.addWidget(line_edit)
        layout.addLayout(h_layout)
        return line_edit

    def _browse_download_dir(self):
        """Opens a dialog to select the download directory."""
        initial_dir = self.download_dir_display.text()
        if not os.path.isdir(initial_dir):
            initial_dir = os.path.expanduser("~")

        directory = QFileDialog.getExistingDirectory(self, "选择下载目录", initial_dir)
        if directory:
            self.download_dir_display.setText(directory)
            self.save_settings() # Save setting immediately
            self.update_log(f"已选择下载目录: {directory}", False)

    def _save_test_report_id(self):
        """Saves the test report ID when the button is clicked."""
        self.save_settings()
        QMessageBox.information(self, "保存成功", "测试单号已保存。")
        self.update_log("测试单号已保存。", False)

    def _start_export(self):
        """Initiates the data export process in a separate thread."""
        account = self.account_input.text().strip()
        password = self.password_input.text().strip()
        product_name = self.product_name_input.text().strip()
        test_report_id = self.test_report_id_input.text().strip()
        download_dir = self.download_dir_display.text().strip()
        headless_mode = self.headless_checkbox.isChecked() # Get headless mode setting

        if not account or not password or not product_name or not download_dir:
            QMessageBox.warning(self, "输入错误", "账号、密码、产品名称和下载目录都不能为空，请填写完整。")
            return

        # 在启动任务前，尝试创建下载目录，以防用户手动输入而非通过“浏览”选择
        if not os.path.exists(download_dir):
            try:
                os.makedirs(download_dir, exist_ok=True)
                self.update_log(f"已创建下载目录: {download_dir}", False)
            except Exception as e:
                self.update_log(f"错误: 无法创建下载目录 '{download_dir}': {e}", True)
                QMessageBox.critical(self, "目录创建失败", f"无法创建下载目录，请检查权限或路径是否合法。\n错误: {e}")
                return
        elif not os.path.isdir(download_dir):
            self.update_log(f"错误: 下载目录 '{download_dir}' 存在但不是一个目录。", True)
            QMessageBox.critical(self, "路径错误", f"下载目录 '{download_dir}' 存在但不是一个目录，请重新选择。")
            return

        self.save_settings() # Save current input for product_name, test_report_id and download_dir

        self.log_output.clear()
        self.update_log("--- 开始执行自动化任务 ---", False)
        self.export_button.setEnabled(False)

        self.progress_dialog = QProgressDialog("导出进度", "取消", 0, 100, self)
        self.progress_dialog.setWindowTitle("导出进度")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setAutoReset(True)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)
        self.progress_dialog.setLabelText("正在准备...")
        self.progress_dialog.show()

        # 实例化 SeleniumWorker 时传递 test_report_id 和 headless_mode
        self.worker_thread = SeleniumWorker(account, password, product_name, test_report_id, download_dir, headless_mode)
        self.worker_thread.log_signal.connect(self.update_log)
        self.worker_thread.status_signal.connect(self.progress_dialog.setLabelText)
        self.worker_thread.finished_signal.connect(self._export_finished)
        self.worker_thread.progress_signal.connect(self.progress_dialog.setValue)
        self.progress_dialog.canceled.connect(self._cancel_export)
        self.worker_thread.start()

    def _export_finished(self, success, message):
        """Handles the completion of the export process."""
        self.export_button.setEnabled(True)
        if self.progress_dialog:
            self.progress_dialog.hide()

        self.update_log(f"\n--- 任务完成: {'成功' if success else '失败'} ---", False)
        self.update_log(message, not success)
        if success:
            QMessageBox.information(self, "任务完成", message)
        else:
            QMessageBox.critical(self, "任务失败", message)
        self.worker_thread = None

    def _cancel_export(self):
        """Handles cancellation of the export process."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.update_log("用户请求取消任务 (此版本暂不支持中断正在进行的Selenium操作)...", True)

            if self.progress_dialog:
                self.progress_dialog.hide()

            self.export_button.setEnabled(True)
            QMessageBox.information(self, "任务取消", "导出任务已请求取消。请等待当前Selenium操作结束。")
        else:
            self.update_log("没有正在运行的任务可以取消。", False)


    def update_log(self, message, is_error=False):
        """Appends a message to the log QTextEdit."""
        cursor = self.log_output.textCursor()
        format = cursor.charFormat()
        if is_error:
            format.setForeground(Qt.red)
        else:
            format.setForeground(Qt.black)
        cursor.setCharFormat(format)
        self.log_output.append(message)
        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_output.setTextCursor(cursor)

    def save_settings(self):
        """Saves settings specific to this tab."""
        settings = {
            "account": self.account_input.text(),
            "password": self.password_input.text(),  #
            "product_name": self.product_name_input.text(),
            "test_report_id": self.test_report_id_input.text(), # Save test report ID
            "download_dir": self.download_dir_display.text(),
            "headless_mode": self.headless_checkbox.isChecked() # Save headless mode setting
        }
        self.settings_manager.save_settings("zentao_export", settings, self.update_log)

    def load_settings(self):
        """Loads settings specific to this tab."""
        default_settings = {
            "account": "",
            "password": "",
            "product_name": "",
            "test_report_id": TEST_REPORT_ID_DEFAULT, # Default for new test report ID from settings.py
            "download_dir": DOWNLOAD_DIR, # Default download directory from settings.py
            "headless_mode": HEADLESS_MODE_DEFAULT # Default headless mode from settings.py
        }
        loaded_settings = self.settings_manager.load_settings(
            "zentao_export",
            default_settings=default_settings,
            log_callback=self.update_log
        )
        self.product_name_input.setText(loaded_settings.get("product_name", ""))
        self.test_report_id_input.setText(loaded_settings.get("test_report_id", TEST_REPORT_ID_DEFAULT))
        self.download_dir_display.setText(loaded_settings.get("download_dir", DOWNLOAD_DIR))
        self.headless_checkbox.setChecked(loaded_settings.get("headless_mode", HEADLESS_MODE_DEFAULT))

        self.account_input.setText("")
        self.password_input.setText("")

        # 确保默认下载目录存在
        initial_download_dir = self.download_dir_display.text()
        if initial_download_dir and not os.path.exists(initial_download_dir):
            try:
                os.makedirs(initial_download_dir, exist_ok=True)
                self.update_log(f"已创建默认下载目录: {initial_download_dir}", False)
            except Exception as e:
                self.update_log(f"警告: 无法创建默认下载目录 '{initial_download_dir}': {e}", True)
                self.download_dir_display.setText(os.path.expanduser("~"))