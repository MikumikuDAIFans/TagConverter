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

    # 新增功能：替换含中文的行为三个换行符
    def replace_chinese_lines(text):
        # 匹配包含中文字符的行（包括中日韩统一表意文字）
        chinese_pattern = re.compile(r'^.*[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df].*$', re.MULTILINE)
        # 替换匹配行为三个换行符（创建两个空行）
        return chinese_pattern.sub('\n\n\n', text)

    # 处理中文行（在最前端执行）
    modified_text = replace_chinese_lines(input_text)

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
    intermediate = convert_brackets(modified_text)
    final_result = convert_curly_braces(intermediate)

    # 分组处理功能
    groups = re.split(r'\n{2,}', final_result.strip())
    processed_groups = [
        group.replace('\n', ' ').strip()
        for group in groups 
        if group.strip()
    ]
    final_output = '\n'.join(processed_groups)

    # 显示结果
    outputTextEdit.setPlainText(final_output)


# 绑定按钮事件
button.clicked.connect(process_text)

# 显示窗口
window.show()
app.exec()
