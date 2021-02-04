"""Spoilers cog
Filters out messages that start with a certain prefix, and store them for
later retrieval.
"""

from datetime import datetime, timedelta
import logging
import json
import os
import re
import discord
from discord.ext import commands

from redbot.core import Config, checks, commands, data_manager
from redbot.core.commands.context import Context
from redbot.core.bot import Red

# Global variables
KEY_MESSAGE = "message"
KEY_AUTHOR_ID = "authorid"
KEY_AUTHOR_NAME = "author"
KEY_TIMESTAMP = "timestamp"
KEY_EMBED = "embed"
LOGGER = None
PREFIX = "spoiler"
COOLDOWN = 60

BASE = { "messages": {} }

class Spoilers(commands.Cog)
    """Store messages for later retrieval."""

    #Class constructor
    def __init__(self, bot: Red):
        self.bot = bot

        self.config = Config.get_conf(self, identifier=5842647, force_registration=True)
        # Register default (empty) settings.
        self.config.register_global(**BASE)
        self.onCooldown = {}

        # Initialize logger, and save to cog folder.
        saveFolder = data_manager.cog_data_path(cog_instance=self)
        self.logger = logging.getLogger("red.luicogs.Spoilers")
        if self.logger.level == 0:
            # Prevents the self.logger from being loaded again in case of module reload.
            self.logger.setLevel(logging.INFO)
            handler = logging.FileHandler(
                filename=str(saveFolder) + "/info.log", encoding="utf-8", mode="a"
            )
            handler.setFormatter(
                logging.Formatter("%(asctime)s %(message)s", datefmt="[%d/%m/%Y %H:%M:%S]")
            )
            self.logger.addHandler(handler)

    @commands.command(name="spoiler")
    async def spoiler(self, ctx: Context, *, msg: str):
        """Create a message spoiler."""
        wordFilter = self.bot.get_cog("WordFilter")
        if not wordFilter:
            await ctx.send("This cog requires the word filter cog to be loaded. Please load "
                           "the cog and try again")
            return
        if wordFilter.containsFilterableWords(ctx.message):
            await ctx.send("You have filtered words in your spoiler!  Please "
                           "check it and try again!")
            return

        try:
            store = {}
            store[KEY_MESSAGE] = msg
            store[KEY_AUTHOR_ID] = str(ctx.message.author.id)
            store[KEY_AUTHOR_NAME] = "{0.name}#{0.discriminator}".format(ctx.message.author)
            store[KEY_TIMESTAMP] = ctx.message.timestamp.strftime("%s")
            if ctx.message.embeds:
                data = discord.Embed.from_data(ctx.message.embeds[0])
                if data.type == 'image':
                    store[KEY_EMBED] = data.url
            else:
                imglinkPattern = r"(?i)http[^ ]+\.(?:png|jpg|jpeg|gif)"
                match = re.search(imglinkPattern, msg)
                if match:
                    store[KEY_EMBED] = match.group(0)
            await self.bot.delete_message(ctx.message)
            newMsg = await ctx.send(":warning: {} created a spoiler!  React to see "
                                    "the message!".format(ctx.message.author.mention))

            async with self.config.messages() as messages:
                messages[str(newMsg.id)] = store
            await newMsg.add_reaction("\N{INFORMATION SOURCE}")
            self.logger.info("%s#%s (%s) added a spoiler: %s",
                             ctx.message.author.name,
                             ctx.message.author.discriminator,
                             ctx.message.author.id,
                             msg)
        except discord.errors.Forbidden as error:
            await ctx.send("I'm not able to do that.")
            await newMsg.delete()
            self.logger.error("Could not create a spoiler in server %s channel %s",
                              ctx.message.server.name,
                              ctx.message.channel.name)
            self.logger.error(error)

    async def checkForReaction(self, data):
        """Reaction listener (using socket data)
        Checks to see if a spoilered message is reacted, and if so, send a DM to the
        user that reacted.
        """
        # no binary frames
        if isinstance(data, bytes):
            return

        data = json.loads(data)
        event = data.get("t")
        payload = data.get("d")
        if event not in ("MESSAGE_REACTION_ADD", "MESSAGE_REACTION_REMOVE",
                         "MESSAGE_REACTION_REMOVE_ALL"):
            return

        isReaction = event == "MESSAGE_REACTION_ADD"

        # make sure the reaction is proper
        if isReaction:
            msgId = payload["message_id"]
            if msgId in self.messages.keys():
                server = discord.utils.get(self.bot.servers,
                                           id=payload["guild_id"])
                reactedUser = discord.utils.get(server.members,
                                                id=payload["user_id"])
                if reactedUser.bot:
                    return

                channel = discord.utils.get(server.channels,
                                            id=payload["channel_id"])
                message = await self.bot.get_message(channel, msgId)

                if payload["emoji"]["id"]:
                    emoji = discord.Emoji(name=payload["emoji"]["name"],
                                          id=payload["emoji"]["id"],
                                          server=server)
                else:
                    emoji = payload["emoji"]["name"]
                await self.bot.remove_reaction(message, emoji, reactedUser)

                if (msgId in self.onCooldown.keys() and
                        reactedUser.id in self.onCooldown[msgId].keys() and
                        self.onCooldown[msgId][reactedUser.id] > datetime.now()):
                    return
                msg = self.messages[msgId]
                embed = discord.Embed()
                userObj = discord.utils.get(server.members,
                                            id=msg[KEY_AUTHOR_ID])
                if userObj:
                    embed.set_author(name="{0.name}#{0.discriminator}".format(userObj),
                                     icon_url=userObj.avatar_url)
                else:
                    embed.set_author(name=msg[KEY_AUTHOR_NAME])
                if KEY_EMBED in msg:
                    embed.set_image(url=msg[KEY_EMBED])
                embed.description = msg[KEY_MESSAGE]
                embed.timestamp = datetime.fromtimestamp(int(msg[KEY_TIMESTAMP]))
                try:
                    await self.bot.send_message(reactedUser, embed=embed)
                    if msgId not in self.onCooldown.keys():
                        self.onCooldown[msgId] = {}
                    self.onCooldown[msgId][reactedUser.id] = (datetime.now() +
                                                              timedelta(seconds=COOLDOWN))
                except (discord.errors.Forbidden, discord.errors.HTTPException) as error:
                    LOGGER.error("Could not send DM to %s#%s (%s).",
                                 reactedUser.name,
                                 reactedUser.discriminator,
                                 reactedUser.id)
                    LOGGER.error(error)

def setup(bot):
    """Add the cog to the bot."""
    checkFolder()   # Make sure the data folder exists!
    checkFiles()    # Make sure we have settings!
    spoilersCog = Spoilers(bot)
    global LOGGER # pylint: disable=global-statement
    LOGGER = logging.getLogger("red.Spoilers")
    if LOGGER.level == 0:
        # Prevents the LOGGER from being loaded again in case of module reload.
        LOGGER.setLevel(logging.INFO)
        handler = logging.FileHandler(filename="data/lui-cogs/spoilers/info.log",
                                      encoding="utf-8",
                                      mode="a")
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s",
                                               datefmt="[%d/%m/%Y %H:%M:%S]"))
        LOGGER.addHandler(handler)
    bot.add_listener(spoilersCog.checkForReaction, "on_socket_raw_receive")
    bot.add_cog(spoilersCog)
