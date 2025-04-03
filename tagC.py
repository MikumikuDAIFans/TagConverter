from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QPlainTextEdit, QCheckBox, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QSizePolicy
from PySide6.QtCore import QThread, Signal, QUrl, QSize, Qt
from PySide6.QtGui import QIcon, QDesktopServices
import re
import math

# 标签处理线程类，用于异步处理标签转换操作
class ProcessingThread(QThread):
    # 定义信号：转换完成信号和错误发生信号
    finished = Signal(str)  # 转换完成时发送结果文本
    error_occurred = Signal(str)  # 发生错误时发送错误信息

    def __init__(self, input_text, mode, options, precise_mode=False):
        """初始化处理线程
        Args:
            input_text (str): 需要转换的输入文本
            mode (int): 转换模式，0表示NAI→SD，1表示SD→NAI
            options (list): 预处理选项列表
            precise_mode (bool): 是否使用精确权重模式，默认False
        """
        super().__init__()
        self.input_text = input_text
        self.mode = mode
        self.options = options
        self.precise_mode = precise_mode

    def run(self):
        """线程执行函数，处理标签转换"""
        try:
            # 应用预处理过滤器
            text = self.apply_optional_filters(self.input_text)
            
            # 根据模式选择转换方向
            if self.mode == 0:
                result = self.convert_nai_to_sd(text)
            else:
                result = self.convert_sd_to_nai(text)
                
            self.finished.emit(result)
        except Exception as e:
            self.error_occurred.emit(f"处理错误: {str(e)}")

    def apply_optional_filters(self, text):
        """应用可选的预处理过滤器
        Args:
            text (str): 输入文本
        Returns:
            str: 处理后的文本
        """
        # 转换中文逗号为英文逗号
        if self.options[0]:
            text = re.sub(r'，', ',', text)
        # 删除中文标签（与中文行替换为空行互斥）
        if self.options[1] and not self.options[2]:
            text = re.sub(r'[\u4e00-\u9fff]+', '', text)
        # 将中文行替换为空行（与删除中文标签互斥）
        if self.options[2] and not self.options[1]:
            text = re.sub(r'^.*[\u4e00-\u9fff]+.*$', '\n\n\n', text, flags=re.M)
        # 删除artist标签
        if self.options[3]:
            text = re.sub(r',?\s*\bartist:\w+\b\s*,?', ',', text, flags=re.I)
            # 清理连续逗号和首尾逗号
            text = re.sub(r',{2,}', ',', text)
            text = re.sub(r'^,|,$', '', text)
        # 压缩空行
        if self.options[4]:
            groups = (
                ' '.join(segment.strip().splitlines())
                for segment in re.split(r'\n{4,}', text.strip())
                if segment.strip()
            )
            text = '\n'.join(groups)
        # 移除反斜杠
        if self.options[5]:
            text = text.replace('\\', '')
        # 替换下划线为空格
        if self.options[7]:
            text = re.sub(r'_', ' ', text)
        return text

    def convert_nai_to_sd(self, text):
        """将NAI格式标签转换为SD格式
        Args:
            text (str): NAI格式的标签文本
        Returns:
            str: 转换后的SD格式标签文本
        """
        # 处理浮点权重格式（例如：1.2::tag::）
        def replace_float_weight(match):
            weight = float(match.group(1))
            content = match.group(2)
            
            # 如果启用拆分复合标签选项
            if self.options[6]:
                tags = [tag.strip() for tag in content.split(',') if tag.strip()]
                return ','.join([f'({tag}:{weight:.{3 if self.precise_mode else 1}f})' for tag in tags])
            return f'({content.strip()}:{weight:.{3 if self.precise_mode else 1}f})'

        # 处理括号权重格式（例如：{{tag}}或[[tag]]）
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

        # 先处理浮点权重格式，再处理括号权重格式
        text = re.sub(r'(\d+\.\d+)::(.*?)::', replace_float_weight, text, flags=re.DOTALL)
        return re.sub(r'([{\[{]+)(.*?)([]}]+)', replace_bracket_weight, text, flags=re.DOTALL)

    def convert_sd_to_nai(self, text):
        """将SD格式标签转换为NAI格式
        Args:
            text (str): SD格式的标签文本
        Returns:
            str: 转换后的NAI格式标签文本
        """
        def replace_sd(match):
            content, weight = match.groups()
            weight = float(weight)
            
            # 根据权重值选择使用花括号或方括号，并计算嵌套层数
            if weight >= 1:
                count = math.ceil((weight - 1) / 0.1)
                return '{' * count + content + '}' * count
            else:
                count = math.ceil((1 - weight) / 0.1)
                return '[' * count + content + ']' * count

        return re.sub(r'\(([^:]+):([\d.]+)\)', replace_sd, text)

# 标签转换器主窗口类
class TagConverterApp(QMainWindow):
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        self.current_mode = 0  # 当前转换模式：0为NAI→SD，1为SD→NAI
        self.options = [False]*7  # 预处理选项状态
        self.drag_pos = None  # 窗口拖拽位置
        self.init_ui()  # 初始化用户界面
        self.worker = None  # 处理线程

    def init_ui(self):
        """初始化用户界面"""
        # 设置无边框窗口
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle('Tag转换器 by Dispalce')
        self.resize(1000, 800)
        self.setWindowIcon(QIcon(r"D:\tagc\Logo_miku.ico"))

        # 创建自定义标题栏
        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("background-color: #2d2d2d;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)

        # 设置标题文字
        self.title_label = QLabel('Tag转换器')
        self.title_label.setStyleSheet("color: white; font-size: 14px;")

        # 创建窗口控制按钮（最小化、最大化、关闭）
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
                }"""
            )

        # 绑定窗口控制按钮事件
        btn_min.clicked.connect(self.showMinimized)
        btn_close.clicked.connect(self.close)

        # 创建博客链接按钮
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

        # 组织标题栏布局
        title_layout.addWidget(self.blog_btn)
        title_layout.addStretch(1)
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
            }"""
        )
        btn_max.clicked.connect(self.toggle_fullscreen)
        title_layout.addWidget(btn_max)
        title_layout.addWidget(btn_close)
        
        # 设置标题标签样式
        self.title_label.setStyleSheet("color: white; font-size: 14px;")

        # 设置主窗口样式
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
        
        # 创建主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.addWidget(title_bar)
        
        # 创建输入输出文本框
        self.input_text = QPlainTextEdit()
        self.output_text = QPlainTextEdit()
        self.input_text.setPlaceholderText("输入需要转换的标签...")
        self.output_text.setReadOnly(False)
        
        # 创建输入框操作按钮
        # 创建输入框操作按钮
        input_buttons_layout = QHBoxLayout()
        self.paste_btn = QPushButton('粘贴到输入')
        self.clear_btn = QPushButton('清空输入')
        
        # 设置按钮样式
        self.paste_btn.setStyleSheet("""
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
        self.clear_btn.setStyleSheet("""
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
        
        for btn in [self.paste_btn, self.clear_btn]:
            btn.setFixedHeight(50)  # 设置固定高度
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 设置大小策略为水平扩展

        input_buttons_layout.addWidget(self.paste_btn)
        input_buttons_layout.addWidget(self.clear_btn)
        
        # 设置文本框样式
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
        
        # 创建功能按钮区域
        button_layout = QHBoxLayout()
        self.convert_btn = QPushButton('转换Tags')
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
        self.copy_btn = QPushButton('复制输出')
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
        button_layout.addWidget(self.convert_btn)
        button_layout.addWidget(self.copy_btn)
        
        # 创建模式切换区域
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

        # 创建GitHub项目链接按钮
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
        
        # 创建预处理选项
        options_grid = QGridLayout()
        self.option_checks = [
            QCheckBox('转换中文逗号为英文逗号'),
            QCheckBox('删除中文标签'),
            QCheckBox('将中文行替换空行'),
            QCheckBox('删除artist标签'),
            QCheckBox('压缩空行'),
            QCheckBox('移除反斜杠'),
            QCheckBox('拆分复合标签'),
            QCheckBox('替换下划线为空格')
        ]
        
        # 设置互斥选项
        self.option_checks[1].toggled.connect(lambda: self.option_checks[2].setChecked(False))
        self.option_checks[2].toggled.connect(lambda: self.option_checks[1].setChecked(False))
        
        # 排列选项布局
        for i, check in enumerate(self.option_checks):
            options_grid.addWidget(check, i//3, i%3)
        
        # 组合主布局
        main_layout.addLayout(mode_group)
        main_layout.addWidget(self.input_text)
        main_layout.addLayout(input_buttons_layout)
        main_layout.addLayout(options_grid)

        # 创建输出区域布局
        output_layout = QVBoxLayout()
        main_layout.addLayout(button_layout)  # 将按钮布局添加到输出框上方
        output_layout.addWidget(self.output_text)
        main_layout.addLayout(output_layout)
        
        # 绑定按钮事件
        self.copy_btn.clicked.connect(self.copy_output)
        self.mode_btn.clicked.connect(self.toggle_mode)
        self.convert_btn.clicked.connect(self.start_conversion)
        self.paste_btn.clicked.connect(self.paste_input)
        self.clear_btn.clicked.connect(self.clear_input)

    def start_conversion(self):
        """开始转换处理"""
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
        
        # 禁用转换按钮并启动处理线程
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
        """更新输出文本框内容
        Args:
            result (str): 转换结果文本
        """
        self.output_text.setPlainText(result)
        self.convert_btn.setEnabled(True)

    def show_error(self, message):
        """显示错误信息
        Args:
            message (str): 错误信息
        """
        self.output_text.setPlainText(message)
        self.convert_btn.setEnabled(True)

    def toggle_fullscreen(self):
        """切换全屏模式"""
        if self.isFullScreen():
            self.showNormal()
            self.findChild(QPushButton, 'btn_max').setText('□')
        else:
            self.showFullScreen()
            self.findChild(QPushButton, 'btn_max').setText('🗖')

    def toggle_mode(self):
        """切换转换模式"""
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

    def mousePressEvent(self, event):
        """鼠标按下事件处理
        Args:
            event: 鼠标事件对象
        """
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动事件处理
        Args:
            event: 鼠标事件对象
        """
        if event.buttons() == Qt.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件处理
        Args:
            event: 鼠标事件对象
        """
        self.drag_pos = None

    def copy_output(self):
        """复制输出文本到剪贴板"""
        clipboard = QApplication.clipboard()
        output = self.output_text.toPlainText()
        if output:
            clipboard.setText(output)
        else:
            self.output_text.setPlainText("没有可复制的内容")
        self.convert_btn.setEnabled(True)

    def paste_input(self):
        """从剪贴板粘贴文本到输入框"""
        clipboard = QApplication.clipboard()
        self.input_text.setPlainText(clipboard.text())

    def clear_input(self):
        """清空输入框文本"""
        self.input_text.clear()

app = QApplication([])
window = TagConverterApp()
window.show()
app.exec()