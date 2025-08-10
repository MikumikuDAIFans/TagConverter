import re
import math

def process_tags(input_text, mode, options, precise_mode=False, short_line_threshold=20, cnline_blank_count=3, compress_blank_threshold=4, weight_limit=1.6):
    """
    后端核心处理函数，负责标签文本的全部处理逻辑。
    Args:
        input_text (str): 输入文本
        mode (int): 0=NAI→SD, 1=SD→NAI
        options (list): 预处理选项
        precise_mode (bool): 精确权重转换
        short_line_threshold (int): 短行阈值
        cnline_blank_count (int): 中文行替换空行数
        compress_blank_threshold (int): 压缩空行阈值
        weight_limit (float): 权重上限
    Returns:
        str: 处理后的文本
    """
    def apply_optional_filters(text):
        if options[0]:
            text = re.sub(r'，', ',', text)
        if options[1] and not options[2]:
            text = re.sub(r'[\u4e00-\u9fff]+', '', text)
        if options[2] and not options[1]:
            blank = '\n' * cnline_blank_count
            text = re.sub(r'^.*[\u4e00-\u9fff]+.*$', blank, text, flags=re.M)
        if options[3]:
            def remove_artist_tag(match):
                return ','
            text = re.sub(r'([,，])[^,，]*artist[^,，]*([,，])', remove_artist_tag, text, flags=re.I)
            text = re.sub(r'(^|[,，])[^,，]*artist[^,，]*$', '', text, flags=re.I|re.M)
            text = re.sub(r'[^,，]*artist[^,，]*([,，])', r'\1', text, flags=re.I)
            text = re.sub(r',{2,}', ',', text)
            text = re.sub(r'^,|,$', '', text)
        if options[4]:
            threshold = compress_blank_threshold
            text = re.sub(r'(\n\s*){' + str(threshold) + ',}', '\n', text)
        if options[5]:
            text = text.replace('\\', '')
        if options[7]:
            text = re.sub(r'_', ' ', text)
        if len(options) > 8 and options[8]:
            text = filter_lines(text)
        return text

    def filter_lines(content):
        lines = content.split('\n')
        filtered_lines = []
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                filtered_lines.append(line)
                continue
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in line_stripped)
            if has_chinese or len(line_stripped) >= short_line_threshold:
                if 'year' in line_stripped.lower():
                    filtered_lines.append(line[line.lower().find('year'):])
                else:
                    filtered_lines.append(line)
        return '\n'.join(filtered_lines)

    def convert_nai_to_sd(text):
        def replace_float_weight(match):
            weight = float(match.group(1))
            content = match.group(2)
            if options[6]:
                tags = [tag.strip() for tag in content.split(',') if tag.strip()]
                return ','.join([f'({tag}:{weight:.{3 if precise_mode else 1}f})' for tag in tags])
            return f'({content.strip()}:{weight:.{3 if precise_mode else 1}f})'
        def replace_bracket_weight(match):
            left_brackets = match.group(1)
            right_brackets = match.group(3)
            content = match.group(2)
            count = max(len(left_brackets), len(right_brackets))
            weight = math.pow(1.1 if left_brackets[0] == '{' else 0.9, count)
            weight = round(weight, 3 if precise_mode else 1)
            if options[6]:
                tags = [tag.strip() for tag in content.split(',') if tag.strip()]
                return ','.join([f'({tag}:{weight:.{3 if precise_mode else 1}f})' for tag in tags])
            return f'({content.strip()}:{weight:.{3 if precise_mode else 1}f})'
        text = re.sub(r'(\d+\.\d+)::(.*?)::', replace_float_weight, text, flags=re.DOTALL)
        return re.sub(r'([{{\[{]+)(.*?)([}}\]]+)', replace_bracket_weight, text, flags=re.DOTALL)

    def convert_sd_to_nai(text):
        def replace_sd(match):
            content, weight = match.groups()
            weight = float(weight)
            if weight >= 1:
                count = math.ceil((weight - 1) / 0.1)
                return '{' * count + content + '}' * count
            else:
                count = math.ceil((1 - weight) / 0.1)
                return '[' * count + content + ']' * count
        return re.sub(r'\(([^:]+):([\d.]+)\)', replace_sd, text)

    # 主处理流程
    text = apply_optional_filters(input_text)
    if mode == 0:
        result = convert_nai_to_sd(text)
    else:
        result = convert_sd_to_nai(text)
    if len(options) > 9 and options[9]:
        pattern = r'(:)(\d+\.?\d*)'
        limit = weight_limit
        def replace_weight(match):
            colon = match.group(1)
            weight = float(match.group(2))
            if weight > limit:
                return f"{colon}{limit:.2f}"
            else:
                return f"{colon}{weight:.2f}" if '.' in match.group(2) else match.group(0)
        result = re.sub(pattern, replace_weight, result)
    # 权重自动规整，仅在精确权重转换关闭时启用
    if not precise_mode:
        def trim_weight_zero(m):
            tag = m.group(1)
            weight = m.group(2)
            weight_str = str(float(weight)).rstrip('0').rstrip('.') if '.' in weight else weight
            return f'({tag}:{weight_str})'
        result = re.sub(r'\(([^:()]+):([0-9]+\.[0-9]+)\)', trim_weight_zero, result)
    return result
