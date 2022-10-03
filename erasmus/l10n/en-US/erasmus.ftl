# General error messages

generic-error = An error occurred
no-private-message = This command is not available in private messages
only-private-message = This command is only available in private messages
missing-required-argument = The required argument `{ $name }` is missing
cooldown-error = You can retry again in { PERIOD($period) }.
user-on-cooldown =
    You have used this command too many times. You can retry again in { PERIOD($period) }.
command-on-cooldown =
    This command has been used too many times in this channel. You can retry again in { PERIOD($period) }.
missing-permissions = You do not have the correct permissions to run this command
cannot-paginate =
    I need the "{ $permission ->
        [embed-links] Embed Links
        [send-messages] Send Messages
        [add-reactions] Add Reactions
       *[read-message-history] Read Message History
    }" permission

# Bible Cog

## Commands

-bible-version =
    { $number ->
       *[singular] Bible version
        [plural] Bible versions
    }

serverprefs = serverprefs
    .description = Server preferences

serverprefs__setdefault = setdefault
    .description = Set the default { -bible-version } for this server
    .PARAM--version--name = version
    .PARAM--version--description = { -bible-version }
    .response = Server version set to `{ $version }`

serverprefs__unsetdefault = unsetdefault
    .description = Unset the default version for this server
    .deleted = Server version deleted
    .already-deleted = Server version already deleted

serverprefs__daily-bread = daily-bread
    .description = Daily bread

serverprefs__daily-bread__set = set
    .description = Set or update the automated daily bread post settings for this server
    .PARAM--channel--name = channel
    .PARAM--channel--description = The channel to post the daily bread to
    .PARAM--time--name = time
    .PARAM--time--description = The time to post at
    .PARAM--timezone--name = timezone
    .PARAM--timezone--description = The time zone for the time to post
    .started =
        Automated daily bread posting has been started. I will post the daily bread in { $channel } starting at { $next_scheduled } using `{ $version }`.

        Use `/serverprefs daily-bread set` to set a new channel or time.
        Use `/serverprefs daily-bread stop` to stop automated posts.
        Use `/serverprefs setdefault` to change the version.
    .updated =
        Automated daily bread posting has been updated. I will post the daily bread in { $channel } starting at { $next_scheduled } using `{ $version }`.

        Use `/serverprefs daily-bread set` to set a new channel or time.
        Use `/serverprefs daily-bread stop` to stop automated posts.
        Use `/serverprefs setdefault` to change the version.
    .need-guild-webhooks-permission = I need the "Manage Webhooks" permission in order to post the daily bread. [Click here]({ $invite_url }) to re-authorize me with the correct permissions. Afterwards, please re-run this command.
    .need-channel-webhooks-permission = I need the "Manage Webhooks" permission enabled for me in { $actual_channel } to allow me to post the daily bread in { $channel }. After doing so, please re-run this command.
    .version-warning = The server's current default version (`{ $version }`) does not include both Old and New Testaments. I will skip posting daily bread for days where the verse or verses are in a book missing from this version. In order to get daily bread posted every day, please change the server's default version to a version that includes both the Old and New Testaments using `/serverprefs setdefault`.

serverprefs__daily-bread__stop = stop
    .description = Stop the automated daily bread posts for this server
    .stopped = Automated daily bread posting has been stopped for this server
    .not_set = Automated daily bread posting has not been set for this server
    .unable-to-remove-existing = I was unable to remove my existing webhooks. You will need to manually remove any webhooks in my integrations settings in the "Integrations" server settings under "Bots and Apps".

prefs = prefs
    .description = Preferences

prefs__setdefault = setdefault
    .description = Set your default { -bible-version }
    .PARAM--version--name = version
    .PARAM--version--description = { -bible-version }
    .response = Default version set to `{ $version }`

prefs__unsetdefault = unsetdefault
    .description = Unset your default { -bible-version }
    .deleted = Default version unset
    .already-deleted = Default version already unset

verse = verse
    .description = Look up a verse
    .PARAM--reference--name = reference
    .PARAM--reference--description = A verse reference
    .PARAM--version--name = version
    .PARAM--version--description = The version in which to look up the verse
    .PARAM--only_me--name = only_me
    .PARAM--only_me--description = Whether to display the verse to yourself or everyone

search = search
    .description = Search in the Bible
    .PARAM--terms--name = terms
    .PARAM--terms--description = Terms to search for
    .PARAM--version--name = version
    .PARAM--version--description = The { -bible-version } to search within
    .title = Search results from { $bible_name }
    .no-results = I found 0 results
    .footer = Page { $current_page }/{ $max_pages } ({ $total } entries)
    .stop-button = Stop
    .unknown-error = An unknown error occurred. Sorry!
    .embed-links-error = I do not have embed links permission in this channel
    .cannot-be-controlled-error = This pagination menu cannot be controlled by you. Sorry!
    .modal-title = Skip to page…
    .modal-input-label = Page
    .modal-input-placeholder = Page number here…
    .modal-generic-error = An error occurred
    .modal-not-a-number-error = You must enter a number

bibles = bibles
    .description = List which { -bible-version(number: "plural") } are available for lookup and search
    .prefix = I support the following { -bible-version(number: "plural") }:

bibleinfo = bibleinfo
    .description = Get information about a { -bible-version }
    .PARAM--version--name = version
    .PARAM--version--description = The { -bible-version } to get information for
    .abbreviation = Abbreviation
    .books = Books

daily-bread = daily-bread
    .description = Daily bread

daily-bread__show = show
    .description = Display today's daily bread
    .PARAM--version--name = version
    .PARAM--version--description = The version to display the daily bread in
    .PARAM--only_me--name = only_me
    .PARAM--only_me--description = Whether to display the daily bread to yourself or everyone

daily-bread__status = status
    .description = Display the status of automated daily bread posts for this server
    .not_set = Automated daily bread posts have not been set up in this server. You will need to ask an administrator to set it up.
    .title = Daily Bread Status
    .channel = Channel
    .next_scheduled = Next Scheduled

## Errors

book-not-understood = I do not understand the book "{ $book }"
book-not-in-version = { $version } does not contain { $book }
book-mapping-invalid = The mapping for `{ $book }` in `{ $version }` is invalid
do-not-understand = I do not understand that request
reference-not-understood = I do not understand the reference "{ $reference }"
bible-not-supported = `{ $version }` is not supported
bible-not-supported-context = `{ $prefix }{ $version }` is not supported
no-user-version = You must first set your default version with `/version set`
invalid-version = `{ $version }` is not a valid version. Check `/bibles` for valid versions.
service-not-supported = The service configured for `{ $name }` is not supported
service-lookup-timeout = The request timed out looking up { $verses } in { $name }
service-search-timeout = The request timed out searching for { $terms } in { $name }
invalid-time = `{ $time }` is not a valid time representation
invalid-timezone = `{ $timezone }` is not a recognized time zone
daily-bread-not-in-version = Today's daily bread is not in `{ $version }`

# Confessions Cog

## Commands

confess = confess
    .description = Confessions

confess__cite = cite
    .description = Cite a section from a confession or catechism
    .PARAM--source--name = source
    .PARAM--source--description = The confession or catechism to cite
    .PARAM--section--name = section
    .PARAM--section--description = The section to cite

confess__search = search
    .description = Search for terms in a confession or catechism
    .PARAM--source--name = source
    .PARAM--source--description = The confession or catechism to search within
    .PARAM--terms--name = terms
    .PARAM--terms--description = Terms to search for
    .title = Search results from { $confession_name }
    .no-results = I found 0 results
    .footer = Page { $current_page }/{ $max_pages } ({ $total } entries)
    .stop-button = Stop
    .unknown-error = An unknown error occurred. Sorry!
    .embed-links-error = I do not have embed links permission in this channel
    .cannot-be-controlled-error = This pagination menu cannot be controlled by you. Sorry!
    .modal-title = Skip to page…
    .modal-input-label = Page
    .modal-input-placeholder = Page number here…
    .modal-generic-error = An error occurred
    .modal-not-a-number-error = You must enter a number

## Errors

invalid-confession = `{ $confession }` is not a valid confession
no-section =
    `{ $confession }` does not have { $section_type ->
       *[CHAPTERS] a paragraph
        [SECTIONS] a section
        [QA] a question
        [ARTICLES] an article
    } `{ $section }`

# Creeds Cog

## Commands

creed = creed
    .description = Historic creeds

creed__apostles = apostles
    .description = The Apostles' Creed

creed__athanasian = athanasian
    .description = The Athanasian Creed

creed__chalcedon = chalcedon
    .description = The Chalcedonian Definition

creed__nicene = nicene
    .description = The Nicene Creed

creed__nicene325 = nicene325
    .description = The Nicene Creed (325 AD)

creed__nicene381 = nicene381
    .description = The Nicene Creed (381 AD)

# Misc Cog

## Commands

invite = invite
    .description = Get a link to invite Erasmus to your server

about = about
    .description = Get info about Erasmus
    .title = About Erasmus
    .version = Version
    .guilds = Guilds
    .channels = Channels
    .footer = Made with discord.py v{ $version }
    .invite = Invite Erasmus
    .support-server = Official Support Server

notice = notice
    .description = Display text-command deprecation notice

news = news
    .description = Display news from the latest release
    .news-for-version = News for { $version }
