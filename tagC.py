from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QMainWindow, 
                              QPushButton, QPlainTextEdit)
from PySide6.QtCore import QThread, Signal
import re

class ProcessingThread(QThread):
    finished = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, input_text):
        super().__init__()
        self.input_text = input_text

    def run(self):
        try:
            # 第一阶段：中文行处理
            text = re.sub(
                r'^.*[\u4E00-\u9FFF\u3400-\u4DBF\uF900-\uFAFF].*$', 
                '\n\n\n', 
                self.input_text, 
                flags=re.MULTILINE
            )

            # 第二阶段：括号转换优化
            # 中括号处理
            bracket_pattern = re.compile(r'\[([^][]*)]')
            prev_text = ""
            while text != prev_text:
                prev_text = text
                text = bracket_pattern.sub(
                    lambda m: '(' + '),('.join(
                        s.strip() for s in m.group(1).split(',')
                    ) + ')',
                    text
                )

            # 花括号处理
            brace_pattern = re.compile(r'\{([^{}]*)}')
            prev_text = ""
            while text != prev_text:
                prev_text = text
                text = brace_pattern.sub(
                    lambda m: '[' + '],['.join(
                        s.strip() for s in m.group(1).split(',')
                    ) + ']',
                    text
                )

            # 第三阶段：分组处理优化
            groups = (
                ' '.join(segment.strip().splitlines())
                for segment in re.split(r'\n{2,}', text.strip())
                if segment.strip()
            )
            result = '\n'.join(groups)

            self.finished.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(f"处理错误: {str(e)}")

class TagConverterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.worker = None

    def init_ui(self):
        # 窗口设置
        self.setWindowTitle('Tag转换器 (优化版)')
        self.resize(600, 500)
        self.move(600, 400)
        self.setWindowIcon(QIcon(r"D:\AI_Artwork\other\Logo_miku.ico"))
        self.setStyleSheet("QMainWindow { background-color: #2a2d32; }")

        # 输入文本框
        self.inputTextEdit = QPlainTextEdit(self)
        self.inputTextEdit.setPlaceholderText("输入文本...")
        self.inputTextEdit.setGeometry(10, 25, 450, 200)
        self.inputTextEdit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #232529;
                color: #FFFFFF;
                border: 1px solid #4CAF50;
                border-radius: 10px;
                padding: 5px;
                font-size: 14px;
            }
        """)

        # 输出文本框
        self.outputTextEdit = QPlainTextEdit(self)
        self.outputTextEdit.setReadOnly(True)
        self.outputTextEdit.setPlaceholderText("处理结果...")
        self.outputTextEdit.setGeometry(10, 250, 450, 200)
        self.outputTextEdit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #232529;
                color: #FFFFFF;
                border: 1px solid #4CAF50;
                border-radius: 10px;
                padding: 5px;
                font-size: 14px;
            }
        """)

        # 转换按钮
        self.convertBtn = QPushButton('转换', self)
        self.convertBtn.setGeometry(475, 150, 100, 200)
        self.convertBtn.setStyleSheet("""
            QPushButton {
                background-color: #34383e;
                color: #FFFFFF;
                font-size: 20px;
                border: 5px solid #000000;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover { background-color: #333333; }
            QPushButton:pressed { background-color: #555555; }
            QPushButton:disabled { background-color: #454545; }
        """)
        self.convertBtn.clicked.connect(self.start_processing)

    def start_processing(self):
        if self.worker and self.worker.isRunning():
            return

        input_text = self.inputTextEdit.toPlainText()
        if not input_text.strip():
            return

        # 更新按钮状态
        self.convertBtn.setEnabled(False)
        self.convertBtn.setText("处理中...")

        # 创建并启动工作线程
        self.worker = ProcessingThread(input_text)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error_occurred.connect(self.on_processing_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error_occurred.connect(self.worker.deleteLater)
        self.worker.start()

    def on_processing_finished(self, result):
        self.outputTextEdit.setPlainText(result)
        self.convertBtn.setEnabled(True)
        self.convertBtn.setText("转换")

    def on_processing_error(self, error_msg):
        self.outputTextEdit.setPlainText(error_msg)
        self.convertBtn.setEnabled(True)
        self.convertBtn.setText("转换")

if __name__ == "__main__":
    app = QApplication([])
    window = TagConverterWindow()
    window.show()
    app.exec()
