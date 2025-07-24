# core/excel_worker.py
from PyQt5.QtCore import QThread, pyqtSignal
import traceback
from core.excel_utils import consolidate_excel_data_and_insert_chart

class ExcelWorker(QThread):
    log_signal = pyqtSignal(str, bool)  # message, is_error
    finished_signal = pyqtSignal(bool, str) # success, message

    def __init__(self, doc1_path, doc2_path, doc3_path, doc4_path, target_report_path):
        super().__init__()
        self.doc1_path = doc1_path
        self.doc2_path = doc2_path
        self.doc3_path = doc3_path
        self.doc4_path = doc4_path
        self.target_report_path = target_report_path

    def run(self):
        try:
            self.log_signal.emit("开始 Excel 数据汇总及图片插入...", False)
            success = consolidate_excel_data_and_insert_chart(
                self.doc1_path,
                self.doc2_path,
                self.doc3_path,
                self.doc4_path,
                self.target_report_path,
                log_callback=lambda msg, is_err=False: self.log_signal.emit(msg, is_err)
            )
            if success:
                self.finished_signal.emit(True, "数据汇总和图片插入成功！")
            else:
                self.finished_signal.emit(False, "数据汇总或图片插入失败，请查看日志。")
        except Exception as e:
            self.log_signal.emit(f"Excel 处理任务异常: {e}", True)
            self.log_signal.emit(traceback.format_exc(), True)
            self.finished_signal.emit(False, f"Excel 处理任务异常: {e}")