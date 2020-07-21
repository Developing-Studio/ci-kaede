import json
import logging
import os
import sys
import traceback
from typing import Optional

import aiohttp
import discord
from bs4 import BeautifulSoup
from bs4.element import Tag
from discord.ext import commands
from discord.utils import escape_markdown, escape_mentions

import cogs.administration.modlog


def sanitize(s):
    return escape_mentions(escape_markdown(s))


class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.modlog: Optional[cogs.administration.modlog.ModLog] = None
        bot.loop.create_task(self._init())

    async def _init(self):
        logging.info("[MISC] Waiting for bot")
        await self.bot.wait_until_ready()
        self.modlog = self.bot.get_cog("ModLog")
        logging.info("[MISC] Ready")

    @commands.command()
    async def tiktok(self, ctx: commands.Context, link: str):
        """
        Sends a downloadable mp4 from a tiktok link
        example: https://www.tiktok.com/@arrowfur/video/6824287334876368134?lang=en
        """
        spl = link.strip("/").split("/")
        if len(spl) < 5:
            user = spl[-1]
        else:
            user = spl[-3].strip("@")
        id = spl[-1].split("?")[0]
        fn = f"{user}-{id}"
        tmp = f"tmp/{fn}.html"
        res = f"tmp/{fn}.mp4"
        print(f" @{user} #{id} {link}")
        async with aiohttp.ClientSession() as sess:
            async with sess.get(link,
                                headers={
                                    "User-Agent":
                                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 "
                                        "(KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}) as resp:
                print(f" Writing to {tmp}...", end="")
                with open(tmp, "wb") as fp:
                    fp.write(await resp.content.read())

        print(" Making s o u p...", end="")
        with open(tmp, encoding="utf-8") as fp:
            soup = BeautifulSoup(fp, features="html.parser")

        print(" Removing")
        os.remove(tmp)

        print(" Searching for video object...", end="")
        video_object: Tag = soup.find_all(id="videoObject")[0]
        js = json.loads(video_object.contents[0])
        content_url = js["contentUrl"]
        vid_url = js["url"]
        name = js["name"][:100]
        user = js["creator"]["name"]
        alt = js["creator"].get("alternateName", "")
        print(content_url)

        print(" Saving...", end="")
        async with aiohttp.ClientSession() as sess:
            async with sess.get(content_url) as resp:
                with open(res, "wb") as fp:
                    fp.write(await resp.content.read())
        print(f" Saved as {res}")
        await ctx.send(content= # noqa E251
                       f"Video by: @{alt} ({user})\n"
                       f"{sanitize(name)}\n"
                       f"<{vid_url}>",
                       file=discord.File(res))
        os.remove(res)

    @tiktok.error
    async def tiktok_error(self, ctx, error: Exception):
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        await ctx.send("An error occurred while running the command.")
        await self.modlog.log_message("Error in tiktok command", f"{error}")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Misc(bot))


"""
import json
import os

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

links = []
while True:
    link = input("link> ")
    if link == ".":
        break
    links.append(link)

total = len(links)

for num, link in enumerate(links):
    user = link.split("/")[-3].strip("@")
    id = link.split("/")[-1]
    fn = f"{user}-{id}"
    tmp = f"tmp/{fn}.html"
    res = f"results/{fn}.mp4"
    print(f"Getting {num+1}/{total}")
    print(f" @{user} #{id} {link}")
    resp = requests.get(link,
                        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 "
                                               "(KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"})

    print(f" Writing to {tmp}...", end="")
    with open(tmp, "wb") as fp:
        fp.write(resp.content)

    print(f" Making s o u p...", end="")
    with open(tmp, encoding="utf-8") as fp:
        soup = BeautifulSoup(fp, features="html.parser")

    print(f" Removing")
    os.remove(tmp)

    print(f" Searching for video object...", end="")
    video_object: Tag = soup.find_all(id="videoObject")[0]
    content_url = json.loads(video_object.contents[0])["contentUrl"]
    print(content_url)

    print(" Saving...", end="")
    with open(res, "wb") as fp:
        fp.write(requests.get(content_url).content)
    print(f" Saved as {res}")

"""
