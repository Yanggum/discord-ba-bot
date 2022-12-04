import asyncio
import datetime

import disnake
from disnake.ext import commands
import requests
import json
import sys
import time
import typing
import functools
import logging
import os
from os import environ
from dotenv import load_dotenv

load_dotenv()

from discord.ext.commands import bot, command


# charcater num
class KibotosStudent:
    def __init__(self, name, full_name, inc_id, std_id, token, role, error_msg, short_name, status, thumbnail):
        self.name = name
        self.full_name = full_name
        self.inc_id = inc_id
        self.std_id = std_id
        self.token = token
        self.role = role
        self.error_msg = error_msg
        self.short_name = short_name
        self.status = status
        self.thumbnail = thumbnail


students = []
current_student_name = ""
current_student_token = ""
current_student_id = ""
current_student_role = ""
current_student_error_msg = ""
current_student_short_name = ""
current_student_full_name = ""
current_student_inc_id = ""
current_student_std_id = ""
current_student = KibotosStudent(
    "saori", "조마에 사오리", "1", 0,
    "", 0,
    "", "사오리", "1", "")


#


def blocking_func(a, b, c=1):
    """A very blocking function"""
    time.sleep(a + b + c)
    return "some stuff"


async def run_blocking(blocking_func: typing.Callable, *args, **kwargs) -> typing.Any:
    """Runs a blocking function in a non-blocking way"""
    func = functools.partial(blocking_func, *args,
                             **kwargs)  # `run_in_executor` doesn't support kwargs, `functools.partial` does
    return await bot.loop.run_in_executor(None, func)


async def shot_message(message, character, target_url):
    url = base_url + target_url

    payload = json.dumps({
        "charNo": character.inc_id,
        "chatRoomNo": character.inc_id,
        "chatCont": message,
        "regId": "",
        "regDt": "",
        "updId": "",
        "updDt": ""
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return json.loads(response.text)


async def load_students():
    url = base_url + "/chat/load_students"
    local_students = []

    payload = json.dumps({
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    response_list = json.loads(response.text)

    for item in response_list:
        student = KibotosStudent(item["name"], item["full_name"], item["inc_id"], item["std_id"], item["token"],
                                 item["role"], item["error_msg"], item["short_name"], item["status"], item["thumbnail"])
        local_students.append(student)

    return local_students


async def init():
    global students
    global current_student_name
    global current_student_token
    global current_student_id
    global current_student
    # global client
    students = await load_students()

    for student in students:
        # inc로 치환!
        if arguments[1] == student.inc_id:
            current_student_name = student.name
            logging.basicConfig(filename=student.name + '.log', encoding='utf-8', level=logging.DEBUG)

            # For test
            logging.debug(student.name + " is selected.")
            logging.debug("Student list is loaded.")
            current_student = student

            current_student_token = student.token
            current_student_id = student.std_id
            break


arguments = sys.argv

if arguments[1] == 'exit':
    os.exit()

logging.debug("arguments: ", arguments[1])
base_url = environ["BASE_URL"]
chat_url = "/chat"
error_raise_url = "/chat/error_raise"

command_sync_flags = commands.CommandSyncFlags.default()
command_sync_flags.sync_commands_debug = True

bot = commands.Bot(
    command_sync_flags=command_sync_flags,
    command_prefix="!",
)

asyncio.run(init())


@bot.event
async def on_ready():
    activity = disnake.Game(current_student.status)
    activity.name = current_student.status
    await bot.change_presence(status=disnake.Status.online, activity=activity)
    print(f'We have logged in as {bot.user}')


@bot.event
async def on_message(message):
    return


@bot.event
async def on_command(ctx: commands.Context) -> None:
    await ctx.me.send(ctx.args[1])
    return


@bot.command(
    name=current_student.name, description="채팅을 보냅니다.")
async def c(ctx: commands.Context, arg) -> None:
    if ctx.bot.application_id == current_student_id and len(arg) > 0:
        mention_id = ""
        message = arg[0]
        logging.debug("mention_id = " + mention_id)
        my_message = message

        logging.debug("my_message = " + my_message)
        result = await shot_message(my_message, current_student, chat_url)

        try:
            result = result["message"]

            if result.__contains__("선생님:") or result.__contains__(current_student.short_name + ":"):
                raise Exception("잘못된 구문")

            # r = await run_blocking(blocking_func, 1, 2, c=3)
            # logging.debug(r)  # -> "some stuff"
            await ctx.send(result)
        except Exception as e:
            logging.debug(e)
            # r = await run_blocking(blocking_func, 1, 2, c=3)
            # logging.debug(r)  # -> "error stuff"
            await shot_message(current_student.error_msg, current_student, error_raise_url)
            await ctx.send(current_student.error_msg)


@bot.slash_command(
    name=current_student.name + "s", description="슬래쉬 채팅을 보냅니다.",
)
async def ping_slash(inter: disnake.ApplicationCommandInteraction,
                     message: str) -> None:
    # if inter.bot.application_id == current_student_id:

    mention_id = ""
    logging.debug("mention_id = " + mention_id)
    my_message = message

    logging.debug("my_message = " + my_message)
    await inter.response.defer()
    result = await shot_message(my_message, current_student, chat_url)

    try:
        result = result["message"]

        if result.__contains__("선생님:") or result.__contains__(current_student.short_name + ":"):
            raise Exception("잘못된 구문")

        # r = await run_blocking(blocking_func, 1, 2, c=3)
        # logging.debug(r)  # -> "some stuff"
        teacher_embed = disnake.Embed(
            title="선생님",
            description=my_message,
            colour=0x1DA0F2,
            timestamp=datetime.datetime.now(),
        )

        student_embed = disnake.Embed(
            title=current_student.short_name,
            description=result,
            colour=0x1DA0F2,
            timestamp=datetime.datetime.now(),
        )

        student_embed.set_thumbnail(url=current_student.thumbnail)

        await inter.send(embeds=[teacher_embed, student_embed])

    except Exception as e:
        logging.debug(e)
        # r = await run_blocking(blocking_func, 1, 2, c=3)
        # logging.debug(r)  # -> "error stuff"
        teacher_embed = disnake.Embed(
            title="선생님",
            description=my_message,
            colour=0x1DA0F2,
            timestamp=datetime.datetime.now(),
        )

        student_embed = disnake.Embed(
            title=current_student.short_name,
            description=result,
            colour=0x1DA0F2,
            timestamp=datetime.datetime.now(),
        )

        student_embed.set_thumbnail(url=current_student.thumbnail)

        await inter.response.defer()
        await shot_message(current_student.error_msg, current_student, error_raise_url)
        await inter.send(embeds=[teacher_embed, student_embed])


# @chit_chat.autocomplete("language")
# async def language_autocomp(inter: disnake.ApplicationCommandInteraction, user_input: str):
#     languages = ("korean", "english", "german", "spanish", "japanese")
#     return [user_input]


bot.run(current_student_token)
