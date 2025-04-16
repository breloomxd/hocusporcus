import pandas as pd
import re  # 用于更复杂的正则表达式（如果需要）

# --- 配置 ---
# 输入你导出的文件名
INPUT_FILENAME = "你导出的文件名.xlsx"  # 也可以是 .csv 或 .jsonl
# 保存过滤后消息的文件名
OUTPUT_FILENAME = "待分析的过滤消息.xlsx"  # 也可以是 .csv

# 需要忽略的命令前缀列表
COMANDO_PREFIXOS = ['!', '/', '.', '$', '%', ';']
# 表示问题或求助的关键词列表（可自行添加）
KEYWORDS_PERGUNTA = [
    '怎么', '如何', '为什么', '为啥', '哪里', '谁', '什么时候', '？',
    '帮助', '求助', '救命', '有问题',
    '报错', '错误', 'bug', '故障', '不行', '不能用',
    '疑问', '有人知道吗', '求问',
    # 添加你的Minecraft/TerraLivre服务器专用术语
    '领地', '保护', '土地', 'IP', '连接', '进服',
    '插件', '模组', '金币', 'VIP', '商店', '重置', '卡顿'
]
# 消息最小长度（根据需要调整）
MIN_MESSAGE_LENGTH = 15  # 至少包含几个词的消息

# --- 加载数据 ---
print(f"🔄 正在从文件加载数据: {INPUT_FILENAME}")
try:
    if INPUT_FILENAME.endswith('.xlsx'):
        df = pd.read_excel(INPUT_FILENAME)
    elif INPUT_FILENAME.endswith('.csv'):
        df = pd.read_csv(INPUT_FILENAME)
    elif INPUT_FILENAME.endswith('.jsonl'):
        df = pd.read_json(INPUT_FILENAME, lines=True)
    else:
        print(f"❌ 不支持的格式: {INPUT_FILENAME}")
        exit()

    # 确保消息列是字符串类型
    df['Message'] = df['Message'].astype(str)
    # 转换时间戳格式（可选，取决于保存的格式）
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    print(f"📊 已加载消息总数: {len(df)}")

except FileNotFoundError:
    print(f"❌ 文件未找到: {INPUT_FILENAME}")
    exit()
except Exception as e:
    print(f"❌ 加载文件时出错: {e}")
    exit()

# --- 应用过滤器 ---
print("🔍 正在应用过滤器...")

# 1. 排除机器人消息
filt_bots = df['Is Bot'] == False
print(f"  -> 过滤机器人后剩余: {filt_bots.sum()} 条消息")

# 2. 排除已知命令（不区分大小写）
# 创建条件：消息不以任何命令前缀开头
filt_comandos = ~df['Message'].str.lower().str.startswith(tuple(COMANDO_PREFIXOS))
print(f"  -> 过滤命令后剩余: {(filt_bots & filt_comandos).sum()} 条消息")

# 3. 搜索关键词或问号（不区分大小写）
# 使用正则表达式匹配完整单词或问号
keyword_regex = r'\b(' + '|'.join(map(re.escape, KEYWORDS_PERGUNTA)) + r')\b|\?'
filt_keywords = df['Message'].str.contains(keyword_regex, case=False, regex=True, na=False)
print(f"  -> 包含关键词/问号的消息: {(filt_bots & filt_comandos & filt_keywords).sum()} 条")

# 4. 按最小长度过滤
filt_length = df['Message'].str.len() >= MIN_MESSAGE_LENGTH
print(f"  -> 达到最小长度要求: {(filt_bots & filt_comandos & filt_keywords & filt_length).sum()} 条")

# --- 组合所有过滤器 ---
# 相关消息 = 非机器人 + 非命令 + (包含关键词或问号) + 达到最小长度
df_filtrado = df[filt_bots & filt_comandos & filt_keywords & filt_length]

# --- 可选：按时间排序查看问题发展 ---
df_filtrado = df_filtrado.sort_values('Timestamp', ascending=True)

# --- 保存结果 ---
print(f"\n💾 正在保存 {len(df_filtrado)} 条过滤后的消息到: {OUTPUT_FILENAME}")
try:
    if OUTPUT_FILENAME.endswith('.xlsx'):
        df_filtrado.to_excel(OUTPUT_FILENAME, index=False, engine='openpyxl')
    elif OUTPUT_FILENAME.endswith('.csv'):
        df_filtrado.to_csv(OUTPUT_FILENAME, index=False, encoding='utf-8-sig')
    else:  # 假设是JSONL或其他to_json支持的格式
         with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
             f.write(df_filtrado.to_json(orient='records', lines=True, force_ascii=False, date_format='iso'))

    print("✅ 过滤消息导出完成！")

except Exception as e:
    print(f"❌ 保存过滤文件时出错: {e}")
