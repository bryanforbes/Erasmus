# Erasmus

[![Discord Bots](https://discordbots.org/api/widget/status/349394562336292876.svg?noavatar=true)](https://discordbots.org/bot/349394562336292876) [![Discord Bots](https://discordbots.org/api/widget/servers/349394562336292876.svg?noavatar=true)](https://discordbots.org/bot/349394562336292876) [![Discord Bots](https://discordbots.org/api/widget/upvotes/349394562336292876.svg?noavatar=true)](https://discordbots.org/bot/349394562336292876) [![Discord Bots](https://discordbots.org/api/widget/lib/349394562336292876.svg?noavatar=true)](https://discordbots.org/bot/349394562336292876)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

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
