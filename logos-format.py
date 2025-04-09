#!/usr/bin/env python3
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
    
    # 检查是否已有样式参数
    has_style = any(arg.startswith("-style=") for arg in args)
    
    if not has_style:
        # 添加使用tab缩进的样式参数
        args.append("-style={UseTab: Always, IndentWidth: 8}")
    else:
        # 如果已有样式参数，尝试修改它
        for i, arg in enumerate(args):
            if arg.startswith("-style="):
                # 提取现有样式并添加tab设置
                style = arg.replace("-style=", "")
                # 处理文件风格和内联风格两种情况
                if style.startswith("{") and style.endswith("}"):
                    # 内联风格，添加tab设置
                    style = style[:-1] + ", UseTab: Always, IndentWidth: 8}"
                elif not style.startswith("file"):
                    # 非文件风格，转换为内联风格
                    style = f"{{{style}, UseTab: Always, IndentWidth: 8}}"
                args[i] = f"-style={style}"
    
    command = ["clang-format"] + args
    process = Popen(command, stdout=PIPE, stderr=None, stdin=PIPE)
    formatted_content = process.communicate(input="\n".join(lines).encode())[0]
    return formatted_content.decode().splitlines()


def output_processed_code(formatted_lines):
    """将格式化后的代码中的临时标记替换回 Logos 语法"""
    for line in formatted_lines:
        if "@logosformat" in line:
            # 将 @logosformat 替换回 %
            fixed_line = line.replace("@logosformat", "%")
            
            # 检查是否为特殊标记，如果是则移除行尾的分号
            if any(token in fixed_line for token in SPECIAL_TOKENS):
                fixed_line = fixed_line.replace(";", "")
            
            print(fixed_line)
        else:
            print(line)


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
