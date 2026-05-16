import sys
try:
    import audioop
except ModuleNotFoundError:
    import audioop_lts as audioop
    sys.modules["audioop"] = audioop

import discord
import asyncio
import os
from gtts import gTTS
import tempfile

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True

client = discord.Client(intents=intents)


async def speak_in_channel(voice_channel, text):
    """Join a voice channel, speak the TTS message, then leave."""
    voice_client = None
    try:
        # Join the voice channel
        voice_client = await voice_channel.connect()

        # Generate TTS audio
        tts = gTTS(text=text, lang="en")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tts_path = f.name
        tts.save(tts_path)

        # Play the audio
        voice_client.play(discord.FFmpegPCMAudio(tts_path))

        # Wait for audio to finish
        while voice_client.is_playing():
            await asyncio.sleep(0.5)

    except Exception as e:
        print(f"Error in speak_in_channel: {e}")
    finally:
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
        try:
            os.remove(tts_path)
        except Exception:
            pass


@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("Bot is ready and listening for voice joins.")


@client.event
async def on_voice_state_update(member, before, after):
    # Ignore bot accounts
    if member.bot:
        return

    # User joined a voice channel (wasn't in one before, or moved to a new one)
    if after.channel is not None and before.channel != after.channel:
        channel = after.channel
        display_name = member.display_name
        message = f"{display_name} joined the voice chat"
        print(f"Announcing: {message}")

        # Avoid joining if bot is already in this channel
        for vc in client.voice_clients:
            if vc.channel == channel:
                return  # Already connected, skip

        await speak_in_channel(channel, message)


TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable not set!")

client.run(TOKEN)
