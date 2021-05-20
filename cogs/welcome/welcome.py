"""Welcome cog
Sends welcome DMs to users that join the server.
"""

import asyncio
import discord
import logging
import random

from redbot.core import Config, checks, commands, data_manager
from redbot.core.bot import Red
from redbot.core.commands.context import Context
from redbot.core.utils.chat_formatting import error, pagify, warning
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu
from redbot.core.utils import AsyncIter

LOGGER = logging.getLogger("red.luicogs.Welcome")

KEY_DM_ENABLED = "dmEnabled"
KEY_LOG_JOIN_ENABLED = "logJoinEnabled"
KEY_LOG_JOIN_CHANNEL = "logJoinChannel"
KEY_LOG_LEAVE_ENABLED = "logLeaveEnabled"
KEY_LOG_LEAVE_CHANNEL = "logLeaveChannel"
KEY_TITLE = "title"
KEY_MESSAGE = "message"
KEY_IMAGE = "image"
GREETINGS = []

DEFAULT_GUILD = {
    KEY_DM_ENABLED: False,
    KEY_LOG_JOIN_ENABLED: False,
    KEY_LOG_JOIN_CHANNEL: None,
    KEY_LOG_LEAVE_ENABLED: False,
    KEY_LOG_LEAVE_CHANNEL: None,
    KEY_TITLE: "Welcome!",
    KEY_MESSAGE: "Welcome to the server! Hope you enjoy your stay!",
    KEY_IMAGE: None,
    "greetings": [],
    "KEY_WELCOME_CHANNEL": None,
    "KEY_WELCOME_CHANNEL_SET": False,
}



class Welcome(commands.Cog):  # pylint: disable=too-many-instance-attributes
    """Send a welcome DM on server join."""

    # Class constructor
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=5842647, force_registration=True)
        self.config.register_guild(**DEFAULT_GUILD)


    async def getRandomMessage(self, guild):
        greetings = await self.config.guild(guild).greetings()
        numGreetings = len(greetings)
        if(numGreetings == 0):
            return "Welcome to the server {USER}"
        else:
            return greetings[random.randint(0, numGreetings-1)][1]


    # The async function that is triggered on new member join.
    @commands.Cog.listener()
    async def on_member_join(self, newMember: discord.Member):
        guild = newMember.guild
        await self.sendWelcomeMessageChannel(newMember, guild)
        #await self.sendWelcomeMessage(newMember)

    @commands.Cog.listener()
    async def on_member_remove(self, leaveMember: discord.Member):
        await self.logServerLeave(leaveMember)

    #This async function is to look for if the welcome channel was removed
    @commands.Cog.listener()
    async def on_channel_remove(self, removedChannel: discord.TextChannel):
        guild = removedChannel.guild
        #the channel to post welcome stuff in
        welcomeIDSet = await self.config.guild(guild).KEY_WELCOME_CHANNEL_SET()
        welcomeID = await self.config.guild(guild).KEY_WELCOME_CHANNEL()
        #the channel msg should point to
        welcomeLinkIDSet = await self.config.guild(guild).KEY_WELCOME_CHANNEL_LINK_SET()
        welcomeLinkID = await self.config.guild(guild).KEY_WELCOME_CHANNEL_LINK()
        if welcomeIDSet and removedChannel.id == welcomeID:
            await self.config.guild(guild).KEY_WELCOME_CHANNEL_SET.set(False)
        return


    async def sendWelcomeMessageChannel(self, newUser: discord.Member, guild: discord.guild):
        channelID = await self.config.guild(guild).KEY_WELCOME_CHANNEL()
        isSet = await self.config.guild(guild).KEY_WELCOME_CHANNEL_SET()
        #if channel isn't set
        if not isSet:
            return
        channel = discord.utils.get(guild.channels, id=channelID)
        rawMessage = await self.getRandomMessage(guild)
        splitMessage  = rawMessage.split("{USER}")
        message = ""
        for x in range(len(splitMessage)):
            message+=splitMessage[x]
            if(x<len(splitMessage)-1):
                message+=newUser.mention
        fullMessage = f"""{message} Welcome to SFU Anime Club's Discord!

Please check out <#225044755887685632> for all of our basic information and rules, and feel free to introduce yourself with the pinned template in this channel!

We hope you enjoy your stay~

=========================================================="""
        await channel.send(fullMessage)
        return

    async def sendWelcomeMessage(self, newUser, test=False):
        """Sends the welcome message in DM."""
        async with self.config.guild(newUser.guild).all() as guildData:
            if not guildData[KEY_DM_ENABLED]:
                return

            welcomeEmbed = discord.Embed(title=guildData[KEY_TITLE])
            welcomeEmbed.description = guildData[KEY_MESSAGE]
            welcomeEmbed.colour = discord.Colour.red()
            if guildData[KEY_IMAGE]:
                imageUrl = guildData[KEY_IMAGE]
                welcomeEmbed.set_image(url=imageUrl.replace(" ", "%20"))

            channel = discord.utils.get(
                newUser.guild.text_channels, id=guildData[KEY_LOG_JOIN_CHANNEL]
            )

            try:
                await newUser.send(embed=welcomeEmbed)
            except (discord.Forbidden, discord.HTTPException) as errorMsg:
                LOGGER.error(
                    "Could not send message, the user may have"
                    "turned off DM's from this server."
                    " Also, make sure the server has a title "
                    "and message set!",
                    exc_info=True,
                )
                LOGGER.error(errorMsg)
                if guildData[KEY_LOG_JOIN_ENABLED] and not test and channel:
                    await channel.send(
                        ":bangbang: ``Server Welcome:`` User "
                        f"{newUser.name}#{newUser.discriminator} "
                        f"({newUser.id}) has joined. Could not send "
                        "DM!"
                    )
                    await channel.send(errorMsg)
            else:
                if guildData[KEY_LOG_JOIN_ENABLED] and not test and channel:
                    await channel.send(
                        f":o: ``Server Welcome:`` User {newUser.name}#"
                        f"{newUser.discriminator} ({newUser.id}) has "
                        "joined. DM sent."
                    )
                    LOGGER.info(
                        "User %s#%s (%s) has joined.  DM sent.",
                        newUser.name,
                        newUser.discriminator,
                        newUser.id,
                    )

    async def logServerLeave(self, leaveUser: discord.Member):
        """Logs the server leave to a channel, if enabled."""
        async with self.config.guild(leaveUser.guild).all() as guildData:
            if guildData[KEY_LOG_LEAVE_ENABLED]:
                channel = discord.utils.get(
                    leaveUser.guild.text_channels, id=guildData[KEY_LOG_LEAVE_CHANNEL]
                )
                if channel:
                    await channel.send(
                        f":x: ``Server Leave  :`` User {leaveUser.name}#"
                        f"{leaveUser.discriminator} ({leaveUser.id}) has "
                        "left the server."
                    )
                LOGGER.info(
                    "User %s#%s (%s) has left the server.",
                    leaveUser.name,
                    leaveUser.discriminator,
                    leaveUser.id,
                )

    ####################
    # MESSAGE COMMANDS #
    ####################

    # [p]welcome
    @commands.group(name="welcomeset")
    @commands.guild_only()
    @checks.mod_or_permissions()
    async def welcome(self, ctx: Context):
        """Server welcome message settings."""


    @checks.mod_or_permissions()
    @welcome.command(name="channel")
    async def welcomeChannelSet(self, ctx, channel: discord.TextChannel):
        """
        Set the welcome channel

        Parameters:
        -----------
        channel: The text channel to set welcome's to
        """
        if not isinstance(channel, discord.TextChannel):
            return

        await self.config.guild(ctx.guild).KEY_WELCOME_CHANNEL.set(channel.id)
        await self.config.guild(ctx.guild).KEY_WELCOME_CHANNEL_SET.set(True)
        await ctx.send(f"Channel set to {channel}")

        return

    @checks.mod_or_permissions()
    @welcome.command(name="add")
    async def greetAdd(self, ctx, name):
        """
        Add a new greeting, please add name to the passed field. In the message, include '{USER}' for that to be replaced with a ping to the new user

        Parameters:
        -----------
        name: name of the greeting
        """
        def check(message: discord.Message):
            return message.author == ctx.message.author and message.channel == ctx.message.channel

        await ctx.send("What would you like the greeting message to be?")
        try:
            greeting = await self.bot.wait_for("message", check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("No response received, not setting anything!")
            return

        if len(greeting.content) > 2048:
            await ctx.send("Your message is too long!")
            return

        greetings = await self.config.guild(ctx.guild).greetings()

        for greetingTuple in greetings:
            if greetingTuple[0] == name:
                await ctx.send(warning("This greeting already exists, overwrite it? Please type 'yes' to overwrite"))
                try:
                    response = await self.bot.wait_for("message", timeout=30.0, check=check)
                except asyncio.TimeoutError:
                    await ctx.send("You took too long, not overwriting")
                    return

                if response.content.lower() != "yes":
                    await ctx.send("Not overwriting the greeting")
                    return
        #save the greetings
        saveGreeting = (name, greeting.content)
        greetings.append(saveGreeting)
        await greeting.add_reaction('✅')
        await self.config.guild(ctx.guild).greetings.set(greetings)
        return

    @checks.mod_or_permissions()
    @welcome.command(name="remove")
    async def greetRemove(self, ctx, name):
        """
        Removes a greeting. Please pass name of greeting to remove

        Parameters:
        -----------
        name: name of the greeting
        """
        def check(message: discord.Message):
            return message.author == ctx.message.author and message.channel == ctx.message.channel
        greetings = await self.config.guild(ctx.guild).greetings()

        tuple = ()
        for greetingTuple in greetings:
            if greetingTuple[0] == name:
                await ctx.send(warning("Are you sure you wish to delete this greeting? Respond with 'yes' if yes"))
                tuple = greetingTuple
                try:
                    response = await self.bot.wait_for("message", timeout=30.0, check=check)
                except asyncio.TimeoutError:
                    await ctx.send("You took too long, not deleting")
                    return

                if response.content.lower() != "yes":
                    await ctx.send("Not deleting")
                    return
        #delete the greeting
        greetings.remove(tuple)
        await ctx.send(f"{name} removed from list")
        await self.config.guild(ctx.guild).greetings.set(greetings)
        return

    @checks.mod_or_permissions()
    @welcome.command(name="list")
    async def greetList(self, ctx):
        greetings = await self.config.guild(ctx.guild).greetings()

        if len(greetings) == 0:
            await ctx.send("There are no greetings, please add some first!")
            return

        msg = ""
        for greeting in greetings:
            msg += f"{greeting[0]}: {greeting[1]}\n"

        pageList = []
        pages = list(pagify(msg, page_length=500))
        totalPages = len(pages)
        async for pageNumber, page in AsyncIter(pages).enumerate(start=1):
            embed = discord.Embed(
                title=f"Server greetings changes for {ctx.guild.name}", description=page
            )
            embed.set_footer(text=f"Page {pageNumber}/{totalPages}")
            pageList.append(embed)
        await menu(ctx, pageList, DEFAULT_CONTROLS)


    # [p]welcome setmessage
    @welcome.command(name="message", aliases=["msg"])
    async def setmessage(self, ctx: Context):
        """Interactively configure the contents of the welcome DM."""
        await ctx.send("What would you like the welcome DM message to be?")

        def check(message: discord.Message):
            return message.author == ctx.message.author and message.channel == ctx.message.channel

        try:
            message = await self.bot.wait_for("message", check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("No response received, not setting anything!")
            return

        if len(message.content) > 2048:
            await ctx.send("Your message is too long!")
            return

        await self.config.guild(ctx.guild).message.set(message.content)
        await ctx.send("Message set to:")
        await ctx.send(f"```{message.content}```")
        LOGGER.info(
            "Message changed by %s#%s (%s)",
            ctx.message.author.name,
            ctx.message.author.discriminator,
            ctx.message.author.id,
        )
        LOGGER.info(message.content)

    # [p]welcome toggledm
    @welcome.command(name="dm", aliases=["toggledm"])
    async def toggledm(self, ctx: Context):
        """Toggle sending a welcome DM."""
        async with self.config.guild(ctx.guild).all() as guildData:
            if guildData[KEY_DM_ENABLED]:
                guildData[KEY_DM_ENABLED] = False
                isSet = False
            else:
                guildData[KEY_DM_ENABLED] = True
                isSet = True
        if isSet:
            await ctx.send(":white_check_mark: Server Welcome - DM: Enabled.")
            LOGGER.info(
                "Message toggle ENABLED by %s#%s (%s)",
                ctx.message.author.name,
                ctx.message.author.discriminator,
                ctx.message.author.id,
            )
        else:
            await ctx.send(":negative_squared_cross_mark: Server Welcome - DM: " "Disabled.")
            LOGGER.info(
                "Message toggle DISABLED by %s#%s (%s)",
                ctx.message.author.name,
                ctx.message.author.discriminator,
                ctx.message.author.id,
            )

    # [p]welcome togglelog
    @welcome.command(name="log", aliases=["togglelog"])
    async def toggleLog(self, ctx: Context):
        """Toggle sending logs to a channel."""
        async with self.config.guild(ctx.guild).all() as guildData:
            if not guildData[KEY_LOG_JOIN_CHANNEL] or not guildData[KEY_LOG_LEAVE_CHANNEL]:
                await ctx.send(":negative_squared_cross_mark: Please set a log channel first!")
                return
            if guildData[KEY_LOG_JOIN_ENABLED]:
                guildData[KEY_LOG_JOIN_ENABLED] = False
                guildData[KEY_LOG_LEAVE_ENABLED] = False
                isSet = False
            else:
                guildData[KEY_LOG_JOIN_ENABLED] = True
                guildData[KEY_LOG_LEAVE_ENABLED] = True
                isSet = True
        if isSet:
            await ctx.send(":white_check_mark: Server Welcome/Leave - Logging: " "Enabled.")
            LOGGER.info(
                "Welcome channel logging ENABLED by %s#%s (%s)",
                ctx.message.author.name,
                ctx.message.author.discriminator,
                ctx.message.author.id,
            )
        else:
            await ctx.send(
                ":negative_squared_cross_mark: Server Welcome/Leave " "- Logging: Disabled."
            )
            LOGGER.info(
                "Welcome channel logging DISABLED by %s#%s (%s)",
                ctx.message.author.name,
                ctx.message.author.discriminator,
                ctx.message.author.id,
            )

    # [p]welcome logchannel
    @welcome.command(name="logchannel", aliases=["logch"])
    async def setLogChannel(self, ctx: Context, channel: discord.TextChannel = None):
        """Set log channel. Defaults to current channel.

        Parameters:
        -----------
        channel: discord.TextChannel (optional)
            The channel to log member join and leaves. Defaults to current channel.
        """
        if not channel:
            channel = ctx.channel
        async with self.config.guild(ctx.guild).all() as guildData:
            guildData[KEY_LOG_JOIN_CHANNEL] = channel.id
            guildData[KEY_LOG_LEAVE_CHANNEL] = channel.id
        await ctx.send(
            ":white_check_mark: Server Welcome/Leave - Logging: "
            f"Member join/leave will be logged to {channel.name}."
        )
        LOGGER.info(
            "Welcome channel changed by %s#%s (%s)",
            ctx.message.author.name,
            ctx.message.author.discriminator,
            ctx.message.author.id,
        )
        LOGGER.info(
            "Welcome channel set to #%s (%s)", ctx.message.channel.name, ctx.message.channel.id
        )

    # [p]welcome title
    @welcome.command(name="title")
    async def setTitle(self, ctx: Context):
        """Interactively configure the title for the welcome DM."""
        await ctx.send("What would you like the welcome DM title to be?")

        def check(message: discord.Message):
            return message.author == ctx.message.author and message.channel == ctx.message.channel

        try:
            title = await self.bot.wait_for("message", check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("No response received, not setting anything!")
            return

        if len(title.content) > 256:
            await ctx.send("The title is too long!")
            return

        await self.config.guild(ctx.guild).title.set(title.content)
        await ctx.send("Title set to:")
        await ctx.send(f"```{title.content}```")
        LOGGER.info(
            "Title changed by %s#%s (%s)",
            ctx.message.author.name,
            ctx.message.author.discriminator,
            ctx.message.author,
        )
        LOGGER.info(title.content)

    # [p]welcome setimage
    @welcome.command(name="image")
    async def setImage(self, ctx: Context, imageUrl: str = None):
        """Sets an image in the embed with a URL.

        Parameters:
        -----------
        imageUrl: str (optional)
            The URL of the image to use in the DM embed. Leave blank to disable.
        """
        if imageUrl == "":
            imageUrl = None

        await self.config.guild(ctx.guild).image.set(imageUrl)
        if imageUrl:
            await ctx.send(f"Welcome image set to `{imageUrl}`. Be sure to test it!")
        else:
            await ctx.send("Welcome image disabled.")
        LOGGER.info(
            "Image changed by %s#%s (%s)",
            ctx.message.author.name,
            ctx.message.author.discriminator,
            ctx.message.id,
        )
        LOGGER.info("Image set to %s", imageUrl)

    # [p]welcome test
    @welcome.command(name="test")
    async def test(self, ctx: Context):
        """Test the welcome DM by sending a DM to you."""
        await self.sendWelcomeMessage(ctx.message.author, test=True)
        #await self.sendWelcomeMessageChannel(ctx.message.author, ctx.guild)
        await ctx.send("If this server has been configured, you should have received a DM.")
