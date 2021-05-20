"""Welcome cog
Sends welcome DMs to users that join the server.
"""



from redbot.core import Config, checks, commands, data_manager
from redbot.core.bot import Red
from redbot.core.commands.context import Context
import discord




class Greet(commands.Cog):
    """Greet a person"""


    def __init__(self):
        self.config = Config.get_conf(self, identifier=834654179236)

        default_guild = {
            "greetings": []
        }
        self.config.register_member(**default_guild)


    async def getRandomMessage(self):
        return ""


    @commands.group(name="greet", invoke_without_command=True)
    async def greetCommand(self, ctx, user: discord.Member):
        """Greets a person

        Parameters:
        -----------

        """
        await ctx.trigger_typing()
        message =  await self.getRandomMessage()
        await ctx.send(message)

    @greetCommand.command(name="add")
    async def urlSource(self, ctx, greeting):
        """Adds a greeting

        Parameters:
        -----------
        greeting: a greeting that may or may not include {USER} in the message
        """
