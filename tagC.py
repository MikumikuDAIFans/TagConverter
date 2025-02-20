from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QPlainTextEdit
import re

# 创建应用程序实例
app = QApplication([])

# 创建主窗口
window = QMainWindow()
window.resize(600, 500)
window.move(600, 400)
window.setWindowTitle('Tag转换器')
window.setWindowIcon(QIcon("D:\AI_Artwork\other\Logo_miku.ico"))
window.setStyleSheet("""
    QMainWindow {
        background-color: #2a2d32;
    }
""")

# 输入文本框
inputTextEdit = QPlainTextEdit(window)
inputTextEdit.setPlaceholderText("Nai3_Tags")
inputTextEdit.move(10, 25)
inputTextEdit.resize(450, 200)
inputTextEdit.setStyleSheet("""
    QPlainTextEdit {
        background-color: #232529;
        color: #FFFFFF;
        font-size: 14px;
        border: 1px solid #4CAF50;
        border-radius: 10px;
        padding: 5px;
    }
""")

# 输出文本框
outputTextEdit = QPlainTextEdit(window)
outputTextEdit.setPlaceholderText("SD_Tags")
outputTextEdit.setReadOnly(True)
outputTextEdit.move(10, 250)
outputTextEdit.resize(450, 200)
outputTextEdit.setStyleSheet("""
    QPlainTextEdit {
        background-color: #232529;
        color: #FFFFFF;
        font-size: 14px;
        border: 1px solid #4CAF50;
        border-radius: 10px;
        padding: 5px;
    }
""")

# 转换按钮
button = QPushButton('转换', window)
button.move(475, 150)
button.resize(100, 200)
button.setStyleSheet("""
    QPushButton {
        background-color: #34383e;
        color: #FFFFFF;
        font-size: 20px;
        border: 5px solid #00000;
        border-radius: 10px;
        padding: 5px;
    }
    QPushButton:hover {
        background-color: #333333;
    }
    QPushButton:pressed {
        background-color: #555555;
    }
""")

def process_text():
    # 获取输入文本
    input_text = inputTextEdit.toPlainText()

    # 处理中括号
    def convert_brackets(input_str):
        pattern = r'\[([^\[\]]+)\]'
        while '[' in input_str:
            input_str = re.sub(pattern, 
                lambda m: '(' + '),('.join(m.group(1).split(',')) + ')', 
                input_str)
        return input_str

    # 处理花括号
    def convert_curly_braces(input_str):
        pattern = r'\{([^\{\}]+)\}'
        while '{' in input_str:
            input_str = re.sub(pattern,
                lambda m: '[' + '],['.join(m.group(1).split(',')) + ']',
                input_str)
        return input_str

    # 执行转换
    intermediate = convert_brackets(input_text)
    final_result = convert_curly_braces(intermediate)

    # 新增分组处理功能
    # 步骤1：按两个以上换行分割段落
    groups = re.split(r'\n{2,}', final_result.strip())
    
    # 步骤2：处理每个段落
    processed_groups = []
    for group in groups:
        if group.strip():  # 过滤空段落
            # 合并段落内的换行为空格并去除首尾空格
            processed = group.replace('\n', ' ').strip()
            processed_groups.append(processed)
    
    # 步骤3：用单换行连接所有段落
    final_output = '\n'.join(processed_groups)

    # 显示结果
    outputTextEdit.setPlainText(final_output)

# 绑定按钮事件
button.clicked.connect(process_text)

# 显示窗口
window.show()
app.exec()
