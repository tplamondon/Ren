import os
import discord
from __main__ import send_cmd_help #For help
from .utils import checks # For permissions
from .utils.paginator import Pages # For making pages, requires the util!
import copy
import re
from discord.ext import commands
from .utils.dataIO import dataIO


class SmartReact:

    """Create automatic reactions when trigger words are typed in chat"""

    def __init__(self, bot):
        self.bot = bot
        self.settings_path = "data/smartreact/settings.json"
        self.settings = dataIO.load_json(self.settings_path)

    @commands.group(name="react", pass_context=True, no_pm=True)
    # @checks.mod_or_permissions(manage_messages=True)
    async def reacts(self, ctx):
        """Smart Reacts, modified."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @reacts.command(name="add", no_pm=True, pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def add(self, ctx, word, emoji):
        """Add an auto reaction to a word"""
        server = ctx.message.server
        message = ctx.message
        self.load_settings(server.id)
        emoji = self.fix_custom_emoji(emoji)
        await self.create_smart_reaction(server, word, emoji, message)

    @reacts.command(name="del", no_pm=True, pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def delete(self, ctx, word, emoji):
        """Delete an auto reaction to a word"""
        server = ctx.message.server
        message = ctx.message
        self.load_settings(server.id)
        emoji = self.fix_custom_emoji(emoji)
        await self.remove_smart_reaction(server, word, emoji, message)

    @reacts.command(name="reload", no_pm=True, pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def reload(self, ctx):
        """Reloads auto reactions with new emojis by name"""
        server = ctx.message.server
        try:
            code = await self.update_emojis(server)
        except Exception:
            await self.bot.say("Error reloading emojis.")
        await self.bot.say("Reload success.")

    @reacts.command(name="list", no_pm=True, pass_context=True)
    # @checks.mod_or_permissions(manage_messages=True)
    async def list(self, ctx):
        """List the auto reaction emojis and triggers"""
        guild_id = ctx.message.server.id
        guild_name = ctx.message.server.name
        user = ctx.message.author

        display = []
        for emoji, trigger in self.settings[guild_id].items():
            text = emoji+": "
            for n in range(0, len(trigger)):
                text += trigger[n]+" "
            display.append(text)

        p = Pages(self.bot,message=ctx.message,entries=display)
        p.embed.title = "Smart React emojis for: **{}**".format(guild_name)
        p.embed.colour = discord.Colour.red()
        await p.paginate()

    def load_settings(self, server_id):
        self.settings = dataIO.load_json(self.settings_path)
        if server_id not in self.settings.keys():
            self.add_default_settings(server_id)

    def add_default_settings(self, server_id):
        self.settings[server_id] = {}
        dataIO.save_json(self.settings_path, self.settings)

    def fix_custom_emoji(self, emoji):
        try:
            if emoji[:2] != "<:":
                return emoji
            return [r for server in self.bot.servers for r in server.emojis if r.id == emoji.split(':')[2][:-1]][0]
        except IndexError:
            return None

    # From Twentysix26's trigger.py cog
    def is_command(self, msg):
        if callable(self.bot.command_prefix):
            prefixes = self.bot.command_prefix(self.bot, msg)
        else:
            prefixes = self.bot.command_prefix
        for p in prefixes:
            if msg.content.startswith(p):
                return True
        return False

    async def update_emojis(self, server):
        try:
            settings = copy.deepcopy(self.settings[server.id])
            for emoji in self.settings[server.id].keys():
                names_list = [x.name for x in server.emojis]

                if not ':' in emoji:
                    continue
                # Looks for the location of the emoji name in server's list
                loc = names_list.index(emoji.split(':')[1])
                if emoji != str(server.emojis[loc]):
                    # Update any emojis in the trigger words
                    for idx, w in enumerate(self.settings[server.id][emoji]):
                        try:
                            if ':' in w: # Hackishly makes sure it's a custom emoji
                                locv = names_list.index(w.split(':')[1])
                                if w != str(server.emojis[locv]):
                                    settings[emoji][idx] = str(server.emojis[locv])
                        except Exception as e:
                            print("SmartReact Reload Trigger Words Error:")
                            print(e)
                            print(w)
                            raise

                    # Update to the new emoji string
                    settings[str(server.emojis[loc])] = self.settings[server.id][emoji]
                    del settings[emoji]
            self.settings[server.id] = settings

            dataIO.save_json(self.settings_path, self.settings)

        except ValueError as e:
            print("SmartReact Reload Error:")
            print(e)
            print(emoji)
            raise
        except Exception as e:
            print("SmartReact Reload Error:")
            print(e)
            print(emoji)
            raise

    async def create_smart_reaction(self, server, word, emoji, message):
        try:
            # Use the reaction to see if it's valid
            await self.bot.add_reaction(message, emoji)
            if str(emoji) in self.settings[server.id]:
                if word.lower() in self.settings[server.id][str(emoji)]:
                    await self.bot.say("This smart reaction already exists.")
                    return
                self.settings[server.id][str(emoji)].append(word.lower())
            else:
                self.settings[server.id][str(emoji)] = [word.lower()]

            await self.bot.say("Successfully added this reaction.")
            dataIO.save_json(self.settings_path, self.settings)

        except (discord.errors.HTTPException, discord.errors.InvalidArgument):
            await self.bot.say("That's not an emoji I recognize.")

    async def remove_smart_reaction(self, server, word, emoji, message):
        try:
            # Use the reaction to see if it's valid
            await self.bot.add_reaction(message, emoji)
            if str(emoji) in self.settings[server.id]:
                if word.lower() in self.settings[server.id][str(emoji)]:
                    self.settings[server.id][str(emoji)].remove(word.lower())
                    if len(self.settings[server.id][str(emoji)]) == 0:
                        self.settings[server.id].pop(str(emoji))
                    await self.bot.say("Removed this smart reaction.")
                else:
                    await self.bot.say("That emoji is not used as a reaction "
                                       "for that word.")
            else:
                await self.bot.say("There are no smart reactions which use "
                                   "this emoji.")

            dataIO.save_json(self.settings_path, self.settings)

        except (discord.errors.HTTPException, discord.errors.InvalidArgument):
            await self.bot.say("That's not an emoji I recognize.")

    # Special thanks to irdumb#1229 on discord for helping me make this method
    # "more Pythonic"
    async def msg_listener(self, message):
        if message.author == self.bot.user:
            return
        if self.is_command(message):
            return
        server = message.server
        if server is None:
            return
        if server.id not in self.settings:
            return
        react_dict = copy.deepcopy(self.settings[server.id])
        words = re.split('((?=\W+)(?=[^:\\<>]).)|', message.content.lower())
        for emoji in react_dict:
            if set(w.lower() for w in react_dict[emoji]).intersection(words):
                fixed_emoji = self.fix_custom_emoji(emoji)
                if fixed_emoji is not None:
                    try:
                        await self.bot.add_reaction(message, fixed_emoji)
                    except discord.errors.Forbidden as e:
                        print("SmartReact Error:")
                        print(e)


def check_folders():
    folder = "data/smartreact"
    if not os.path.exists(folder):
        print("Creating {} folder...".format(folder))
        os.makedirs(folder)


def check_files():
    default = {}
    if not dataIO.is_valid_json("data/smartreact/settings.json"):
        print("Creating default smartreact settings.json...")
        dataIO.save_json("data/smartreact/settings.json", default)


def setup(bot):
    check_folders()
    check_files()
    n = SmartReact(bot)
    bot.add_cog(n)
    bot.add_listener(n.msg_listener, "on_message")
