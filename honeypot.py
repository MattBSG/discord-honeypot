import discord
import asyncio
import os
import aiofiles
import constants
import subprocess
import ast
import sys
import time
import random
from datetime import datetime
import mysql.connector
from raven import Client

bot = discord.Client()
# If you like sentry
#client = Client('FullSentry.ioUrlHere', auto_log_stacks=True)
cnx = mysql.connector.connect(**constants.mysql_config)
cursoru = cnx.cursor(buffered=True)
cursorw = cnx.cursor()
cursors = cnx.cursor(buffered=True)
registrations = {}

class main():

	@bot.event
	async def on_ready():
		print("----------------------------------------------")
		print("On ready completed!")
		print("Logged in as {} ({})".format(bot.user, bot.user.id))

	@bot.event
	async def on_message(msg):
		message_content = msg.content.strip()
		if msg.author.bot == True:
			return

		if msg.author.id in constants.slaves:
			if msg.content == 'check':
				await main.db_query_updates()

		if message_content.startswith(constants.prefix):
			command, *args = message_content.split()
			command = command[len(constants.prefix):].lower().strip()

			if command == 'logout' and msg.author.id in constants.owner_id:
				print('Logout initiated by {}({})'.format(msg.author, msg.author.id))
				await bot.send_message(msg.channel, 'Shutting down slaves and main process')
				for slave in constants.slaves:
					await bot.send_message(discord.utils.get(bot.get_all_members(), id=slave), constants.poweroff_command)
				try:
					await bot.send_message(msg.channel, 'Done.')
					await bot.logout()
					for task in asyncio.Task.all_tasks():
						task.cancel()
					cnx.close()
				except CancelledError:
					pass

			if command == 'ping':
				await bot.send_message(msg.channel, '<@{}> Pong!'.format(msg.author.id))

			if command == 'inf':
				if not args:
					await bot.send_message(msg.channel, '<@{}> I expected 1 argument, got none. This needs to be a case id or userid.'.format(msg.author.id))
					return
				if msg.author.id == msg.author.id:
					try:
						a = ""
						for arg in args:
							a = a + arg
						args = int(a)
						if not isinstance(args, int):
							raise TypeError
					except TypeError:
						await bot.send_message(msg.channel, '<@{}> I expected a integer, got `{}`.'.format(msg.author.id, args))
						return

					if len(str(args)) <= 16:
						cursoru.execute("SELECT * FROM honeypot.cases WHERE case_id=%s" % args)
						if cursoru.rowcount <= 0:
							await bot.send_message(msg.channel, '<@{}> No results for `{}` found.'.format(msg.author.id, args))
							return
						r = cursoru.fetchone()
						embed = discord.Embed(title='Information for Case #{}'.format(r[0]), color=0xff5555, description='<@{}> ({}) sent the message for the case you requested.'.format(r[1], r[1]), timestamp=datetime.fromtimestamp(r[2]))
						embed.add_field(name='Message contents:', value='```{}```'.format(r[3]), inline=True)
						embed.set_thumbnail(url=bot.user.avatar_url)
						await bot.send_message(msg.channel, embed=embed)
					else:
						cursoru.execute("SELECT * FROM honeypot.cases WHERE userid=%s" % args)
						cursors.execute("SELECT * FROM honeypot.cases WHERE userid=%s" % args)
						if cursoru.rowcount <= 0:
							await bot.send_message(msg.channel, '<@{}> No results for `{}` found.'.format(msg.author.id, args))
							return
						r = cursoru.fetchone()
						s = cursors.fetchone()
						case_list = []
						while s is not None:
							if not len(case_list) >= 15:
								case_list.append(s[0])
							s = cursoru.fetchone()
						cases = ""
						for number in case_list:
							cases = "{}\n{}".format(cases, number)

						embed = discord.Embed(title='Information for User ID {}'.format(r[1]), color=0xff5555, description='<@{}> ({}) has been involved in {} incidents.'.format(r[1], r[1], cursoru.rowcount))
						embed.add_field(name='Case Numbers:', value='```{}```'.format(cases))
						if cursoru.rowcount > 15:
							embed.add_field(name='Note', value='Only 15 entries are shown. If you need to view all cases for this user, you can use the api\n__<http://api.bennystudios.com/user_lookup?userid={}>__'.format(args))
						embed.set_thumbnail(url=bot.user.avatar_url)
						await bot.send_message(msg.channel, embed=embed)

			if command == 'setup' and msg.author.id in constants.owner_id:
				cursoru.execute("SELECT * FROM honeypot.serverdata WHERE serverid={}".format(msg.server.id))
				if cursoru.rowcount <= 0:
					await bot.send_message(msg.channel, 'Oops <@{}>! It appears this server is already setup and ready to roll.\n\nDo you have an issue and need help instead? You can join my support discord here:\n<https://discord.gg/6WuHnRa>'.format(msg.author.id))
				else:
					registrations[msg.author.id] = 1
					register(msg.author.id)


			if command == 'introduce' and msg.author.id in constants.owner_id:
				for server in bot.servers:
					for slave in constants.slaves:
						invite = await main.create_invite(server)
						try:
							await bot.send_message(discord.utils.get(bot.get_all_members(), id=slave), invite.id)
						except Exception as e:
							print(e)
				await bot.send_message(msg.channel, 'Done.')

	@bot.event
	async def on_server_join(server):
		invite = await main.create_invite(server)
		for slave in constants.slaves:
			await bot.send_message(discord.utils.get(bot.get_all_members(), id=slave), invite.id)
		print('- Added to a server! -\n{}\n'.format(server))
		cursoru.execute("SELECT * FROM honeypot.serverdata WHERE serverid={}".format(server.id))
		if cursoru.rowcount <= 0:
			embed = discord.Embed(title='Discord Honeypot', color=0xf6bf55,description='Hi! I\'m Honeypot, and I was added to make your lives easier.\nPlease begin setup contacting MattBSG#1043.', timestamp=datetime.now())
			embed.set_thumbnail(url=bot.user.avatar_url)
			await bot.send_message(server.default_channel, embed=embed)


	async def db_query_updates():
		cursoru.execute("SELECT * FROM honeypot.cases WHERE processed=0")
		query = list(cursoru)
		for entry in query:
			for server in bot.servers:
				if discord.utils.get(server.members, id=str(entry[1])):
					embed = discord.Embed(title='DM received', color=0xff5555, description='<@{}> ({}) has sent a DM to a honey pot account.'.format(entry[1], entry[1]), timestamp=datetime.utcfromtimestamp(entry[2]))
					embed.add_field(name='Message contents:', value='```{}```'.format(entry[3]), inline=True)
					embed.set_thumbnail(url=bot.user.avatar_url)
					embed.set_footer(text='Case {}'.format(entry[0]))
					cursors.execute("SELECT * FROM honeypot.serverdata WHERE serverid=%s" % server.id)
					for r in cursors:
						if r[3] == 1:
							try:
								channel = discord.utils.get(bot.get_all_channels(), id=str(r[2]))
								await bot.send_message(channel, embed=embed)
							except Exception as e:
								print('ERROR IN CURSOR NOTIFY:\n{}'.format(e))
						else:
							print('Tried sending msg to disabled server.')
			cursorw.execute("UPDATE honeypot.cases SET processed=1 WHERE case_id=%s" % entry[0])
			cnx.commit()

	async def register(user, server):
		raise NotImplementedError

	async def create_invite(server):
		return await bot.create_invite(server, max_age=60, max_uses=0, unique=True)

bot.run(constants.bot_token)
