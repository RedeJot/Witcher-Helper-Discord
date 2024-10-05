import settings
import discord
import json
import os
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Button, View
from typing import Optional
import requests
import random
import asyncio
from datetime import datetime

logger = settings.logging.getLogger("bot")


def run():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.messages = True
    intents.guilds = True
    intents.members = True
    CAT_API_KEY = settings.CAT_API_SECRET
    GENERAL_CHANNEL_ID = 1286785359652454444
    ROLES_CHANNEL_ID = 1287435867883049030
    ANNOUNCEMENTS_CHANNEL_ID = 1286785359652454442
    frequency_meow_range = (10, 30)
    interval_meow_range = (30, 1800)
    admin_role_id = 1286785967692316744
    roles_buttons_filename = "roles_buttons.json"

    bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'), intents=intents)


    def save_buttons_to_file(data, base_filename):
        filename = base_filename
        with open(filename, mode='w') as file:
            json.dump(data, file, indent=4)
            logger.info(f"Saved buttons to {filename}")

    def load_data_from_file(filename):
        if not os.path.exists(filename):
            logger.info(f"File {filename} doesn't exist. Returning empty data.")
            return []
        with open(filename, mode="r") as file:
            logger.info(f"Loading data from {filename}")
            return json.load(file)
        
    def search_for_id_and_assign(filename, message_id):
        data = load_data_from_file(filename)

        for item in data:
            if item['id'] == message_id:
                logger.info(f"Loaded roles: {item["roles_and_labels"]}")
                return item['roles_and_labels']
        
        
    def add_roles_and_labels(filename, new_id, new_roles_and_labels):
        data = []
        if not os.path.exists(filename):
            new_data = {
                "id": new_id,
                "roles_and_labels": new_roles_and_labels
            }
            data.append(new_data)
            save_buttons_to_file(data, filename)
        else:
            data = load_data_from_file(filename)

            for item in data:
                if item['id'] == new_id:
                    logger.info(f"{new_id} already exists.")
                    return
                
            new_entry = {
                "id": new_id,
                "roles_and_labels": new_roles_and_labels
            }
            data.append(new_entry)

            logger.info(f"Added new entry with ID: {new_id}")
            save_buttons_to_file(data, filename)

    def delete_roles_and_labels(filename, delete_id):
        data = load_data_from_file(filename)

        for item in data:
            if item['id'] == delete_id:
                delete_index = data.index(item)
                del data[delete_index]

        save_buttons_to_file(data, filename)

    def on_delete_event(message_id):
        logger.info("Deleted roles!")
        delete_roles_and_labels(roles_buttons_filename, message_id)

    def ordinal(n):
        if 10 <= n % 100 <= 13:
            suffix = "th"
        else:
            suffix = {1: 'st', 2: 'nd', 3:'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"


    class RoleAssignView(discord.ui.View):
        def __init__(self, roles_and_labels):
            super().__init__(timeout=None)
            index = 0
            self.roles_and_labels = roles_and_labels

            for i in range(0, len(roles_and_labels), 2):
                label = roles_and_labels[i]
                role = roles_and_labels[i+1]
                index += 1
                logger.info(f"For button {index} given {role}")
                button = Button(label=label, style=discord.ButtonStyle.secondary, custom_id=f"role_button{index}")
                button.callback = self.create_button_callback(role)
                self.add_item(button)
                logger.info(f"Added to button {index}: Label: {label}, role: {role}")
            

        def create_button_callback(self, role):
            async def button_callback(interaction: discord.Interaction):
                user = interaction.user
                guild_role = discord.utils.get(interaction.guild.roles, name=role)
                logger.info(f"User {user} clicked the button for role: {role}")

                if guild_role:
                    if guild_role in user.roles:
                        await user.remove_roles(guild_role)
                        await interaction.response.send_message("Role Removed!", ephemeral=True)
                    else:
                        await user.add_roles(guild_role)
                        await interaction.response.send_message("Role given!", ephemeral=True)
                else:
                    await interaction.response.send_message("Role doesn't exist!", ephemeral=True)
            return button_callback
        

    class CatState(discord.ui.View):
        def __init__(self):
            self.cat_hungry = random.randint(1, 5)
            self.angry_state = False
            self.meow_interval = random.randint(*interval_meow_range)
            

        async def send_meow_message(self):
            random_days = random.sample(range(1, 7), 2)
            current_day = datetime.now().weekday() + 1
            treat_gif = "https://cdn.discordapp.com/attachments/883133741407555674/1289734618437910569/cat-tuxedo-cat.gif?ex=66fa8f37&is=66f93db7&hm=412f04cb7cedfe8a84ccf1e80fb0b2a39d49dbbcda74f67a62eb58ac8bb8fe2b&"
            logger.info(f"Current day of the week: {ordinal(current_day)}")
            
            with open('cat_gifs.txt', 'r') as file:
                gifs = file.readlines()
            gifs = [gif.strip() for gif in gifs if gif.strip()]
            with open('happy_cat_gifs.txt', 'r') as file:
                happy_gifs = file.readlines()
            happy_gifs = [happy_gif.strip() for happy_gif in happy_gifs if happy_gif.strip()]
            with open('angry_cat_gifs.txt', 'r') as file:
                angry_gifs = file.readlines()
            angry_gifs = [angry_gif.strip() for angry_gif in angry_gifs if angry_gif.strip()]


            if current_day in random_days:
                channel = bot.get_channel(GENERAL_CHANNEL_ID)
                meow_frequency = random.randint(*frequency_meow_range)
                
                logger.info(f"Cat will meow today: {meow_frequency} times.")
                await bot.change_presence(activity=discord.Game(name="Cat will meow today a lot!"))
                logger.info(f"Next meow in: {self.meow_interval}s")
                await asyncio.sleep(self.meow_interval)

                if channel:
                    disable_button_interval = 13
                    angry_interval = 2
                    for _ in range(meow_frequency):
                        self.meow_interval = random.randint(*interval_meow_range)
                        logger.info(f"Next meow in: {self.meow_interval}s")

                        if self.cat_hungry == 5:
                            self.angry_state = True
                            chosen_gif = random.choice(gifs)

                            button = Button(label="Give treat!", style=discord.ButtonStyle.primary, custom_id="treat_button")

                            async def button_callback(self, interaction: discord.Interaction):
                                chosen_happy_gif = random.choice(happy_gifs)
                                self.cat_hungry = 1
                                self.meow_interval = random.randint(*interval_meow_range)
                                if self.angry_state:
                                    self.angry_state = False
                                    await interaction.response.send_message(f"Meow :3 *He is happy now* \nTreat given by: {interaction.user.mention} \n{chosen_happy_gif}")
                                    await last_message.delete()
                                else:
                                    await interaction.response.send_message("Something went wrong!", ephemeral=True)
                                
                            button.callback = button_callback
                            view = View()
                            view.add_item(button)

                            last_message = await channel.send(f"Meow! *I think he wants a treat. Give him a treat!* \n{treat_gif}", view=view)
                            await asyncio.sleep(disable_button_interval)
                            button.disabled
                            last_message.edit(content=last_message.content, view=view)
                            await asyncio.sleep(angry_interval)
                        else:
                            chosen_gif = random.choice(gifs)

                            await channel.send(f"Meow! \n{chosen_gif}")
                            self.cat_hungry = random.randint(1, 10)
                            await asyncio.sleep(self.meow_interval)
                        if self.angry_state:
                            chosen_angry_gif = random.choice(angry_gifs)
                            self.cat_hungry = random.randint(3,5)

                            view.remove_item(button)
                            await last_message.delete()
                            await channel.send(f"# MEOW! \n*I think he angy because no treat >:(* \n{chosen_angry_gif}", view=view)
                            await asyncio.sleep(self.meow_interval)
                        else:
                            logger.info(f"Next meow in: {self.meow_interval}s")
                            await asyncio.sleep(self.meow_interval)
            else:
                logger.info(f"Cat will be sleeping today.")
                await bot.change_presence(activity=discord.Game(name="Cat is sleeping.\nGeneral will be quiet for some time."))
    cat_state = CatState()



    class Rules(discord.ui.View):
        def __init__(self, button_label: str):
            super().__init__(timeout=None)
            self.button_label = button_label
            button = discord.ui.Button(label=self.button_label, style=discord.ButtonStyle.success, custom_id="rules_button")
            button.callback = self.button_callback
            self.add_item(button)
             
        async def button_callback(self, interaction: discord.Interaction):
            user = interaction.user
            role = discord.utils.get(interaction.guild.roles, name="Rules Accepted")
            
            if role:
                if role in user.roles:
                    await interaction.response.send_message("You have already accepted rules!", ephemeral=True)
                    logger.info(f"User {user} tried to accept rules but already has accepted rules!.")
                else:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message("Rules Accepted! Have a nice stay!", ephemeral=True)
                    logger.info(f"User {user} accepted the rules.")
            else:
                await interaction.response.send_message("Role doesn't exist!", ephemeral=True)
                logger.info(f"Error giving role: Role doesn't exist!")

            
    


    @tasks.loop(hours=24)
    async def send_meow_message():
        await cat_state.send_meow_message()
 
    @tasks.loop(hours=168)
    async def random_days_refresh():
        global random_days
        random_days = random.sample(range(1, 7), 2)
        logger.info(f"Days refreshed {random_days}")

    ## Bot Status
    @bot.event
    async def on_ready():
        logger.info(f"User: {bot.user} (ID: {bot.user.id})")
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} commands successfully.")
        except Exception as e:
            logger.info(f"Error syncing commands: {e}")
    

        send_meow_message.start()
        random_days_refresh.start()
        bot.add_view(Rules("Persistent Button"))
        channel = bot.get_channel(ROLES_CHANNEL_ID)

        if os.path.exists(roles_buttons_filename):
            async for message in channel.history(limit=None):

                view = RoleAssignView(search_for_id_and_assign(roles_buttons_filename, message.id))

                await message.edit(content=message.content, view=view)
                await asyncio.sleep(5)


    @bot.event
    async def on_message(message: discord.Message):
        with open('cat_gifs.txt', 'r') as file:
            gifs = file.readlines()
        gifs = [gif.strip() for gif in gifs if gif.strip()]
        if bot.user.mentioned_in(message):
            chosen_gif = random.choice(gifs)
            await message.channel.send(f"Meow! \n*You just summoned the cat* \n{chosen_gif}")
        await bot.process_commands(message)

    @bot.event
    async def on_raw_message_delete(payload):
        message_id = payload.message_id
        channel_id = payload.channel_id
        channel = bot.get_channel(channel_id)

        data = load_data_from_file(roles_buttons_filename)
        if channel is not None:
            for item in data:
                if item['id'] == message_id:
                    on_delete_event(message_id)

        
    
        



    ## Bot Commands
    @bot.command(name="rules", help="This command is only for admins!")
    @commands.has_role(admin_role_id)
    ## Rules Command prefix: !rules <none>/"<labeltext>" "<messagecontent>"
    async def rules(ctx, channelID: int, buttonLabel: str, userMessage: str):
        channel = bot.get_channel(channelID)
        if channel:
            if len(userMessage) < 2000:
                if buttonLabel != "none":
                    view = Rules(buttonLabel)
                    await channel.send(userMessage, view=view)
                    logger.info(f"ChannelID: {channelID}\nButton Label: {buttonLabel} \nMessage Content: {userMessage}")
                    await ctx.message.delete()
                    await ctx.send("Done!")
                else:
                    await channel.send(userMessage)
                    logger.info(f"ChannelID: {channelID}\nButton Label: none \nMessage Content: {userMessage}")
                    await ctx.message.delete()
                    await ctx.send("Done!")
            else:
                logger.info(f"Can't send message is higher than 2000 character limit!\nMessage Content: {userMessage}")
                await ctx.send("Your message is higher than 2000 character limit!")
        else:
            await ctx.send("Couldn't find channel with this ID!")
    @rules.error
    async def rules_error(ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send("You don't have the requiered role to use this command!")


    @bot.command(name="roleassign", help="This command is only for admins!")
    @commands.has_role(admin_role_id)
    async def roleassign(ctx, message: str, *roles_and_labels):
        
        roles_and_labels_parsed = []
        logger.info(f"Given data: {roles_and_labels}")

        for i in range(0, len(roles_and_labels), 2):
            label = roles_and_labels[i]
            role_name = roles_and_labels[i+1]
            
            if not role_name:
                error_message_2 = await ctx.send(f"Role {role_name} not found.")
                await asyncio.sleep(5)
                await error_message_2.delete()
                return
            
            roles_and_labels_parsed.append(label)
            roles_and_labels_parsed.append(role_name)
            logger.info(f"User given data: {roles_and_labels_parsed}")

        view = RoleAssignView(roles_and_labels_parsed)
        

        message_id = await ctx.send(message, view=view)
        
        add_roles_and_labels(roles_buttons_filename, message_id.id, roles_and_labels_parsed)
        await ctx.message.delete()
        



            
    @bot.command()
    async def chat(ctx, userMessage: str, channelID: Optional[int] = None):
        channel = bot.get_channel(channelID) if channelID else ctx.channel
        if len(userMessage) < 2000:
            await channel.send(userMessage)
            await ctx.message.delete()
        else:
            await ctx.send("Your message is higher than 2000 character limit!")


    ## Random cat image command
    @bot.tree.command(name="showmecat", description="Sends random cat image!")
    async def showmecat(interaction: discord.Interaction):
        headers = {
            "x-api-key": CAT_API_KEY
        }
        respone = requests.get("https://api.thecatapi.com/v1/images/search", headers=headers)

        if respone.status_code == 200:
            with open('random_cat_word.txt', 'r') as file:
                titles = file.readlines()
            titles = [title.strip() for title in titles if title.strip()]
            random_title = random.choice(titles)

            data = respone.json()
            cat_image_url = data[0]["url"]

            embed = discord.Embed(title=random_title)
            embed.set_image(url=cat_image_url)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Sorry something went wrong! :(")





        


    bot.run(settings.DISCORD_API_SECRET, root_logger=True)

if __name__ == "__main__":
    run()