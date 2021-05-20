"""Welcome cog
Sends welcome DMs to users that join the server.
"""



from redbot.core import Config, checks, commands, data_manager
from redbot.core.bot import Red
from redbot.core.commands.context import Context
import discord
import random

def createEmbed(list, start):
    embed = discord.Embed()
    embed.colour = discord.Colour.blue()
    embed.title = "List of Greetings"
    if list:
        for i in range(start, min(start+10, len(list))):
            embed.add_field(name="", value=list[i], inline=False)
    return embed


class Greet(commands.Cog):
    """Greet a person"""


    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=834654179236)

        default_guild = {
            "greetings": []
        }
        self.config.register_member(**default_guild)


    async def getRandomMessage(self, ctx):
        greetings = await self.config.guild(ctx.guild).greetings()
        numGreetings = len(greetings)
        if(numGreetings == 0):
            return "Welcome to the server {USER}"
        else:
            return greetings[random.randint(0, numGreetings-1)]



    @commands.group(name="greet", invoke_without_command=True)
    async def greetCommand(self, ctx, user: discord.Member):
        """Greets a person

        Parameters:
        -----------

        """
        USERPING = "{USER}"

        await ctx.trigger_typing()
        rawMessage =  await self.getRandomMessage(ctx)
        splitMessage = rawMessage.split("{USER}")
        message = ""
        for x in range(len(splitMessage)):
            message+=splitMessage[x]
            if(x<len(splitMessage)):
                message+=discord.Member
        await ctx.send(message)
        return


    @checks.mod_or_permissions()
    @greetCommand.command(name="add")
    async def greetAdd(self, ctx, greeting):
        """Adds a greeting

        Parameters:
        -----------
        greeting: a greeting that may or may not include {USER} in the message
        """
        return


    @checks.mod_or_permissions()
    @greetCommand.command(name="remove")
    async def greetRemove(self, ctx, greeting):

        return

    @greetCommand.command(name="list")
    async def greetList(self, ctx):
        greetings = await self.config.guild(ctx.guild).greetings()
        embed = createEmbed(greetings, 0)
        try:
            sentMsg = await ctx.send(embed=embed)
            await sentMsg.add_reaction('⬅')
            await sentMsg.add_reaction('➡')
            await sentMsg.add_reaction('❌')
        except discord.errors.Forbidden as error:
            await ctx.send("I'm not able to do that.")
            await sentMsg.delete()

    @commands.Cog.listener("on_raw_reaction_add")
    async def checkForReaction(self, payload):
        """Reaction listener (using socket data)
        Checks to see if a spoilered message is reacted, and if so, send a DM to the
        user that reacted.
        """
        spoilerMessages = await self.config.messages()
        # make sure the reaction is proper
        msgId = payload.message_id
        if str(msgId) in spoilerMessages:
            server = discord.utils.get(self.bot.guilds, id=payload.guild_id)
            reactedUser = discord.utils.get(server.members, id=payload.user_id)
            if reactedUser.bot:
                return

            channel = discord.utils.get(server.channels, id=payload.channel_id)
            message = await channel.fetch_message(int(msgId))


            emoji = payload.emoji.name
            await message.remove_reaction(emoji, reactedUser)
            return
