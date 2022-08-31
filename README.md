# Erasmus

[![Discord Bots](https://top.gg/api/widget/servers/349394562336292876.svg)](https://top.gg/bot/349394562336292876)
[![Build Status](https://travis-ci.org/bryanforbes/Erasmus.svg?branch=master)](https://travis-ci.org/bryanforbes/Erasmus)
[![codecov](https://codecov.io/gh/bryanforbes/Erasmus/branch/master/graph/badge.svg)](https://codecov.io/gh/bryanforbes/Erasmus)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://github.com/bryanforbes/botus_receptus/blob/master/LICENSE)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

A Bible bot for Discord

[Invite Erasmus to your server](https://discordapp.com/oauth2/authorize?client_id=349394562336292876&scope=bot&permissions=388160)

## Application Commands

* `/verse` - Look up a verse in your preferred or selected version
* `/search` - Search for terms in your preferred or selected version
* `/bibles` - List the Bible versions supported
* `/bibleinfo` - Display information about the specified Bible version
* `/prefs setdefault` - Set your preferred version
* `/prefs unsetdefault` - Unset your preferred version
* `/serverprefs setdefault` - Set the server's preferred version (Administrator only)
* `/serverprefs unsetdefault` - Unset the server's preferred version (Administrator only)
* `/creed apostles` - Display The Apostles' Creed
* `/creed athanasian` - Display The Athanasian Creed
* `/creed chalcedon` - Display The Chalcedonian Definition
* `/creed nicene` - Display The Nicene Creed
* `/creed nicene325` - Display The Nicene Creed (325 AD)
* `/creed nicene381` - Display The Nicene Creed (381 AD)
* `/confess cite` - Cite the specified section from the selected confession or catechism
* `/confess search` - Search for terms in the selected confession or catechism
* `/invite` - Get a link to invite Erasmus to your server
* `/about` - Information about Erasmus

## Text-based Commands

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

* A user's internal Discord ID (a [snowflake](https://discord.com/developers/docs/reference#snowflakes)) ONLY if the user set a preferred version (this can be deleted using `/prefs unsetdefault`)
* A guild's internal Discord ID (a [snowflake](https://discord.com/developers/docs/reference#snowflakes)) ONLY if a guild administrator sets a preferred version for the guild (this can be deleted using `/serverprefs unsetdefault`)

While Erasmus uses message content to determine when it should execute a command, **no message content is ever stored**.

## Setup

Ensure that [Poetry](https://https://python-poetry.org//) is [installed](https://python-poetry.org/docs/#installation)

### Running

```
poetry install --only main
poetry run erasmus
```

### Development

```
poetry install
poetry run erasmus
```
