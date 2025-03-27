import discord
import csv
import asyncio

TOKEN = "你的机器人token"
GUILD_ID = 1004236876403703900  # 你的服务器ID

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"🔗 已连接为 {client.user}")
    guild = client.get_guild(GUILD_ID)

    if not guild:
        print("❌ 未找到服务器！")
        return

    for channel in guild.text_channels:
        print(f"📥 正在导出消息来自: {channel.name}")
        messages = []
        
        try:
            async for msg in channel.history(limit=None):
                messages.append([msg.id, msg.author.name, msg.content, msg.created_at.strftime("%Y-%m-%d %H:%M:%S")])

            if messages:
                filename = f"{channel.name}_messages.csv"
                with open(filename, "w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(["ID", "作者", "消息", "日期"])
                    writer.writerows(messages)

                print(f"✅ 导出完成: {filename}")
            else:
                print(f"⚠️ 频道 {channel.name} 中没有消息")

        except discord.Forbidden:
            print(f"🚫 没有权限访问 {channel.name}")

    await client.close()

client.run(TOKEN)