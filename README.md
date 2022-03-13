# Erasmus

[![Discord Bots](https://discordbots.org/api/widget/status/349394562336292876.svg?noavatar=true)](https://discordbots.org/bot/349394562336292876) [![Discord Bots](https://discordbots.org/api/widget/servers/349394562336292876.svg?noavatar=true)](https://discordbots.org/bot/349394562336292876) [![Discord Bots](https://discordbots.org/api/widget/upvotes/349394562336292876.svg?noavatar=true)](https://discordbots.org/bot/349394562336292876) [![Discord Bots](https://discordbots.org/api/widget/lib/349394562336292876.svg?noavatar=true)](https://discordbots.org/bot/349394562336292876)

[![Build Status](https://travis-ci.org/bryanforbes/Erasmus.svg?branch=master)](https://travis-ci.org/bryanforbes/Erasmus)
[![codecov](https://codecov.io/gh/bryanforbes/Erasmus/branch/master/graph/badge.svg)](https://codecov.io/gh/bryanforbes/Erasmus)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://github.com/bryanforbes/botus_receptus/blob/master/LICENSE)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

A Bible bot for Discord

[Invite Erasmus to your server](https://discordapp.com/oauth2/authorize?client_id=349394562336292876&scope=bot&permissions=388160)

## Commands

* `$`, `$lookup` - Look up a verse in your preferred version
* `$s`, `$search` - Search for terms in your perferred version
* `$setversion` - Set your preferred version
* `$versions` - List which Bible versions are available for lookup and search
* `$<versions>` - Look up a verse in a specific version (ex. `$esv`)
* `$s<version>` - Search for terms in a specific version (ex. `$sesv`)
* `$confess` - Query confessions and catechisms
* `$creeds` - List the supported creeds
* `$help <command>` - Get more information about a specific command

## Data Privacy Policy

Erasmus stores the following data:

* A user's internal Discord ID (a [snowflake](https://discord.com/developers/docs/reference#snowflakes)) ONLY if the user set a preferred version (this can be deleted using `$unsetversion`)
* A guild's internal Discord ID (a [snowflake](https://discord.com/developers/docs/reference#snowflakes)) ONLY if a guild administrator sets a preferred version for the guild (this can be deleted using `unsetguildversion`)

While Erasmus uses message content to determine when it should execute a command, **no message content is ever stored**.

## Setup

Ensure that [Poetry](https://poetry.eustace.io/) is installed

### Running

```
poetry install --no-dev
poetry run erasmus
```

### Development

```
poetry install
poetry run erasmus
```
