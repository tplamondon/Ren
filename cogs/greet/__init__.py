"""Good Smile Info module
Parse GSC info
"""

from redbot.core.bot import Red
from .greet import Greet


def setup(bot: Red):
    """Add the cog to the bot."""
    bot.add_cog(Greet(bot))
