import sys
import re
from subprocess import Popen, PIPE

# Logos 语法标记分类
# 需要在行尾添加分号的块级标记
SPECIAL_TOKENS = ["%hook", "%end", "%new", "%group", "%subclass"]

# 不需要添加分号的标记
NORMAL_TOKENS = [
    "%property",  # 块级别的特殊情况，不添加分号
    "%config",    # 顶层标记
    "%hookf",     # 顶层标记
    "%ctor",      # 顶层标记
    "%dtor",      # 顶层标记
    "%init",      # 函数级别标记
    "%c",         # 函数级别标记
    "%orig",      # 函数级别标记
    "%log",       # 函数级别标记
]


def preprocess_logos_syntax(lines):
    """将 Logos 语法替换为临时标记，以便 clang-format 格式化"""
    processed_lines = []
    
    # 将多行合并为一个文本进行处理，处理跨行的 %c() 表达式
    full_content = "\n".join(lines)
    
    # 处理 %c(ClassName) 表达式，包括可能跨行的情况
    c_pattern = re.compile(r"%c\(\s*([A-Za-z0-9_]+)\s*\)")
    full_content = c_pattern.sub(r"@logosformatc_\1", full_content)
    
    # 重新分割为行
    lines = full_content.splitlines()
    
    for line in lines:
        # 检查是否是注释行或包含注释
        comment_pos = line.find('//')
        
        # 如果是纯注释行（行首就是注释）或空行，直接添加不处理
        if comment_pos == 0 or line.strip() == '':
            processed_lines.append(line)
            continue
        
        # 如果行中没有注释，正常处理
        if comment_pos == -1:
            # 处理正常标记（不添加分号）
            for token in NORMAL_TOKENS:
                if token in line and token != "%c":  # 跳过 %c，因为已经在前面处理了
                    token_name = token[1:]  # 去掉 %
                    line = re.sub(rf"%({token_name})\b", r"@logosformat\1", line)
            
            # 处理特殊标记（添加分号）
            for token in SPECIAL_TOKENS:
                if token in line:
                    token_name = token[1:]  # 去掉 %
                    line = re.sub(rf"%({token_name})\b", r"@logosformat\1", line) + ";"
        else:
            # 行中有注释，分别处理注释前和注释部分
            code_part = line[:comment_pos]
            comment_part = line[comment_pos:]
            
            # 处理代码部分
            modified_code = False
            
            # 只处理注释前的代码部分
            for token in NORMAL_TOKENS:
                if token in code_part and token != "%c":  # 跳过 %c，因为已经在前面处理了
                    token_name = token[1:]  # 去掉 %
                    code_part = re.sub(rf"%({token_name})\b", r"@logosformat\1", code_part)
            
            for token in SPECIAL_TOKENS:
                if token in code_part:
                    token_name = token[1:]  # 去掉 %
                    code_part = re.sub(rf"%({token_name})\b", r"@logosformat\1", code_part) + ";"
                    modified_code = True
            
            # 重新组合代码和注释部分
            if modified_code:
                # 如果添加了分号，添加新行并保留注释
                processed_lines.append(code_part)
                if comment_part.strip():  # 如果注释部分不为空
                    processed_lines.append(comment_part)
            else:
                line = code_part + comment_part
                processed_lines.append(line)
            continue
        
        processed_lines.append(line)
    
    return processed_lines



def preprocess_logos_syntax(lines):
    """将 Logos 语法替换为临时标记，以便 clang-format 格式化"""
    processed_lines = []
    
    for line in lines:
        # 检查是否是注释行或包含注释
        comment_pos = line.find('//')
        
        # 如果是纯注释行（行首就是注释）或空行，直接添加不处理
        if comment_pos == 0 or line.strip() == '':
            processed_lines.append(line)
            continue
        
        # 如果行中没有注释，正常处理
        if comment_pos == -1:
            # 处理正常标记（不添加分号）
            for token in NORMAL_TOKENS:
                if token in line:
                    token_name = token[1:]  # 去掉 %
                    line = re.sub(rf"%({token_name})\b", r"@logosformat\1", line)
            
            # 处理特殊标记（添加分号）
            for token in SPECIAL_TOKENS:
                if token in line:
                    token_name = token[1:]  # 去掉 %
                    line = re.sub(rf"%({token_name})\b", r"@logosformat\1", line) + ";"
        else:
            # 行中有注释，分别处理注释前和注释部分
            code_part = line[:comment_pos]
            comment_part = line[comment_pos:]
            
            # 处理代码部分
            modified_code = False
            
            # 只处理注释前的代码部分
            for token in NORMAL_TOKENS:
                if token in code_part:
                    token_name = token[1:]  # 去掉 %
                    code_part = re.sub(rf"%({token_name})\b", r"@logosformat\1", code_part)
            
            for token in SPECIAL_TOKENS:
                if token in code_part:
                    token_name = token[1:]  # 去掉 %
                    code_part = re.sub(rf"%({token_name})\b", r"@logosformat\1", code_part) + ";"
                    modified_code = True
            
            # 重新组合代码和注释部分
            if modified_code:
                # 如果添加了分号，添加新行并保留注释
                processed_lines.append(code_part)
                if comment_part.strip():  # 如果注释部分不为空
                    processed_lines.append(comment_part)
            else:
                line = code_part + comment_part
                processed_lines.append(line)
            continue
        
        processed_lines.append(line)
    
    return processed_lines

def format_code_with_clang(lines):
    """使用 clang-format 格式化代码"""
    # 创建命令行参数列表
    args = sys.argv[1:]
    
    # 定义减少换行的样式参数
    style_options = {
        "UseTab": "Always", 
        "IndentWidth": 8,
        "ColumnLimit": 200,  # 增加列宽限制，防止长行被拆分
        "BinPackParameters": "true",  # 尽可能将参数打包到一行
        "BinPackArguments": "true",   # 尽可能将参数打包到一行
        "AllowAllParametersOfDeclarationOnNextLine": "true",
        "AlignAfterOpenBracket": "Align",  # 对齐开括号后的参数
        "ContinuationIndentWidth": 4,      # 控制续行的缩进宽度
        "BreakBeforeBinaryOperators": "None",  # 不在二元运算符前换行
        "PenaltyBreakAssignment": 500,     # 大幅增加赋值语句换行的惩罚值
        "PenaltyBreakBeforeFirstCallParameter": 500,  # 大幅增加调用参数换行的惩罚值
        "BreakConstructorInitializersBeforeComma": "false",
        "AllowShortFunctionsOnASingleLine": "All"
    }
    
    # 检查是否已有样式参数
    has_style = any(arg.startswith("-style=") for arg in args)
    
    if not has_style:
        # 构建样式参数字符串
        style_str = ", ".join([f"{k}: {v}" for k, v in style_options.items()])
        args.append(f"-style={{{style_str}}}")
    else:
        # 如果已有样式参数，尝试修改它
        for i, arg in enumerate(args):
            if arg.startswith("-style="):
                # 提取现有样式
                style = arg.replace("-style=", "")
                
                # 处理文件风格和内联风格两种情况
                if style.startswith("{") and style.endswith("}"):
                    # 内联风格，添加我们的样式参数
                    style_content = style[1:-1]
                    # 合并已有样式和新样式
                    merged_style = style_content
                    for k, v in style_options.items():
                        if k not in style_content:
                            if merged_style:
                                merged_style += ", "
                            merged_style += f"{k}: {v}"
                    args[i] = f"-style={{{merged_style}}}"
                elif not style.startswith("file"):
                    # 非文件风格，转换为内联风格
                    style_str = ", ".join([f"{k}: {v}" for k, v in style_options.items()])
                    args[i] = f"-style={{{style}, {style_str}}}"
    
    command = ["clang-format"] + args
    process = Popen(command, stdout=PIPE, stderr=None, stdin=PIPE)
    formatted_content = process.communicate(input="\n".join(lines).encode())[0]
    formatted_lines = formatted_content.decode().splitlines()
    
    # 处理可能被分割到多行的 @logosformatc_ 表达式
    return fix_split_c_expressions(formatted_lines)


def fix_split_c_expressions(lines):
    """修复被分割到多行的 @logosformatc_ 表达式"""
    result = []
    i = 0
    while i < len(lines):
        current_line = lines[i]
        
        # 检查是否有不完整的 @logosformatc_ 表达式
        if "@logosformatc_" in current_line and current_line.strip().endswith("[["):
            # 这可能是一个被拆分的 %c 表达式的开始
            combined_line = current_line
            j = i + 1
            
            # 尝试向后找到表达式的其余部分
            while j < len(lines) and "alloc]" in lines[j]:
                combined_line += " " + lines[j].strip()
                j += 1
            
            # 添加组合的行并跳过已处理的行
            result.append(combined_line)
            i = j
        else:
            result.append(current_line)
            i += 1
    
    return result



def output_processed_code(formatted_lines):
    """将格式化后的代码中的临时标记替换回 Logos 语法"""
    for line in formatted_lines:
        # 处理 @logosformatc_ClassName 标记，替换回 %c(ClassName)
        c_pattern = re.compile(r"@logosformatc_([A-Za-z0-9_]+)")
        fixed_line = c_pattern.sub(r"%c(\1)", line)
        
        # 处理其他标记
        if "@logosformat" in fixed_line:
            # 将 @logosformat 替换回 %
            fixed_line = fixed_line.replace("@logosformat", "%")
            
            # 检查是否为特殊标记，如果是则移除行尾的分号
            if any(token in fixed_line for token in SPECIAL_TOKENS):
                fixed_line = fixed_line.replace(";", "")
            
            print(fixed_line)
        else:
            print(fixed_line)


def main():
    """主函数：处理输入，格式化代码，输出结果"""
    # 读取标准输入
    file_contents = sys.stdin.read().splitlines()
    
    # 预处理: 替换 Logos 语法为临时标记
    processed_lines = preprocess_logos_syntax(file_contents)
    
    # 使用 clang-format 格式化代码
    formatted_lines = format_code_with_clang(processed_lines)
    
    # 后处理: 将临时标记替换回 Logos 语法
    output_processed_code(formatted_lines)


if __name__ == "__main__":
    main()
