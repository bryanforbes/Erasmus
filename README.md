# Erasmus

[![Discord Bots](https://top.gg/api/widget/servers/349394562336292876.svg)](https://top.gg/bot/349394562336292876)
[![Build Status](https://travis-ci.org/bryanforbes/Erasmus.svg?branch=master)](https://travis-ci.org/bryanforbes/Erasmus)
[![codecov](https://codecov.io/gh/bryanforbes/Erasmus/branch/master/graph/badge.svg)](https://codecov.io/gh/bryanforbes/Erasmus)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://github.com/bryanforbes/botus_receptus/blob/master/LICENSE)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Checked with pyright](https://img.shields.io/badge/pyright-checked-informational.svg)](https://github.com/microsoft/pyright/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

A Bible bot for Discord

[Invite Erasmus to your server](https://discord.com/oauth2/authorize?client_id=349394562336292876&scope=bot+applications.commands&permissions=275414871104)

## Commands

* `/verse` - Look up a verse in your preferred or selected version
* `/search` - Search for terms in your preferred or selected version
* `/bibles` - List the Bible versions supported
* `/bibleinfo` - Display information about the specified Bible version
* `/version set` - Set your preferred version
* `/version clear` - Clear your preferred version
* `/version show` - Display information about how Erasmus will display verses for you
* `/daily-bread show` - Display today's daily bread
* `/daily-bread status` - Display the status of automated daily bread posts for this server
* `/serverprefs version set` - Set the server's preferred version (Administrator only)
* `/serverprefs version clear` - Clear the server's preferred version (Administrator only)
* `/serverprefs version show` - Display the server's preferred version (Administrator only)
* `/serverprefs daily-bread set` - Schedule the automated daily bread posts (Administrator only)
* `/serverprefs daily-bread stop` - Stop the automated daily bread posts (Administrator only)
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
* `/news` - News from the latest release

## Bracket Notation

In addition to the slash-commands listed above, Erasmus will respond to all verse references surrounded in brackets (ex. `[John 1:1]`) anywhere in a message. By default, Erasmus will look up the verse using the user's default version (set with `/version set`), the servers's default version (`/serverprefs version set`), or the ESV. Users can also specify a version to use by appending the version abbreviation after the verse (ex. `[John 1:1 KJV]`).

## Data Privacy Policy

Erasmus retains the following data:

* A user's internal Discord ID (a [snowflake](https://discord.com/developers/docs/reference#snowflakes)) ONLY if the user sets a preferred version using `/version set` (this can be deleted using `/version clear`)
* A guild's internal Discord ID (a [snowflake](https://discord.com/developers/docs/reference#snowflakes)) ONLY if one of the following conditions is met:
  * A guild administrator sets a preferred version for the guild using `/serverprefs version set` (this can be deleted using `/serverprefs version clear`)
  * A guild administrator schedules the automatic daily bread posts for the guild using `/serverprefs daily-bread set` (this can be deleted using `/serverprefs daily-bread stop`)

Erasmus **never** retains message content.

## Setup

Ensure that [Poetry](https://python-poetry.org/) is [installed](https://python-poetry.org/docs/#installation)

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
