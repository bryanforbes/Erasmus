# General error messages

generic-error = En feil oppstod
no-private-message = Denne kommandoen er ikke tilgjengelig i private meldinger
only-private-message = Denne kommandoen er kun tilgjengelig i private meldinger
missing-required-argument = Det nødvendige argumentet `{ $name }` mangler
cooldown-error = Du kan prøve igjen om { PERIOD($period) }.
user-on-cooldown = Du har brukt denne kommandoen for mange ganger. Du kan prøve igjen om { PERIOD($period) }.
command-on-cooldown = `{ $command }` har blitt brukt for mange ganger i denne kanalen. Du kan prøve igjen om { PERIOD($period) }.
missing-permissions = Du har ikke de riktige tillatelsene for å kjøre denne kommandoen
cannot-paginate =
    Jeg trenger tillatelsen "{ $permission ->
            [embed-links] Bygg inn lenker
            [send-messages] Send meldinger
            [add-reactions] Legg til reaksjoner
           *[read-message-history] Les meldingshistorikk
        }"

# Bible Cog


## Commands

-bible-version =
    { $number ->
       *[singular] Bible version
        [plural] Bible versions
    }
serverprefs = serverprefs
    .description = Server preferences commands
serverprefs__setdefault = setdefault
    .description = Set the default { -bible-version } for this server
    .PARAM--version--name = versjon
    .PARAM--version--description = { -bible-version }
    .response = Server version set to `{ $version }`
serverprefs__unsetdefault = unsetdefault
    .description = Unset the default version for this server
    .deleted = Server version deleted
    .already-deleted = Server version already deleted
prefs = prefs
    .description = Preferences commands
prefs__setdefault = setdefault
    .description = Set your default { -bible-version }
    .PARAM--version--name = version
    .PARAM--version--description = { -bible-version }
    .response = Version set to `{ $version }`
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

## Errors

book-not-understood = I do not understand the book "{ $book }"
book-not-in-version = { $version } does not contain { $book }
do-not-understand = I do not understand that request
reference-not-understood = I do not understand the reference "{ $reference }"
bible-not-supported = `{ $version }` is not supported
bible-not-supported-context = `{ $prefix }{ $version }` is not supported
no-user-version = You must first set your default version with `{ $command }`
invalid-version = `{ $version }` is not a valid version. Check `{ $command }` for valid versions
service-not-supported = The service configured for `{ $name }` is not supported
service-lookup-timeout = The request timed out looking up { $verses } in { $name }
service-search-timeout = The request timed out searching for { $terms } in { $name }

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
        [QA] a question
        [ARTICLES] an article
    } `{ $section }`
no-sections =
    `{ $confession }` has no { $section_type ->
       *[chapters] chapters
        [paragraphs] paragraphs
        [articles] articles
    }

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
    .guilds = Guilds
    .channels = Channels
    .footer = Made with discord.py v{ $version }
    .invite = Invite Erasmus
    .support-server = Official Support Server
notice = notice
    .description = Display text-command deprecation notice
