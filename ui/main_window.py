import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QMessageBox
from ui.zentao_export_page import ZentaoExportPage
from ui.acceptance_filling_page import AcceptanceTestFillingPage
from ui.ExcelTool import ExcelTool
from ui.data_chart_page import ZentaoDataChartPage
from core.settings_manager import SettingsManager

class MainApplication(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XD_自动化报告生成_V1.6")
        self.setGeometry(100, 100, 900, 950)

        self.tabs = QTabWidget()
        self.settings_manager = SettingsManager()

        self._init_ui_pages()
        self._load_all_settings()

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def _init_ui_pages(self):
        """Initializes and adds all sub-pages to the tab widget."""
        self.zentao_export_page = ZentaoExportPage(self)
        self.ExcelTool = ExcelTool()
        self.data_chart_page = ZentaoDataChartPage(self)

        self.tabs.addTab(self.zentao_export_page, "禅道自动化导出")
        self.tabs.addTab(self.data_chart_page, "禅道数据表单与验收图插入")
        self.tabs.addTab(self.ExcelTool, "验收测试结果填充")

    def _load_all_settings(self):
        """Loads settings for all tabs."""
        self.zentao_export_page.load_settings()
        # self.acceptance_filling_page.load_settings()
        self.data_chart_page.load_settings()

    def closeEvent(self, event):
        """Handles the window close event."""
        is_zentao_running = self.zentao_export_page and \
                            self.zentao_export_page.worker_thread and \
                            self.zentao_export_page.worker_thread.isRunning()

        is_excel_running = self.data_chart_page and \
                           self.data_chart_page.excel_worker_thread and \
                           self.data_chart_page.excel_worker_thread.isRunning()

        if is_zentao_running or is_excel_running:
            task_name = ""
            if is_zentao_running and is_excel_running:
                task_name = "禅道自动化导出和 Excel 处理"
            elif is_zentao_running:
                task_name = "禅道自动化导出"
            elif is_excel_running:
                task_name = "Excel 处理"

            reply = QMessageBox.question(self, '退出确认',
                                         f"{task_name} 任务正在运行，确定要退出并停止任务吗？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                if is_zentao_running:
                    self.zentao_export_page._cancel_export()
                if is_excel_running:
                    # You might need to add a cancel method to ExcelWorker if it supports graceful termination
                    # For now, it will simply be terminated with the app.
                    pass
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
