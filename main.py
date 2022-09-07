import asyncio
import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from datetime import datetime
import logging
import random

logging.basicConfig(level=logging.WARNING)
MSGQ: list = []
ANONCHAN = None
FLOODFILTER: list = []
TIMEOUT: int = 30

bot = commands.Bot(command_prefix="?", case_insensitive=True)


def compose_embed(color, name: str, content: str) -> discord.Embed:
    msg = discord.Embed(title="Anonybot", description="", color=color)
    msg.add_field(name=name, value=content, inline=False)
    return msg


def randcol() -> discord.Colour:
    col: discord.Colour = discord.Colour.from_rgb(
        random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
    )
    return col


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    raise error


async def anonmsg():
    global MSGQ, ANONCHAN, TIMEOUT
    while True:
        if len(MSGQ) > 0:
            try:
                msg: str = MSGQ.pop(0)
                emsg: discord.Embed = compose_embed(randcol(), "Anon", msg)
                await ANONCHAN.send(embed=emsg)
                await asyncio.sleep(TIMEOUT)
            except UnicodeEncodeError:
                await ANONCHAN.send(
                    "Sadly, emotes are not supported (yet)(you know who you are)"
                )
        await asyncio.sleep(TIMEOUT / 3)


@bot.event
async def on_ready():
    now = datetime.now()
    server_count: int = len(bot.guilds)
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="{} servers | ?help".format(server_count),
        )
    )
    date_time = now.strftime("%d/%m/%y, %H:%M:%S")
    if not hasattr(bot, "appinfo"):
        bot.appinfo = await bot.application_info()
    print("Bot initialized at {}\n".format(date_time))
    print(
        "id: {}\nname: {}\nowner: {}\nauthor: github.com/ZexZee\t\t@Zetty#4088\n".format(
            bot.appinfo.id, bot.appinfo.name, bot.appinfo.owner
        )
    )
    with open("log.txt", "a+") as lf:
        lf.write("BOT START {}\n".format(date_time))
    bot.loop.create_task(anonmsg())


@bot.event
async def on_disconnect():
    now = datetime.now()
    date_time = now.strftime("%d/%m/%y, %H:%M:%S")
    print("Bot lost connection at {}\n".format(date_time))
    with open("log.txt", "a+") as lf:
        lf.write("BOT LOST CONNECTION {}\n".format(date_time))


async def _flood_remove(id, channel) -> None:
    global FLOODFILTER, TIMEOUT
    await asyncio.sleep(TIMEOUT)
    FLOODFILTER.remove(id)
    await channel.send("You can now submit again!")


@bot.event
async def on_message(message):
    global MSGQ, ANONCHAN, FLOODFILTER
    now = datetime.now()
    date_time = now.strftime("%d/%m/%y, %H:%M:%S")
    author = message.author
    _ls: str = ""
    if hasattr(message.channel, "name"):
        _ls = "[{}]@{} ({}) {}: {}".format(
            date_time, message.channel.name, author.id, author.name, message.content
        )
    else:
        _ls = "[{}]@DM ({}) {}: {}".format(
            date_time, author.id, author.name, message.content
        )
    print(_ls)
    with open("log.txt", "a+") as lf:
        try:
            lf.write(_ls + "\n")
        except UnicodeEncodeError:
            lf.write(
                "[{}] ({}) {}: <unsupported unicode>\n".format(
                    date_time, author.id, author.name
                )
            )
    if author.id in FLOODFILTER and message.channel == author.dm_channel:
        await author.dm_channel.send("Please wait, spamming harms the bot.")
    if not author.bot and not author.id in FLOODFILTER:
        if message.channel == author.dm_channel:
            FLOODFILTER.append(author.id)
            MSGQ.append(message.content)
            print("Added message to anon queue")
            await _flood_remove(author.id, author.dm_channel)
    await bot.process_commands(message)


bot.remove_command("help")


@bot.command(aliases=["h", "info", "commands", "c"])
async def help(ctx):
    author = ctx.message.author
    if author.dm_channel == None:
        await ctx.message.author.create_dm()
    helpmsg: discord.Embed = compose_embed(
        0x994400,
        "Help",
        "DM the bot your anon message, and the bot will post it (might be some timelag).",
    )
    await author.dm_channel.send(embed=helpmsg)


@bot.command()
async def designate(ctx):
    global ANONCHAN
    if ctx.message.author.top_role.permissions.administrator:
        ANONCHAN = ctx.message.channel
        await ANONCHAN.send("Designated {} as the anon channel!".format(ANONCHAN.name))
    else:
        print("Illegal permissions, no change was made.")


def main() -> None:
    global bot, TOKEN
    with open("token", "r") as tf:
        TOKEN = tf.readline()
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
