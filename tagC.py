from PySide6.QtGui import QIcon  # 导入 QIcon 类
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QPlainTextEdit
import re  # 导入正则表达式库，用于删除数字

# 创建应用程序实例
app = QApplication([])

# 创建主窗口
window = QMainWindow()
window.resize(600, 500)  # 设置窗口大小
window.move(600, 400)  # 设置窗口位置
window.setWindowTitle('Tag转换器')  # 设置窗口标题
# 设置窗口图标
window.setWindowIcon(QIcon("D:\AI_AartWork\miku_logo\logo_Rabbitmiku.ico"))  # 替换为你的图标文件路径

# 设置窗口的样式
window.setStyleSheet("""
    QMainWindow {
        background-color: #2a2d32; /* 窗口背景色为黑色 */
    }
""")

# 创建输入文本框
inputTextEdit = QPlainTextEdit(window)
inputTextEdit.setPlaceholderText("Nai3_Tags")
inputTextEdit.move(10, 25)  # 设置位置
inputTextEdit.resize(450, 200)  # 设置大小

# 设置输入文本框样式
inputTextEdit.setStyleSheet("""
    QPlainTextEdit {
        background-color: #232529; /* 背景色为黑色 */
        color: #FFFFFF;           /* 字体颜色为白色 */
        font-size: 14px;          /* 字体大小 */
        border: 1px solid #4CAF50; /* 边框颜色为绿色 */
        border-radius: 10px;      /* 圆角边框 */
        padding: 5px;             /* 内边距 */        
    }
""")

# 创建输出文本框
outputTextEdit = QPlainTextEdit(window)
outputTextEdit.setPlaceholderText("SD_Tags")
outputTextEdit.setReadOnly(True)  # 设置为只读
outputTextEdit.move(10, 250)  # 设置位置
outputTextEdit.resize(450, 200)  # 设置大小

# 设置输出文本框样式
outputTextEdit.setStyleSheet("""
    QPlainTextEdit {
        background-color: #232529; /* 背景色为黑色 */
        color: #FFFFFF;           /* 字体颜色为白色 */
        font-size: 14px;          /* 字体大小 */
        border: 1px solid #4CAF50; /* 边框颜色为绿色 */
        border-radius: 10px;      /* 圆角边框 */
        padding: 5px;             /* 内边距 */
    }
""")

# 创建按钮
button = QPushButton('转换', window)
button.move(475, 150)  # 设置按钮位置
button.resize(100, 200)  # 设置按钮大小

# 设置按钮样式
button.setStyleSheet("""
    QPushButton {
        background-color: #34383e; /* 按钮背景色为黑色 */
        color: #FFFFFF;           /* 按钮文字颜色为白色 */
        font-size: 20px;          /* 按钮文字大小 */
        border: 5px solid #00000; /* 按钮边框颜色为绿色 */
        border-radius: 10px;      /* 圆角边框 */
        padding: 5px;             /* 内边距 */
    }
    QPushButton:hover {
        background-color: #333333; /* 鼠标悬停时的背景色为深灰色 */
    }
    QPushButton:pressed {
        background-color: #555555; /* 按下时的背景色为更深的灰色 */
    }
""")

# 定义按钮点击事件处理函数
def process_text():
    # 获取输入文本框内容
    input_text = inputTextEdit.toPlainText()

    # 定义递归函数来处理嵌套的中括号
    def convert_brackets(input_str):
        # 通过正则表达式匹配最内层中括号中的内容
        pattern = r'\[([^\[\]]+)\]'  # 匹配最内层的中括号
        while '[' in input_str and ']' in input_str:
            input_str = re.sub(pattern, lambda m: '(' + '),('.join(m.group(1).split(',')) + ')', input_str)
        return input_str

    # 定义递归函数来处理嵌套的花括号
    def convert_curly_braces(input_str):
        # 匹配最内层花括号中的内容
        pattern = r'\{([^\{\}]+)\}'  # 匹配最内层的花括号
        while '{' in input_str and '}' in input_str:
            input_str = re.sub(pattern, lambda m: '[' + '],['.join(m.group(1).split(',')) + ']', input_str)
        return input_str

    # 先处理中括号，再处理花括号
    intermediate_result = convert_brackets(input_text)
    final_result = convert_curly_braces(intermediate_result)

    # 将最终结果显示到输出文本框
    outputTextEdit.setPlainText(final_result)

# 绑定按钮点击事件到处理函数
button.clicked.connect(process_text)

# 显示窗口
window.show()

# 执行应用程序
app.exec()
