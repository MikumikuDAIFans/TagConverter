from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QPlainTextEdit, QCheckBox, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PySide6.QtCore import QThread, Signal, QUrl, QSize, Qt
from PySide6.QtGui import QIcon, QDesktopServices
import re
import math

class ProcessingThread(QThread):
    finished = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, input_text, mode, options, precise_mode=False):
        super().__init__()
        self.input_text = input_text
        self.mode = mode
        self.options = options
        self.precise_mode = precise_mode

    def run(self):
        try:
            text = self.apply_optional_filters(self.input_text)
            
            if self.mode == 0:
                result = self.convert_nai_to_sd(text)
            else:
                result = self.convert_sd_to_nai(text)
                
            self.finished.emit(result)
        except Exception as e:
            self.error_occurred.emit(f"处理错误: {str(e)}")

    # 包含完整的预处理和转换算法实现
    def apply_optional_filters(self, text):
        # 实现所有可选预处理功能
        if self.options[0]:
            text = re.sub(r'，', ',', text)
        if self.options[1] and not self.options[2]:
            text = re.sub(r'[\u4e00-\u9fff]+', '', text)
        if self.options[2] and not self.options[1]:
            text = re.sub(r'^.*[\u4e00-\u9fff]+.*$', '\n\n\n', text, flags=re.M)
        if self.options[3]:
            text = re.sub(r',?\s*\bartist:\w+\b\s*,?', ',', text, flags=re.I)
            # 清理连续逗号和首尾逗号
            text = re.sub(r',{2,}', ',', text)
            text = re.sub(r'^,|,$', '', text)
        if self.options[4]:
            groups = (
                ' '.join(segment.strip().splitlines())
                for segment in re.split(r'\n{4,}', text.strip())
                if segment.strip()
            )
            text = '\n'.join(groups)
        if self.options[5]:
            text = text.replace('\\', '')
        if self.options[7]:
            text = re.sub(r'_', ' ', text)
        return text

    def convert_nai_to_sd(self, text):
        # 新增浮点权重处理
        def replace_float_weight(match):
            weight = float(match.group(1))
            content = match.group(2)
            
            if self.options[6]:  # 拆分复合标签
                tags = [tag.strip() for tag in content.split(',') if tag.strip()]
                return ','.join([f'({tag}:{weight:.{3 if self.precise_mode else 1}f})' for tag in tags])
            return f'({content.strip()}:{weight:.{3 if self.precise_mode else 1}f})'

        # 先处理浮点权重格式
        text = re.sub(r'(\d+\.\d+)::(.*?)::', replace_float_weight, text, flags=re.DOTALL)

        # 原有括号权重处理
        def replace_bracket_weight(match):
            left_brackets = match.group(1)
            right_brackets = match.group(3)
            content = match.group(2)
            count = max(len(left_brackets), len(right_brackets))
            weight = math.pow(1.1 if left_brackets[0] == '{' else 0.9, count)
            weight = round(weight, 3 if self.precise_mode else 1)
            
            if self.options[6]:
                tags = [tag.strip() for tag in content.split(',') if tag.strip()]
                return ','.join([f'({tag}:{weight:.{3 if self.precise_mode else 1}f})' for tag in tags])
            return f'({content.strip()}:{weight:.{3 if self.precise_mode else 1}f})'

        # 后处理括号权重
        return re.sub(r'([{\[{]+)(.*?)([]}]+)', replace_bracket_weight, text, flags=re.DOTALL)

    def convert_sd_to_nai(self, text):
        def replace_sd(match):
            content, weight = match.groups()
            weight = float(weight)
            
            # 强制向上取整计算
            if weight >= 1:
                count = math.ceil((weight - 1) / 0.1)
                return '{' * count + content + '}' * count
            else:
                count = math.ceil((1 - weight) / 0.1)
                return '[' * count + content + ']' * count

        return re.sub(r'\(([^:]+):([\d.]+)\)', replace_sd, text)

class TagConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_mode = 0
        self.options = [False]*7
        self.drag_pos = None
        self.init_ui()
        self.worker = None

    def init_ui(self):
        # 窗口基本设置
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle('Tag转换器 by Dispalce')
        self.resize(1000, 800)
        self.setWindowIcon(QIcon(r"D:\tagc\Logo_miku.ico"))

        # 自定义标题栏
        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("background-color: #2d2d2d;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)

        # 标题文字
        self.title_label = QLabel('Tag转换器')
        self.title_label.setStyleSheet("color: white; font-size: 14px;")

        # 窗口控制按钮
        btn_min = QPushButton('-')
        btn_close = QPushButton('×')
        for btn in [btn_min, btn_close]:
            btn.setFixedSize(24, 24)
            btn.setStyleSheet("""
                QPushButton {
                    color: #AAAAAA;
                    border: none;
                    font-size: 18px;
                    padding-bottom: 2px;
                }
                QPushButton:hover {
                    background-color: #333333;
                    color: white;
                    border-radius: 12px;
                }""")

        btn_min.clicked.connect(self.showMinimized)
        btn_close.clicked.connect(self.close)

        # 添加博客按钮
        self.blog_btn = QPushButton('Tag转换器 by Dispalce')
        self.blog_btn.setIcon(QIcon(r'D:\tagc\Logo_miku.ico'))
        self.blog_btn.setIconSize(QSize(36, 36))
        self.blog_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                color: white;
                border-radius: 15px;
                padding: 8px 12px;
                min-width: 120px;
                font-size: 14px;
                padding-right: 8px;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
            }
        """)
        self.blog_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://displace-github-io.vercel.app/')))

        title_layout.addWidget(self.blog_btn)
        title_layout.addStretch(1)  # 添加伸缩因子
        title_layout.addWidget(btn_min)
        btn_max = QPushButton('□')
        btn_max.setFixedSize(24, 24)
        btn_max.setStyleSheet("""
            QPushButton {
                color: #AAAAAA;
                border: none;
                font-size: 18px;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                background-color: #333333;
                color: white;
                border-radius: 12px;
            }""")
        btn_max.clicked.connect(self.toggle_fullscreen)
        title_layout.addWidget(btn_max)
        title_layout.addWidget(btn_close)
        
        # 移除标题Label的添加
        self.title_label.setStyleSheet("color: white; font-size: 14px;")

        self.setStyleSheet(r"""
            QMainWindow {
                background-color: #2D2D2D;
            }
            QCheckBox {
                color: #CCCCCC;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #444444;
                border-radius: 3px;
                background: #353535;
            }
            QCheckBox::indicator:checked {
                background: #4CAF50;
            }
            QCheckBox::indicator:unchecked:hover {
                border: 1px solid #666666;
            }
        """)
        
        # 主布局和控件初始化
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.addWidget(title_bar)  # 添加标题栏
        
        # 输入输出文本框
        self.input_text = QPlainTextEdit()
        self.output_text = QPlainTextEdit()
        self.input_text.setPlaceholderText("输入需要转换的标签...")
        self.output_text.setReadOnly(False)
        
        # 文本框样式
        text_style = r"""
            QPlainTextEdit {
                background-color: #232629;
                color: #FFFFFF;
                border: 2px solid #2196F3;
                border-radius: 8px;
                padding: 10px;
                font-size: 12pt;
            }
            QPlainTextEdit:hover {
                border: 2px solid #64B5F6;
            }
            QPlainTextEdit:focus {
                border: 2px solid #03A9F4;
            }
        """
        self.input_text.setStyleSheet(text_style)
        self.output_text.setStyleSheet(text_style)
        
        # 功能按钮区域
        button_layout = QHBoxLayout()
        self.convert_btn = QPushButton('转换')
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 24px;
                font-size: 14pt;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #666666; }
        """)
        
        # 模式切换
        mode_group = QHBoxLayout()
        self.mode_btn = QPushButton('NAI→SD模式')
        self.mode_btn.setCheckable(True)
        self.mode_btn.setStyleSheet("""
            QPushButton {
                background-color: %s;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 24px;
                font-size: 14pt;
            }
        """ % ('#4CAF50' if self.current_mode == 0 else '#2196F3'))
        self.precise_mode = QCheckBox('精确权重转换')
        mode_group.addWidget(self.mode_btn)
        mode_group.addWidget(self.precise_mode)
        # 添加GitHub爱心按钮
        self.github_btn = QPushButton('项目地址')
        self.github_btn.setIcon(QIcon(r'D:\tagc\github.ico'))
        self.github_btn.setIconSize(QSize(24, 24))
        self.github_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                color: white;
                border-radius: 15px;
                padding: 8px;
                min-width: 32px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
            }
        """)
        self.github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/MikumikuDAIFans/TagConverter')))
        mode_group.addStretch(1)
        mode_group.addWidget(self.github_btn)
        
        # 预处理选项
        options_grid = QGridLayout()
        self.option_checks = [
            QCheckBox('转换中文逗号为英文逗号'),
            QCheckBox('删除中文标签'),
            QCheckBox('将中文行替换空行'),
            QCheckBox('删除artist标签'),
            QCheckBox('压缩空行'),
            QCheckBox('移除反斜杠'),
            QCheckBox('拆分复合标签'),
            QCheckBox('替换下划线为空格')  # options[6]
        ]
        
        # 设置互斥选项
        self.option_checks[1].toggled.connect(lambda: self.option_checks[2].setChecked(False))
        self.option_checks[2].toggled.connect(lambda: self.option_checks[1].setChecked(False))
        
        # 排列选项
        for i, check in enumerate(self.option_checks):
            options_grid.addWidget(check, i//3, i%3)
        
        # 组合布局
        main_layout.addLayout(mode_group)
        main_layout.addWidget(self.input_text)
        main_layout.addLayout(options_grid)
        # 输出文本框
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(False)
        self.output_text.setStyleSheet(text_style)
        
        # 新增复制按钮
        self.copy_btn = QPushButton('复制')
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12pt;
                margin-top: 10px;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #666666; }
        """)
        
        # 输出区域布局
        output_layout = QVBoxLayout()
        output_layout.addWidget(self.output_text)
        output_layout.addWidget(self.copy_btn)
        self.copy_btn.setMinimumWidth(100)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 24px;
                font-size: 14pt;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #666666; }
        """)
        main_layout.addLayout(output_layout)
        
        # 信号连接
        self.copy_btn.clicked.connect(self.copy_output)
        button_layout.addWidget(self.convert_btn)
        main_layout.addLayout(button_layout)
        # 信号连接
        self.mode_btn.clicked.connect(self.toggle_mode)
        self.convert_btn.clicked.connect(self.start_conversion)

    def start_conversion(self):
        input_text = self.input_text.toPlainText()
        self.options = [check.isChecked() for check in self.option_checks]
        self.current_mode = 1 if self.mode_btn.isChecked() else 0
        mode_text = 'SD→NAI模式' if self.current_mode else 'NAI→SD模式'
        btn_color = '#2196F3' if self.current_mode else '#4CAF50'
        self.mode_btn.setText(mode_text)
        self.mode_btn.setStyleSheet(f'''
            QPushButton {{
                background-color: {btn_color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 24px;
                font-size: 14pt;
            }}
            QPushButton:hover {{ background-color: {btn_color[:-2]}99; }}
        ''')
        
        self.convert_btn.setEnabled(False)
        self.worker = ProcessingThread(
            input_text,
            self.current_mode,
            self.options,
            self.precise_mode.isChecked()
        )
        self.worker.finished.connect(self.update_output)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.finished.connect(lambda: self.convert_btn.setEnabled(True))
        self.worker.error_occurred.connect(lambda: self.convert_btn.setEnabled(True))
        self.worker.start()

    def update_output(self, result):
        self.output_text.setPlainText(result)
        self.convert_btn.setEnabled(True)

    def show_error(self, message):
        self.output_text.setPlainText(message)
        self.convert_btn.setEnabled(True)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.findChild(QPushButton, 'btn_max').setText('□')
        else:
            self.showFullScreen()
            self.findChild(QPushButton, 'btn_max').setText('🗖')

    def toggle_mode(self):
        self.current_mode = 1 - self.current_mode
        mode_text = 'SD→NAI模式' if self.current_mode else 'NAI→SD模式'
        btn_color = '#2196F3' if self.current_mode else '#4CAF50'
        self.mode_btn.setText(mode_text)
        self.mode_btn.setStyleSheet(f'''
            QPushButton {{
                background-color: {btn_color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 24px;
                font-size: 14pt;
            }}
            QPushButton:hover {{ background-color: {btn_color[:-2]}99; }}
        ''')
        self.precise_mode.setVisible(not self.current_mode)
        self.option_checks[6].setVisible(not self.current_mode)
        self.option_checks[7].setVisible(not self.current_mode)
        if self.current_mode:
            self.precise_mode.setChecked(False)
            self.option_checks[6].setChecked(False)
            self.option_checks[7].setChecked(False)
        self.update()

    # 窗口拖拽功能
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

    def copy_output(self):
        clipboard = QApplication.clipboard()
        output = self.output_text.toPlainText()
        if output:
            clipboard.setText(output)
        else:
            self.output_text.setPlainText("没有可复制的内容")
        self.convert_btn.setEnabled(True)

app = QApplication([])
window = TagConverterApp()
window.show()
app.exec()