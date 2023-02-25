import asyncio
import time

import pyrogram.filters
from pyrogram.handlers import MessageHandler
from config import songs, api_id, api_hash, number
from pyrogram.types import Message
from pyrogram import Client
from pytgcalls import idle
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped, VideoPiped
import pytgcalls.exceptions
from pyrogram.enums.parse_mode import ParseMode
from mutagen.mp3 import MP3
from urllib.request import urlopen
from asyncio import sleep

app = Client(number, api_id=api_id, api_hash=api_hash)
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
    if round(time.time() - last_message_time) > 10:
        global last_song_play_time

        async def send_message(_message: str) -> None:
            """Отправка сообщения в чат."""

            await app.send_message(chat_id=message.chat.id,
                                   text=_message,
                                   parse_mode=ParseMode.MARKDOWN)

        async def play_song(_song_id: int = 0) -> None:
            """Включить трек в видеочат."""

            global last_song_play_time

            try:
                interval = round(time.time() - last_song_play_time)
                me = await app.get_me()

                # Cooldown
                if interval > 150 or message.from_user.id == me.id:
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
                    with open('./song.mp3', 'wb') as output:
                        output.write(raw_song.read())

                    # Get song length
                    song_file = open('./song.mp3', 'rb')
                    song = MP3(song_file)
                    song_length = round(song.info.length)

                    # Close files
                    song.clear()
                    song_file.close()

                    # Play next song
                    await asyncio.sleep(song_length)
                    await play_song(next_track())
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

        if message.text:
            if message.text.startswith('/stream'):
                """Запуск стрима."""
                try:
                    await send_message('🎸 Запуск трансляции\n\n'
                                       '🎧 `/song {}`'.format(now_song_index + 1))
                    await tg_calls_app.start()

                except pytgcalls.exceptions.PyTgCallsAlreadyRunning:
                    ...

                except pytgcalls.exceptions.AlreadyJoinedError:
                    await send_message('📻 Радио уже запущено.')

                except pytgcalls.exceptions.NoActiveGroupCall:
                    await send_message('📞 Запустите групповой видеочат.')

                await play_song()

            elif message.text == '/next':
                """Следующий трек."""

                track_index = next_track()
                await play_song(track_index)

            elif message.text.startswith('/song '):
                """Включить трек по номеру."""

                song_id = message.text.split('/song ')
                if 1 < len(song_id) < len(songs) - 1:
                    song_id = song_id[1]
                    if song_id.isdigit():
                        await play_song(int(song_id))
                    else:
                        await send_message('⏸️ Укажи номер трека в виде числа')

            # elif message.text == '/stop':
            #     await send_message('⏸️ Stopped stream')
            #     await tg_calls_app.leave_group_call(message.chat.id)


app.add_handler(MessageHandler(commands_handler))
app.run()
idle()
