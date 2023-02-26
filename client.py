from urllib.request import urlopen

import pytgcalls.exceptions
from mutagen.mp3 import MP3
from pyrogram import Client
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls import idle
from pytgcalls.types import AudioPiped

import asyncio
import time

from config import songs, api_id, api_hash, number

app = Client(number,
             api_id=api_id,
             api_hash=api_hash,
             workdir='./source')
tg_calls_app = PyTgCalls(app)

now_song_index = 0
last_song_play_time = time.time()
last_message_time = time.time()


def next_track():
    global now_song_index
    if now_song_index + 1 <= len(songs):
        now_song_index += 1
    else:
        now_song_index = 0
    return now_song_index


async def commands_handler(client, message: Message):
    global last_song_play_time, now_song_index

    async def send_message(_message: str) -> None:
        """Отправка сообщения в чат."""

        await app.send_message(chat_id=message.chat.id,
                               text=_message,
                               parse_mode=ParseMode.MARKDOWN)

    async def play_song(_song_id: int = 0, notification: bool = True) -> None:
        """Play song in videochat."""

        global last_song_play_time

        try:
            interval = round(time.time() - last_song_play_time)
            me = await app.get_me()

            # Cooldown
            if interval > 150 or message.from_user.id == me.id:
                if notification:
                    await send_message('🎧 `/song {}`'.format(_song_id))

                # Replay songs
                await tg_calls_app.leave_group_call(message.chat.id)
                await tg_calls_app.join_group_call(
                    message.chat.id,
                    stream=AudioPiped(
                        songs[_song_id],
                    ),
                )

                # Open .mp3 with link
                raw_song = urlopen(songs[track_index])

                # Download song
                with open('./source/song.mp3', 'wb') as output:
                    output.write(raw_song.read())

                # Get song length
                song_file = open('./source/song.mp3', 'rb')
                song = MP3(song_file)
                song_length = round(song.info.length)

                # Close files
                song.clear()
                song_file.close()

                # Play next song
                await asyncio.sleep(song_length)

                _track_index = next_track()
                if _track_index >= len(songs):
                    _track_index = 0

                await play_song(track_index, notification=False)
            else:
                await send_message('📻 Повторите запрос через {} секунд.'.format(180 - interval))

        except IndexError:
            await send_message(
                '🎧 Трека #{} не существует. Максимальный номер трека, - {}.'.format(_song_id + 1, len(songs)))

        except pytgcalls.exceptions.AlreadyJoinedError:
            ...

        except pytgcalls.exceptions.NodeJSNotRunning:
            await tg_calls_app.start()
            await send_message('📻 Повторите запрос. Сервер запущен.')

        except pytgcalls.exceptions.NotInGroupCallError:
            await send_message('🎧 `/song {}`'.format(_song_id + 1))
            await tg_calls_app.join_group_call(
                message.chat.id,
                stream=AudioPiped(
                    songs[_song_id],
                ),
            )
            last_song_play_time = time.time()

    if message.text and round(time.time() - last_message_time) > 10:
        if message.text.startswith('/stream'):
            # Run stream.
            try:
                now_song_index = 0
                await send_message('🎸 Запуск трансляции\n\n'
                                   '🎧 `/song {}`'.format(now_song_index + 1))
                await tg_calls_app.start()
                await play_song()

            except pytgcalls.exceptions.PyTgCallsAlreadyRunning:
                ...

            except pytgcalls.exceptions.AlreadyJoinedError:
                await send_message('📻 Радио уже запущено.')

            except pytgcalls.exceptions.NoActiveGroupCall:
                await send_message('📞 Запустите групповой видеочат.')

        elif message.text == '/next':
            # Next song.

            track_index = next_track()
            await play_song(track_index)

        elif message.text.startswith('/song '):
            # Play song with number.

            song_id = message.text.split('/song ')
            if 0 < len(song_id) < len(songs):
                song_id = song_id[1]
                if song_id.isdigit():
                    await play_song(int(song_id))
                else:
                    await send_message('⏸️ Укажи номер трека в виде числа')

        # elif message.text == '/stop':
        #     # Stop stream.
        #     await send_message('⏸️ Stopped stream')
        #     await tg_calls_app.leave_group_call(message.chat.id)


app.add_handler(MessageHandler(commands_handler))  # Register handler.
app.run()  # Run pyrogram client.
idle()