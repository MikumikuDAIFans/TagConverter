
import sys, os
from PySide6.QtWidgets import QSizeGrip
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import QPoint

# 兼容 PyInstaller 的资源路径获取函数
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

# 拖拽方形自定义控件，集成到主文件
class DragDropBox(QWidget):
    """
    一个自定义的倒角正方形拖拽区域，中心有十字，可接收文件拖入。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFixedSize(96, 96)
        self.setToolTip('拖入文本文件以导入内容')
        self.bg_color = QColor(35, 38, 41)  # 与界面风格一致
        self.border_color = QColor(68, 68, 68)
        self.cross_color = QColor(120, 180, 255)
        self._highlight = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        r = 12  # 倒角半径
        rect = self.rect()
        # 绘制倒角正方形
        painter.setBrush(self.bg_color)
        painter.setPen(QPen(self.border_color, 2))
        painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), r, r)
        # 绘制中心十字
        painter.setPen(QPen(self.cross_color, 3))
        cx, cy = rect.center().x(), rect.center().y()
        cross_len = 18
        painter.drawLine(cx - cross_len//2, cy, cx + cross_len//2, cy)
        painter.drawLine(cx, cy - cross_len//2, cx, cy + cross_len//2)

    def dragEnterEvent(self, event):
        text_exts = ('.txt', '.md', '.csv', '.log', '.json', '.xml', '.ini', '.yaml', '.yml', '.py', '.js', '.html', '.css')
        img_exts = ('.png',)
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                f = url.toLocalFile().lower()
                if f.endswith(text_exts) or f.endswith(img_exts):
                    self._highlight = True
                    self.update()
                    event.acceptProposedAction()
                    return
        event.ignore()
    def dragLeaveEvent(self, event):
        self._highlight = False
        self.update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._highlight = False
        self.update()
        import os
        text_exts = ('.txt', '.md', '.csv', '.log', '.json', '.xml', '.ini', '.yaml', '.yml', '.py', '.js', '.html', '.css')
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            content = None
            if file_path.lower().endswith(text_exts):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    content = f"读取文件失败: {e}"
            elif file_path.lower().endswith('.png'):
                try:
                    # 直接集成image_info.py算法
                    import struct
                    def extract_png_text_chunks(filename):
                        def read_chunk(f):
                            length_bytes = f.read(4)
                            if len(length_bytes) < 4:
                                return None, None, None
                            length = struct.unpack(">I", length_bytes)[0]
                            chunk_type = f.read(4)
                            data = f.read(length)
                            crc = f.read(4)
                            return chunk_type, data, crc
                        results = []
                        with open(filename, "rb") as f:
                            sig = f.read(8)
                            if sig != b"\x89PNG\r\n\x1a\n":
                                raise ValueError("Not a PNG file")
                            while True:
                                chunk_type, data, crc = read_chunk(f)
                                if chunk_type is None:
                                    break
                                if chunk_type in [b"tEXt", b"iTXt"]:
                                    if chunk_type == b"tEXt":
                                        parts = data.split(b"\x00", 1)
                                        if len(parts) == 2:
                                            keyword, text = parts
                                            results.append({"keyword": keyword.decode("utf-8", "ignore"), "text": text.decode("utf-8", "ignore")})
                                    elif chunk_type == b"iTXt":
                                        parts = data.split(b"\x00", 5)
                                        if len(parts) == 6:
                                            keyword, comp_flag, comp_method, lang_tag, trans_key, text = parts
                                            results.append({"keyword": keyword.decode("utf-8", "ignore"), "text": text.decode("utf-8", "ignore")})
                                if chunk_type == b"IEND":
                                    break
                        return results
                    def format_image_info(info):
                        if info and 'text' in info[0]:
                            return info[0]['text']
                        return ''
                    info = extract_png_text_chunks(file_path)
                    content = format_image_info(info)
                except Exception as e:
                    content = f"PNG信息提取失败: {e}"
            if content is not None:
                # 在自身区域显示内容预览（只显示前300字，多余省略）
                self.preview_text = content[:300] + ('...\n(内容已截断)' if len(content) > 300 else '')
                self.update()
                # 自动复制到主输入框
                mainwin = self.window()
                if hasattr(mainwin, 'input_text'):
                    mainwin.input_text.setPlainText(content)
                break
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        r = 12  # 倒角半径
        rect = self.rect()
        # 绘制倒角正方形
        painter.setBrush(self.bg_color)
        border_color = QColor(68, 68, 68)
        if self._highlight:
            border_color = QColor(30, 144, 255)  # 高亮蓝色
        painter.setPen(QPen(border_color, 3))
        painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), r, r)
        # 绘制中心十字
        painter.setPen(QPen(self.cross_color, 3))
        cx, cy = rect.center().x(), rect.center().y()
        cross_len = 32
        painter.drawLine(cx - cross_len//2, cy, cx + cross_len//2, cy)
        painter.drawLine(cx, cy - cross_len//2, cx, cy + cross_len//2)
        # 绘制内容预览
        if hasattr(self, 'preview_text') and self.preview_text:
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            painter.drawText(rect.adjusted(8, 8, -8, -8), Qt.TextWordWrap, self.preview_text)
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QPlainTextEdit, QCheckBox, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QSizePolicy
from PySide6.QtWidgets import QSpinBox
from PySide6.QtCore import QThread, Signal, QUrl, QSize, Qt
from PySide6.QtGui import QIcon, QDesktopServices
import re
import math

# 标签处理线程类，用于异步处理标签转换操作
class ProcessingThread(QThread):
    # 定义信号：转换完成信号和错误发生信号
    finished = Signal(str)  # 转换完成时发送结果文本
    error_occurred = Signal(str)  # 发生错误时发送错误信息

    def __init__(self, input_text, mode, options, precise_mode=False, short_line_threshold=20, cnline_blank_count=3, compress_blank_threshold=4, weight_limit=1.6, alt_algo=False):
        """初始化处理线程
        Args:
            input_text (str): 需要转换的输入文本
            mode (int): 转换模式，0表示NAI→SD，1表示SD→NAI
            options (list): 预处理选项列表
            precise_mode (bool): 是否使用精确权重模式，默认False
            short_line_threshold (int): 短行阈值，低于该长度的行会被删除
            cnline_blank_count (int): 中文行替换为空行时的空行数量
            compress_blank_threshold (int): 压缩空行的阈值
            weight_limit (float): 权重上限
            alt_algo (bool): 是否启用备用权重算法
        """
        super().__init__()
        self.input_text = input_text
        self.mode = mode
        self.options = options
        self.precise_mode = precise_mode
        self.short_line_threshold = short_line_threshold
        self.cnline_blank_count = cnline_blank_count
        self.compress_blank_threshold = compress_blank_threshold
        self.weight_limit = weight_limit
        self.alt_algo = alt_algo

    def run(self):
        """线程执行函数，处理标签转换（调用后端核心）"""
        try:
            # 备用权重算法仅在SD->NAI模式下生效
            if self.mode == 1 and self.alt_algo:
                result = self.convert_sd_to_nai_alt(self.input_text)
            else:
                from tagc_core import process_tags
                result = process_tags(
                    self.input_text,
                    self.mode,
                    self.options,
                    self.precise_mode,
                    self.short_line_threshold,
                    self.cnline_blank_count,
                    self.compress_blank_threshold,
                    self.weight_limit
                )
            self.finished.emit(result)
        except Exception as e:
            self.error_occurred.emit(f"处理错误: {str(e)}")

    def convert_sd_to_nai_alt(self, text):
        """备用权重算法，将SD格式转为 权重::tag:: 格式"""
        def replace_sd(match):
            content, weight = match.groups()
            weight = float(weight)
            return f"{weight:.{3 if self.precise_mode else 1}f}::{content.strip()}::"
        import re
        return re.sub(r'\(([^:]+):([\d.]+)\)', replace_sd, text)

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
            blank = '\n' * self.cnline_blank_count
            text = re.sub(r'^.*[\u4e00-\u9fff]+.*$', blank, text, flags=re.M)
        # 删除artist标签
        if self.options[3]:
            # 删除包含artist的标签，前后可有英文逗号或中文逗号，删除两个逗号之间的内容
            def remove_artist_tag(match):
                return ','
            # 1. 匹配规则：逗号（英文或中文）+任意非逗号内容+artist+任意非逗号内容+逗号（英文或中文）
            text = re.sub(r'([,，])[^,，]*artist[^,，]*([,，])', remove_artist_tag, text, flags=re.I)
            # 2. 处理行首或行尾的artist标签（无逗号包围）
            text = re.sub(r'(^|[,，])[^,，]*artist[^,，]*$', '', text, flags=re.I|re.M)
            # 3. 特殊情况：前面无逗号但后面有逗号，删除artist及其前面的内容直到逗号
            # 例如：abc artist,def  → 删除为 def
            text = re.sub(r'[^,，]*artist[^,，]*([,，])', r'\1', text, flags=re.I)
            # 清理连续逗号和首尾逗号
            text = re.sub(r',{2,}', ',', text)
            text = re.sub(r'^,|,$', '', text)
        # 压缩空行
        if self.options[4]:
            # 使用自定义阈值压缩空行
            threshold = self.compress_blank_threshold
            # 将大于等于threshold的连续空行压缩为1个空行
            text = re.sub(r'(\n\s*){' + str(threshold) + ',}', '\n', text)
        # 移除反斜杠
        if self.options[5]:
            text = text.replace('\\', '')
        # 替换下划线为空格
        if self.options[7]:
            text = re.sub(r'_', ' ', text)
        # 删除短行但保留空行和中文行（新功能，界面开关控制，假设self.options[8]）
        if len(self.options) > 8 and self.options[8]:
            text = self.filter_lines(text)
    # 权重限制逻辑已移至run方法，保证作用于最终输出
        return text

    def filter_lines(self, content):
        """删除短行但保留空行和中文行，year特殊处理，阈值可调"""
        lines = content.split('\n')
        filtered_lines = []
        for line in lines:
            line_stripped = line.strip()
            # 保留空行
            if not line_stripped:
                filtered_lines.append(line)
                continue
            # 检查是否是纯中文行（包含至少一个中文字符）
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in line_stripped)
            # 如果是中文行或长度大于等于阈值的行，则保留
            if has_chinese or len(line_stripped) >= self.short_line_threshold:
                # 处理包含year的行
                if 'year' in line_stripped.lower():
                    year_index = line_stripped.lower().find('year')
                    filtered_lines.append(line[line.lower().find('year'):])
                else:
                    filtered_lines.append(line)
        return '\n'.join(filtered_lines)

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
    def add_resize_grip(self):
        # 右下角灰色小箭头（QSizeGrip）
        self.resize_grip = QSizeGrip(self)
        self.resize_grip.setStyleSheet('QSizeGrip { image: none; background: transparent; }')
        self.resize_grip.setFixedSize(38, 38)
        self.resize_grip.setToolTip('拖动缩放窗口')
        self.resize_grip.show()
        # 位置在右下角
        self.resize_grip.raise_()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 固定在右下角
        if hasattr(self, 'resize_grip'):
            self.resize_grip.move(self.width() - self.resize_grip.width() - 2, self.height() - self.resize_grip.height() - 2)
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        self.current_mode = 0  # 当前转换模式：0为NAI→SD，1为SD→NAI
        self.options = [False]*9  # 预处理选项状态（新增一项）
        self.drag_pos = None  # 窗口拖拽位置
        self.init_ui()  # 初始化用户界面
        self.worker = None  # 处理线程
        self.add_resize_grip()
    # 自定义QSizeGrip绘制灰色小箭头
    def paintEvent(self, event):
        super().paintEvent(event)
        if hasattr(self, 'resize_grip'):
            grip_rect = self.resize_grip.geometry()
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            arrow_color = QColor(255, 255, 255)
            painter.setPen(Qt.NoPen)
            painter.setBrush(arrow_color)
            # 绘制右下角小箭头
            x, y, w, h = grip_rect.x(), grip_rect.y(), grip_rect.width(), grip_rect.height()
            points = [
                QPoint(x + w - 18, y + h - 6),
                QPoint(x + w - 6, y + h - 6),
                QPoint(x + w - 6, y + h - 18)
            ]
            painter.drawPolygon(points)
            painter.end()

    def init_ui(self):
        """初始化用户界面"""
        # 设置无边框窗口
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle('Tag转换器 by Dispalce')
        self.resize(1000, 800)
        icon_path = resource_path('Logo_miku.ico')
        if not os.path.exists(icon_path):
            icon_path = resource_path('github.ico')
        self.setWindowIcon(QIcon(icon_path))

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
        self.blog_btn.setIcon(QIcon(resource_path('Logo_miku.ico')))
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
        self.blog_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://displace-ai.top/')))

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
        # 拖拽方形接口
        self.dragdrop_box = DragDropBox(self)
        mode_group.addWidget(self.dragdrop_box)
        # 精确权重转换开关放到拖拽框右侧
        mode_group.addWidget(self.precise_mode)
        # 算法切换滑块，仅SD->NAI时显示
        from PySide6.QtWidgets import QSlider
        self.algo_slider = QSlider(Qt.Horizontal)
        self.algo_slider.setMinimum(0)
        self.algo_slider.setMaximum(1)
        self.algo_slider.setValue(1)  # 默认右端（浮点权重）
        self.algo_slider.setTickPosition(QSlider.TicksBothSides)
        self.algo_slider.setTickInterval(1)
        self.algo_slider.setSingleStep(1)
        self.algo_slider.setFixedHeight(50)
        self.algo_slider.setFixedWidth(70)
        self.algo_slider.setStyleSheet('''
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: #232629;
                height: 12px;
                border-radius: 6px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 2px solid #4CAF50;
                width: 28px;
                margin: -8px 0;
                border-radius: 14px;
            }
        ''')
        # 初始为右端绿色，左端时变蓝色
        def update_slider_color(val):
            if val == 0:
                self.algo_slider.setStyleSheet('''
                    QSlider::groove:horizontal {
                        border: 1px solid #bbb;
                        background: #232629;
                        height: 12px;
                        border-radius: 6px;
                    }
                    QSlider::handle:horizontal {
                        background: #2196F3;
                        border: 2px solid #2196F3;
                        width: 28px;
                        margin: -8px 0;
                        border-radius: 14px;
                    }
                ''')
            else:
                self.algo_slider.setStyleSheet('''
                    QSlider::groove:horizontal {
                        border: 1px solid #bbb;
                        background: #232629;
                        height: 12px;
                        border-radius: 6px;
                    }
                    QSlider::handle:horizontal {
                        background: #4CAF50;
                        border: 2px solid #4CAF50;
                        width: 28px;
                        margin: -8px 0;
                        border-radius: 14px;
                    }
                ''')
        self.algo_slider.valueChanged.connect(update_slider_color)
        update_slider_color(self.algo_slider.value())
        self.algo_label_left = QLabel('转为括号权重')
        self.algo_label_left.setStyleSheet('color: #CCCCCC; font-size: 12pt;')
        self.algo_label_right = QLabel('转为浮点权重')
        self.algo_label_right.setStyleSheet('color: #CCCCCC; font-size: 12pt;')
        self.algo_slider.setVisible(False)
        self.algo_label_left.setVisible(False)
        self.algo_label_right.setVisible(False)
        algo_layout = QHBoxLayout()
        algo_layout.setSpacing(8)
        algo_layout.addWidget(self.algo_label_left, alignment=Qt.AlignVCenter)
        algo_layout.addWidget(self.algo_slider, alignment=Qt.AlignVCenter)
        algo_layout.addWidget(self.algo_label_right, alignment=Qt.AlignVCenter)
        mode_group.addLayout(algo_layout)
        def on_file_dropped(self, file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.input_text.setPlainText(content)
            except Exception as e:
                self.input_text.setPlainText(f"读取文件失败: {e}")

        # 创建GitHub项目链接按钮
        self.github_btn = QPushButton('项目地址')
        self.github_btn.setIcon(QIcon(resource_path('github.ico')))
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
        
        # 创建预处理选项和短行阈值输入
        options_grid = QGridLayout()
        self.option_checks = [
            QCheckBox('转换中文逗号为英文逗号'),
            QCheckBox('删除中文标签'),
            QCheckBox('将中文行替换空行'),
            QCheckBox('删除artist标签'),
            QCheckBox('压缩空行'),
            QCheckBox('移除反斜杠'),
            QCheckBox('拆分复合标签'),
            QCheckBox('替换下划线为空格'),
            QCheckBox('删除短行'),
            QCheckBox('限制权重最大值')
        ]
        # 数字输入框：权重上限
        from PySide6.QtWidgets import QDoubleSpinBox
        self.weight_limit_spin = QDoubleSpinBox()
        self.weight_limit_spin.setDecimals(2)
        self.weight_limit_spin.setMinimum(1.0)
        self.weight_limit_spin.setMaximum(10.0)
        self.weight_limit_spin.setSingleStep(0.1)
        self.weight_limit_spin.setValue(1.6)
        self.weight_limit_spin.setToolTip('设置权重上限（支持两位小数，直接输入如1.60）')
        self.weight_limit_spin.setVisible(False)
        self.weight_limit_spin.setFixedWidth(110)
        self.weight_limit_spin.setStyleSheet('''
            QDoubleSpinBox {
                background-color: #232629;
                color: #FFFFFF;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 2px 6px;
                font-size: 11pt;
                min-height: 24px;
                max-height: 26px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 14px;
                background: #353535;
                border: none;
                border-radius: 3px;
            }
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                background: #4CAF50;
            }
            QDoubleSpinBox::up-arrow, QDoubleSpinBox::down-arrow {
                width: 8px;
                height: 8px;
            }
        ''')
        self.option_checks[9].toggled.connect(self.weight_limit_spin.setVisible)
        # 数字输入框：压缩空行阈值
        self.compress_blank_spin = QSpinBox()
        self.compress_blank_spin.setMinimum(2)
        self.compress_blank_spin.setMaximum(20)
        self.compress_blank_spin.setValue(4)
        self.compress_blank_spin.setToolTip('大于等于该数量的连续空行会被压缩为1个空行')
        self.compress_blank_spin.setStyleSheet(self.compress_blank_spin.styleSheet() + '\nQToolTip { background-color: #232629; color: #fff; border: 1px solid #444; font-size: 10pt; }')
        self.compress_blank_spin.setVisible(False)
        self.compress_blank_spin.setFixedWidth(110)
        self.compress_blank_spin.setStyleSheet('''
            QSpinBox {
                background-color: #232629;
                color: #FFFFFF;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 2px 6px;
                font-size: 11pt;
                min-height: 24px;
                max-height: 26px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 14px;
                background: #353535;
                border: none;
                border-radius: 3px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #4CAF50;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow {
                width: 8px;
                height: 8px;
            }
        ''')
        # 绑定压缩空行选项的显示/隐藏
        self.option_checks[4].toggled.connect(self.compress_blank_spin.setVisible)
        # 数字输入框：短行阈值
        self.short_line_spin = QSpinBox()
        self.short_line_spin.setMinimum(1)
        self.short_line_spin.setMaximum(1000)
        self.short_line_spin.setValue(20)
        self.short_line_spin.setToolTip('小于该长度的行会被删除')
        self.short_line_spin.setStyleSheet(self.short_line_spin.styleSheet() + '\nQToolTip { background-color: #232629; color: #fff; border: 1px solid #444; font-size: 10pt; }')
        self.short_line_spin.setVisible(False)
        self.short_line_spin.setFixedWidth(110)
        self.short_line_spin.setStyleSheet('''
            QSpinBox {
                background-color: #232629;
                color: #FFFFFF;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 2px 6px;
                font-size: 11pt;
                min-height: 24px;
                max-height: 26px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 14px;
                background: #353535;
                border: none;
                border-radius: 3px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #4CAF50;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow {
                width: 8px;
                height: 8px;
            }
        ''')
        # 数字输入框：中文行替换为空行时的空行数量
        self.cnline_blank_spin = QSpinBox()
        self.cnline_blank_spin.setMinimum(1)
        self.cnline_blank_spin.setMaximum(10)
        self.cnline_blank_spin.setValue(3)
        self.cnline_blank_spin.setToolTip('将中文行替换为多少个空行')
        self.cnline_blank_spin.setStyleSheet(self.cnline_blank_spin.styleSheet() + '\nQToolTip { background-color: #232629; color: #fff; border: 1px solid #444; font-size: 10pt; }')
        self.cnline_blank_spin.setFixedWidth(70)
        self.cnline_blank_spin.setStyleSheet('''
            QSpinBox {
                background-color: #232629;
                color: #FFFFFF;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 2px 6px;
                font-size: 11pt;
                min-height: 24px;
                max-height: 26px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 14px;
                background: #353535;
                border: none;
                border-radius: 3px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #4CAF50;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow {
                width: 8px;
                height: 8px;
            }
        ''')
        self.cnline_blank_spin.setVisible(False)
        # 绑定删除短行选项的显示/隐藏
        self.option_checks[8].toggled.connect(self.short_line_spin.setVisible)
        # 绑定将中文行替换空行选项的显示/隐藏
        self.option_checks[2].toggled.connect(self.cnline_blank_spin.setVisible)
        # 设置互斥选项
        self.option_checks[1].toggled.connect(lambda: self.option_checks[2].setChecked(False))
        self.option_checks[2].toggled.connect(lambda: self.option_checks[1].setChecked(False))
        # 排列选项布局，短行开关和输入框同一行
        for i, check in enumerate(self.option_checks):
            if i == 8:
                # 第9项“删除短行”与输入框同一行
                hbox = QHBoxLayout()
                hbox.addWidget(check)
                hbox.addWidget(self.short_line_spin)
                hbox.addStretch(1)
                options_grid.addLayout(hbox, i//3, i%3)
            elif i == 2:
                # 第3项“将中文行替换空行”与输入框同一行
                hbox = QHBoxLayout()
                hbox.addWidget(check)
                hbox.addWidget(self.cnline_blank_spin)
                hbox.addStretch(1)
                options_grid.addLayout(hbox, i//3, i%3)
            elif i == 4:
                # 第5项“压缩空行”与输入框同一行
                hbox = QHBoxLayout()
                hbox.addWidget(check)
                hbox.addWidget(self.compress_blank_spin)
                hbox.addStretch(1)
                options_grid.addLayout(hbox, i//3, i%3)
            elif i == 9:
                # 第10项“限制权重最大值”与输入框同一行
                hbox = QHBoxLayout()
                hbox.addWidget(check)
                hbox.addWidget(self.weight_limit_spin)
                hbox.addStretch(1)
                options_grid.addLayout(hbox, i//3, i%3)
            else:
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
        # SD->NAI模式下根据滑块选择算法
        alt_algo = False
        if self.current_mode == 1:
            alt_algo = (self.algo_slider.value() == 1)
        self.worker = ProcessingThread(
            input_text,
            self.current_mode,
            self.options,
            self.precise_mode.isChecked(),
            self.short_line_spin.value(),
            self.cnline_blank_spin.value(),
            self.compress_blank_spin.value(),
            self.weight_limit_spin.value(),
            alt_algo
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
        # 限制权重最大值选项及输入框在SD->NAI时隐藏
        show_weight_limit = not self.current_mode
        self.option_checks[9].setVisible(show_weight_limit)
        self.weight_limit_spin.setVisible(show_weight_limit and self.option_checks[9].isChecked())
        # 算法切换滑块仅SD->NAI时显示
        show_algo = self.current_mode
        self.algo_slider.setVisible(show_algo)
        self.algo_label_left.setVisible(show_algo)
        self.algo_label_right.setVisible(show_algo)
        if show_algo:
            self.algo_slider.setValue(1)  # 默认右端
        if self.current_mode:
            self.precise_mode.setChecked(False)
            self.option_checks[6].setChecked(False)
            self.option_checks[7].setChecked(False)
            self.option_checks[9].setChecked(False)
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