import constants
import discord
import asyncio
import json
import sys
import requests
import mysql.connector
import time
from raven import Client

token = 'YourUserBotTokenHere'
bot = discord.Client()
# If you like sentry
#client = Client('FullSentry.ioUrlHere', auto_log_stacks=True)
cnx = mysql.connector.connect(**constants.mysql_config)
cursor = cnx.cursor()
invite_headers = {'authorization': token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}


@bot.event
async def on_ready():
	print('On ready completed for slave {}'.format(bot.user))

@bot.event
async def on_message(msg):
	if msg.channel.type != discord.ChannelType.private:
		return
	elif bot.user.id == msg.author.id:
		return

# if the main bot messages it, process it's meaning
	elif msg.author.id == constants.mainbot_id:
		if msg.content == constants.poweroff_command:
			await logout()
		else:
			print('Joining server')
			joinserver(msg.content)
	else:
		await db_store_userdata(msg.author.id, msg.content)

async def logout():
	await bot.logout()
	for task in asyncio.Task.all_tasks():
		task.cancel()
	cursor.close()
	cnx.close()

async def db_store_userdata(userid, message):
	# Some escaping of characters used in discord; hacky rn
	message = message.replace("'", "")
	message = message.replace("\\", "")
	message = message.replace("@", "")
	message = message.replace("`", "")
	try:
		cursor.execute("INSERT INTO honeypot.cases (userid, date, message) VALUES (%s, %s, %s)", (userid, int(time.time()), message))
		cnx.commit()
		await asyncio.sleep(2)
		await bot.send_message(discord.utils.get(bot.get_all_members(), id=constants.mainbot_id), 'check')
	except Exception as e:
		print('WARNING: EXCEPTION (slave):\n{}'.format(e))

def joinserver(invite):
	invite_post = 'https://discordapp.com/api/v6/invite/' + invite
	r = requests.post(invite_post, headers=invite_headers)
	return r.content

try:
	bot.run(token, bot=False)
except Exception as e:
	print(e)