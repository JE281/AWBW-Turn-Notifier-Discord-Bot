import sys

import discord
from discord.ext import commands
import asyncio
import aiohttp
import async_timeout

debug = False
if len(sys.argv) > 1:
    debug = sys.argv[1] == "debug"
bot = commands.Bot(command_prefix='$', description="notify_me_about <game_id>")
global game_id_list
game_id_list = ["255899", "255900", "256517", "256552"]
game_id_list = ["720359", "711425"]
username_map = {"JE281":"JE281#3663", "Snako":"miriada16#5136", "909_919":"909_919#9429", "Xananarg":"Xananarg#8374", "Joe_Bigfoot":"Joe_Bigfoot#3140", "Unity":"fresh Dumbledore#0343"}
username_to_discord_user = {"JE281":None, "Snako":None, "909_919":None, "Xananarg":None, "Joe_Bigfoot":None, "Unity":None}
aw_channel = discord.Object(id='378694324915011596')



@bot.command()
async def notify_me_about(ctx, game_id, pm_instead : str = ""):
    pass


async def check_turn_in_game(game_id, send_pm_instead=False, pm_reminders=False):
    global game_id_list
    await bot.wait_until_ready()
    await bot.wait_until_login()
    same_turn_counter = 0
    counter = 0
    last_turn_was = ""
    while not bot.is_closed:
        username = ""
        counter += 1
        print("Poll number: " + str(counter) + " for game id: " + str(game_id))
        async with aiohttp.ClientSession() as session:
            html = await get_html(session, game_id)
            for line in html.splitlines():
                if 'href="profile.php?username=' in line and '</b>' in line:
                    start_b = line.find('<b>')
                    end_b = line.find('</b>')
                    username = line[start_b+3:end_b]
            if '<span class="small_text">Game&nbsp;Ended:&nbsp;' in html:
                print("Game " + game_id + " ended!")
                if send_pm_instead:
                    await send_message(username_to_discord_user[username], "Game " + game_id + " ended!")
                    if last_turn_was != "":
                        await send_message(username_to_discord_user[last_turn_was], "Game " + game_id + " ended!")
                else:
                    await send_message(aw_channel, "Game " + game_id + " ended!")
                try:
                    game_id_list.remove(game_id)
                except ValueError:
                    pass
                break #terminates the task
        print(username + "'s turn! Last turn was: " + last_turn_was)
        if username != "" and username != last_turn_was:
            same_turn_counter = 0
            last_turn_was = username
            if username in username_to_discord_user.keys():
                print("Sending message")
                if send_pm_instead:
                        await send_message(username_to_discord_user[username], "It's your turn!")
                else:
                    mention = '<@' + str(username_to_discord_user[username].id) + '>'
                    await send_message(aw_channel, "%s's turn!" % mention)
                    print(username_to_discord_user[username].id)
        elif username != "" and username == last_turn_was and username in username_to_discord_user.keys():
            same_turn_counter += 1
            if pm_reminders and same_turn_counter % 90 == 0: #Remind by PM every 6 hours
                print("It's been " + username + "'s turn for " + str(int(same_turn_counter / 15)) + " hours!")
                await send_message(username_to_discord_user[username], "It's been your turn for " + str(int(same_turn_counter/15)) + " hours!")
                if username != "Phelerox": #For debug purposes, tell dev when reminder is issued
                    await send_message(username_to_discord_user["Phelerox"], "It's been " + username + "'s turn for " + str(int(same_turn_counter / 15)) + " hours!")

        await asyncio.sleep(240) # task runs every fourth minute
    print("Shutting down task to monitor game " + game_id)

async def get_html(session, game_id):
    try:
        with async_timeout.timeout(80):
            async with session.get('http://awbw.amarriner.com/game.php?games_id=' + str(game_id)) as response:
                return await response.text()
    except TimeoutError as te:
        await send_message(username_to_discord_user["JE281"], "TimeoutError! " + str(te))
        return await get_html(session, game_id)
    except Exception as e:
        await send_message(username_to_discord_user["JE281"], "Unknown exception when fetching html! " + str(e.__class__.__name__))
        return await get_html(session, game_id)

async def send_message(destination, message):
    try:
        if not debug:
            await bot.send_message(destination, message)
        else:
            await bot.send_message(username_to_discord_user["JE281"], message)
    except Exception as e:
        print("Unknown exception when sending message: " + str(e.__class__.__name__))
        await send_message(destination, message)


@bot.event
async def on_ready():
    for server in bot.servers:
        for discord_user in server.members:
            for username, discord_username in username_map.items():
                if discord_username == str(discord_user):
                    username_to_discord_user[username] = discord_user
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


def start_bot():
    bot.loop.create_task(check_turn_in_game(game_id_list[0], send_pm_instead=True))
    bot.loop.create_task(check_turn_in_game(game_id_list[1], send_pm_instead=True))
    bot.loop.create_task(check_turn_in_game(game_id_list[2], send_pm_instead=True))
    bot.loop.create_task(check_turn_in_game(game_id_list[3], pm_reminders=True))

    token = ''  # The token should be on the first line in a file named 'token'.
    with open('token', 'r') as token_file:  # TODO: rewrite this so that starting the bot works from any directory
        token = token_file.readline()
    bot.run(token)

try:
    start_bot()
except Exception as e:
    with open('fatal_crash_caught', 'a+') as crash_file:
        crash_file.write("Crashed with Exception: " + str(repr(e)) + "\n")
