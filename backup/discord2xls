import os
import discord
import asyncio
import pandas as pd
from dotenv import load_dotenv

# Load environment variables for sensitive information
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
            print(f"🔗 Logged in as {self.user}")
            guild = self.get_guild(int(GUILD_ID))

            if not guild:
                print("❌ Server not found!")
                await self.close()
                return

            # List available text channels
            text_channels = guild.text_channels
            print("\n📜 Available Channels:")
            for index, channel in enumerate(text_channels, 1):
                print(f"{index}. {channel.name} (ID: {channel.id})")

            # Let the user select a channel
            selected_index = self.get_channel_selection(text_channels)
            
            if selected_index is None:
                return

            channel = text_channels[selected_index]
            await self.export_channel_messages(channel)

        except Exception as e:
            print(f"❌ An error occurred: {e}")
        finally:
            await self.close()

    def get_channel_selection(self, text_channels):
        try:
            selected_index = int(input("\nEnter the number of the channel to export messages: ")) - 1

            if selected_index < 0 or selected_index >= len(text_channels):
                print("❌ Invalid selection!")
                return None

            return selected_index
        except ValueError:
            print("❌ Please enter a valid number!")
            return None

    async def export_channel_messages(self, channel):
        print(f"\n📥 Fetching messages from: {channel.name}")

        messages = []
        message_count = 0
        
        async for msg in channel.history(limit=None):
            # Convert timezone-aware datetime to timezone-naive
            timestamp = msg.created_at.replace(tzinfo=None)
            
            messages.append({
                "User ID": msg.author.id,
                "Username": msg.author.name,
                "Display Name": msg.author.display_name,
                "Message": msg.content,
                "Timestamp": timestamp,  # Now timezone-naive
                "Message ID": msg.id
            })
            message_count += 1

            # Optional: Add a progress indicator for large channels
            if message_count % 100 == 0:
                print(f"Fetched {message_count} messages...")

        if messages:
            # Save to an Excel file with enhanced filename
            filename = f"{channel.name}_messages_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df = pd.DataFrame(messages)
            
            # Optional: Sort messages by timestamp
            df.sort_values('Timestamp', inplace=True)
            
            df.to_excel(filename, index=False, engine="openpyxl")

            print(f"✅ Export complete: {filename}")
            print(f"ℹ️ Total messages exported: {message_count}")
        else:
            print(f"⚠️ No messages found in {channel.name}")

def main():
    # Validate token and guild ID are set
    if not TOKEN or not GUILD_ID:
        print("❌ Discord TOKEN or GUILD_ID not set in environment variables!")
        return

    client = DiscordMessageExporter(intents=intents)
    client.run(TOKEN)

if __name__ == '__main__':
    main()
