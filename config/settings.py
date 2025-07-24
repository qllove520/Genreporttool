# config/settings.py
import os

# 定义默认下载目录为程序运行目录下的 'raw_data'
# 确保在 main.py 中将当前工作目录设置为脚本所在目录，以保证相对路径正确
DOWNLOAD_DIR = os.path.join(os.getcwd(), "raw_data")

# 禅道URL基地址
ZEN_TAO_BASE_URL = "http://10.200.10.220/zentao" # **请务必根据您的实际禅道URL修改此项**

# Edge WebDriver 的路径
# 请将 msedgedriver.exe 放在项目根目录，或者在此处指定其完整路径
# 确保 msedgedriver 的版本与您的 Edge 浏览器版本兼容
EDGEDRIVER_PATH = None
# 如果 msedgedriver.exe 不在项目根目录，请提供完整路径，例如：
# EDGEDRIVER_PATH = "C:\\path\\to\\your\\msedgedriver.exe"

# 默认无头模式设置 (True: 默认无头，不显示浏览器界面；False: 默认有头，显示浏览器界面)
HEADLESS_MODE_DEFAULT = True # 默认勾选无头模式

# 默认测试单号 (如果settings.json中没有保存，则使用此默认值)
TEST_REPORT_ID_DEFAULT = None# 截图中的默认值

FIELD_MAPPING_EXCEL_AND_UI = {
    "测试依据": {"excel_cell": "E6", "ui_row_col": (1, 0), "colspan": 5},
    "测试范围": {"excel_cell": "E7", "ui_row_col": (2, 0), "colspan": 5},
}

EXCEL_SHEET_NAME_ACCEPTANCE = "验收测试结果"