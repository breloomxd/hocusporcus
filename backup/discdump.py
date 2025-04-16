import os
import discord
import asyncio
import pandas as pd
import traceback
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('DISCORD_GUILD_ID')

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

class DiscordMessageExporter(discord.Client):
    async def on_ready(self):
        try:
            print(f"🔗 已登录为 {self.user}")
            guild = self.get_guild(int(GUILD_ID))

            if not guild:
                print(f"❌ 未找到ID为 {GUILD_ID} 的服务器！")
                await self.close()
                return

            # --- 修复：将服务器存储为实例变量 ---
            self.guild = guild
            print(f"✅ 已连接到服务器: {self.guild.name}")
            # ----------------------------------------------

            text_channels = self.guild.text_channels
            if not text_channels:
                print("❌ 此服务器中没有文本频道。")
                await self.close()
                return

            print("\n📜 可用频道:")
            for index, channel in enumerate(text_channels, 1):
                print(f"{index}. {channel.name} (ID: {channel.id})")

            # 获取用户选择的频道
            selected_indices = self.get_channel_selection(text_channels)

            if not selected_indices:
                print("ℹ️ 未选择任何频道进行导出。")
                return # 如果未选择频道则优雅退出

            # 获取用户选择的输出格式
            output_format = input("输入输出格式 (csv, xlsx, jsonl) [默认: xlsx]: ").lower().strip() or 'xlsx'
            if output_format not in ['csv', 'xlsx', 'jsonl']:
                print(f"⚠️ 无效格式 '{output_format}'！将使用默认xlsx格式。")
                output_format = 'xlsx'
            print(f"📝 选择的输出格式: {output_format}")

            # 为选中的频道创建导出任务
            tasks = []
            print("\n🚀 开始导出过程...")
            for index in selected_indices:
                channel = text_channels[index]
                # 为每个频道导出创建任务
                tasks.append(self.export_channel_messages(channel, output_format))

            # 并发执行所有导出任务
            await asyncio.gather(*tasks)
            print("\n🎉 所有选中频道的导出已完成。")

        except ValueError:
             print(f"❌ 环境变量中的GUILD_ID无效: '{GUILD_ID}'。请确保它是有效的整数。")
        except discord.errors.LoginFailure:
             print("❌ Discord登录失败：检查DISCORD_TOKEN是否正确有效。")
        except Exception as e:
            print(f"❌ 在设置或频道处理过程中发生意外错误: {e}")
            traceback.print_exc() # 打印详细错误信息用于调试
        finally:
            print("🚪 正在关闭连接...")
            await self.close()

    def get_channel_selection(self, text_channels):
        selected_indices = []
        max_channels = len(text_channels)
        prompt = f"\n输入要导出的频道编号(1-{max_channels}, 例如: 1, 3, 5) 或 'all': "

        while True: # 循环直到输入有效或决定退出
            try:
                selection_str = input(prompt).strip()
                if not selection_str: # 用户未输入直接按回车
                    print("ℹ️ 未做选择。")
                    return []

                if selection_str.lower() == 'all':
                    print("✅ 选择所有频道。")
                    return list(range(max_channels)) # 返回所有索引

                raw_indices = [s.strip() for s in selection_str.replace(',', ' ').split()]
                valid_indices = set() # 使用集合自动处理重复项
                invalid_input_found = False

                for s_idx in raw_indices:
                    if not s_idx: continue # 忽略多个空格/逗号产生的空部分

                    idx = int(s_idx) - 1 # 转换为0基索引
                    if 0 <= idx < max_channels:
                        valid_indices.add(idx)
                    else:
                        print(f"⚠️ 无效的选择编号: '{s_idx}' (必须在1到{max_channels}之间)")
                        invalid_input_found = True

                if invalid_input_found:
                    if valid_indices:
                        print(f"ℹ️ 忽略无效数字。继续处理有效选择: {[i+1 for i in sorted(list(valid_indices))]}")
                        return sorted(list(valid_indices))
                    else:
                        print("❌ 未输入有效的频道编号。请重试。")
                        # 继续循环以重新提示
                elif valid_indices:
                     print(f"✅ 选择的频道: {[text_channels[i].name for i in sorted(list(valid_indices))]}")
                     return sorted(list(valid_indices)) # 返回有效索引的排序列表
                else:
                    # 这种情况可能发生在输入仅为逗号/空格时
                    print("❌ 未输入频道编号。请重试。")

            except ValueError:
                print("❌ 无效输入。请输入数字(例如: 1, 3, 5)或'all'。")
                # 继续循环以重新提示

    async def export_channel_messages(self, channel: discord.TextChannel, output_format='xlsx'):
        print(f"\n📥 正在从 #{channel.name} (ID: {channel.id}) 获取消息...")
        messages = []
        message_count = 0
        try:
            async for msg in channel.history(limit=None): # 考虑添加可选限制参数
                # 收集所需的消息数据
                messages.append({
                    "用户ID": msg.author.id,
                    "用户名": msg.author.name,
                    "显示名称": msg.author.display_name, # 昵称(如果设置)，否则用户名
                    "是机器人": msg.author.bot, # 了解消息是否来自机器人很有用
                    "消息内容": msg.content,
                    "时间戳": msg.created_at, # 保持时区感知以确保准确性
                    "消息ID": msg.id,
                    "频道ID": channel.id,
                    "频道名称": channel.name
                })
                message_count += 1
                if message_count % 1000 == 0: # 根据需要调整反馈频率
                    print(f"[{channel.name}] 已获取 {message_count} 条消息...")

        except discord.Forbidden:
             print(f"❌ 权限错误: 无法访问 #{channel.name} 的消息历史。检查机器人权限。")
             return # 停止处理此频道
        except discord.HTTPException as e:
             print(f"❌ 从 #{channel.name} 获取消息时Discord API错误: {e.status} - {e.text}")
             return # 停止处理此频道
        except Exception as e:
             print(f"❌ 从 #{channel.name} 获取消息时发生意外错误: {e}")
             traceback.print_exc()
             return # 停止处理此频道


        if messages:
            print(f"[{channel.name}] 共获取 {message_count} 条消息。准备导出...")
            try:
                df = pd.DataFrame(messages)
                # 确保时间戳列是datetime类型(如果需要排序)
                df['时间戳'] = pd.to_datetime(df['时间戳'])
                df.sort_values('时间戳', inplace=True, ascending=True) # 按时间顺序排序

                # --- 修复: 使用self.guild.name ---
                base_filename = f"{self.guild.name}_{channel.name}_messages_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
                # --------------------------------

                if output_format == 'xlsx':
                    filename = f"{base_filename}.xlsx"
                    print(f"[{channel.name}] 正在写入Excel文件: {filename}...")
                    # 引擎'openpyxl'是.xlsx的标准
                    df.to_excel(filename, index=False, engine="openpyxl")
                elif output_format == 'csv':
                    filename = f"{base_filename}.csv"
                    print(f"[{channel.name}] 正在写入CSV文件: {filename}...")
                    # 使用utf-8-sig以获得更好的特殊字符Excel兼容性
                    df.to_csv(filename, index=False, encoding='utf-8-sig')
                elif output_format == 'jsonl':
                    filename = f"{base_filename}.jsonl"
                    print(f"[{channel.name}] 正在写入JSON Lines文件: {filename}...")
                    # date_format='iso'确保时间戳以标准ISO 8601格式保存
                    # force_ascii=False防止unicode字符被转义
                    with open(filename, 'w', encoding='utf-8') as f:
                         f.write(df.to_json(orient='records', lines=True, force_ascii=False, date_format='iso'))

                print(f"✅ #{channel.name} 的导出完成: {filename}")

            except Exception as e:
                 print(f"❌ 写入 #{channel.name} 的文件时出错: {e}")
                 traceback.print_exc()

        else:
            print(f"⚠️ 在 #{channel.name} 中未找到或获取到任何消息")

def main():
    """
    主函数，用于验证环境变量并运行Discord客户端。
    """
    print("🚀 正在启动Discord消息导出工具...")
    # 验证token和guild ID是否设置
    if not TOKEN:
        print("❌ 环境变量或.env文件中未设置DISCORD_TOKEN！")
        return
    if not GUILD_ID:
        print("❌ 环境变量或.env文件中未设置DISCORD_GUILD_ID！")
        return

    # 尝试将GUILD_ID转换为int以尽早捕获错误
    try:
        int(GUILD_ID)
    except ValueError:
        print(f"❌ DISCORD_GUILD_ID ('{GUILD_ID}') 不是有效的整数！")
        return

    print("🔑 凭据已加载。")
    client = DiscordMessageExporter(intents=intents)

    try:
        client.run(TOKEN)
    except discord.errors.LoginFailure:
        print("❌ Discord登录失败：请仔细检查您的DISCORD_TOKEN。")
    except discord.errors.PrivilegedIntentsRequired:
        print("❌ 需要特权意图：确保在Discord开发者门户中为您的机器人启用了'MESSAGE CONTENT INTENT'。")
    except Exception as e:
        print(f"❌ 运行客户端时发生意外错误: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    main()
