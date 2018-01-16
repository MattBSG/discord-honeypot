# Discord Honeypot
A bot to complement current server administration in Discord by seeking and reporting DM spammers and advertisers.
Please keep in mind that it is very unfinished and is now under a rewrite and may not work efficiently or correctly.

Upcoming breaking changes:
* Transition to mongo
* Better communication between honeypots and main bot
* Code clean-up

## MySQL
Create table sql for case data:

    CREATE TABLE `cases` (
      `case_id` mediumint(9) NOT NULL AUTO_INCREMENT,
      `userid` bigint(24) NOT NULL,
      `date` bigint(20) NOT NULL,
      `message` longtext,
      `processed` tinyint(4) NOT NULL DEFAULT '0',
      PRIMARY KEY (`case_id`),
      UNIQUE KEY `case_id_UNIQUE` (`case_id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=271 DEFAULT CHARSET=latin1;
    
Create table sql for server data:

    CREATE TABLE `serverdata` (
      `serverid` bigint(20) NOT NULL,
      `registree` bigint(20) NOT NULL,
      `notify_channel` bigint(20) NOT NULL,
      `enabled` tinyint(1) NOT NULL DEFAULT '1',
      PRIMARY KEY (`serverid`),
      UNIQUE KEY `serverid_UNIQUE` (`serverid`),
      UNIQUE KEY `notify_channel_UNIQUE` (`notify_channel`)
    ) ENGINE=InnoDB DEFAULT CHARSET=latin1;

## Bot Setup
Honeypot runs in two sections (which currently do not run each other, so please plan accordingly with a shell script etc. to run all bot files), the main bot (Honeypot), and the slave (baiter) instances as well as a MySQL database. _Note that for this setup I use the default bot prefix `h.`, if you change it then substitutes it as used in the commannds_

In `constants.py` you can edit each of the following details:
* __bot\_token__ - The discord token for the main Honeypot bot account (See https://discordapp.com/developers/applications/me)
* __owner\_id__ - Your discord userid; used for owner only commands
* __prefix__ - The command prefix for the main bot
* __mainbot\_id__ - The client ID of your main Honeypot bot account
* __slaves__ - A `list` of the IDs of ALL slave user accounts
* __poweroff\_command__ - Determines the message sent to slaves during shutdown. This should be left unchanged
* __mysql\_config__ - The details of the host MySQL database

Making extra user accounts is fairly straightforward. Make a discord user account (duh) and have it join at least one server your Honeypot main instance is in. Make sure the user ID is added to the slaves list in `constants.py`. Next run the introduce command. i.e. `h.introduce`.

## Server Setup
I never finished implementation of registration for servers, so it must be done manually.

In the `serverdata` table, insert a row with the correct information:
* __serverid__ - The server you are registering the Honeypot with
* __registree__ - The person registering the bot (Must not be null | Unused data)
* __notify\_channel__ - The channel that infraction notifications will be sent to (must be readable by the bot)
