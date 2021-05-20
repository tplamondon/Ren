"""Welcome cog
Sends welcome DMs to users that join the server.
"""



from redbot.core import Config, checks, commands, data_manager
from redbot.core.bot import Red
from redbot.core.commands.context import Context
import discord
import random




class Greet(commands.Cog):
    """Greet a person"""


    def __init__(self):
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

    @checks.mod
    @greetCommand.command(name="add")
    async def greetAdd(self, ctx, greeting):
        """Adds a greeting

        Parameters:
        -----------
        greeting: a greeting that may or may not include {USER} in the message
        """
