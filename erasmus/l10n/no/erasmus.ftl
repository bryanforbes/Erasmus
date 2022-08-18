# General error messages

generic-error = Noe gikk galt
no-private-message = Denne handlingen er ikke tilgjengelig i private meldinger
only-private-message = Denne handlingen er bare tilgjengelig i private meldinger
missing-required-argument = Du mangler  `{ $name }`
cooldown-error = Du kan prøve igjen om { PERIOD($period) }.
user-on-cooldown =
    Du har brukt denne kommandoen for mange ganger. Du kan prøve igjen om { PERIOD($period) }.
command-on-cooldown =
    `{ $command }` har blitt brukt for mange ganger i denne kanalen. Du kan prøve igjen om { PERIOD($period) }.
missing-permissions = Du har ikke tilgang til denne handlingen
cannot-paginate =
    Jeg trenger tillatelsen "{ $permission ->
        [embed-links] Bygg Inn Lenker
        [send-messages] Send Meldinger
        [add-reactions] Legg Til Reaksjoner
       *[read-message-history] Les Meldingshistorikk
    }"

# Bible Cog

## Commands

-bible-version =
    { $number ->
       *[singular] Bibel versjon
        [plural] Bibel versjoner
    }

serverprefs = serverprefs
    .description = Server instillinger

serverprefs__setdefault = setdefault
    .description = Set the default { -bible-version } for this server
    .PARAM--version--name = version
    .PARAM--version--description = { -bible-version }
    .response = Server version set to `{ $version }`

serverprefs__unsetdefault = unsetdefault
    .description = Unset the default version for this server
    .deleted = Server version deleted
    .already-deleted = Server version already deleted

prefs = prefs
    .description = Preferences commands

prefs__setdefault = settstandard
    .description = Still inn din standard bibelversjon
    .PARAM--version--name = versjon
    .PARAM--version--description = Bibelversjon
    .response = Versjon satt til `{ $version }`

prefs__unsetdefault = unsetdefault
    .description = Unset your default { -bible-version }
    .deleted = Default version unset
    .already-deleted = Default version already unset

verse = vers
    .description = Slå opp et vers
    .PARAM--reference--name = referanse
    .PARAM--reference--description = En versreferanse
    .PARAM--version--name = versjon
    .PARAM--version--description = Versjonen der du skal slå opp verset
    .PARAM--only_me--name = bare_meg
    .PARAM--only_me--description = Om du skal vise verset til deg selv eller alle

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
no-user-version = You must first set your default version with `/version set`
invalid-version = `{ $version }` is not a valid version. Check `/bibles` for valid versions
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

creed = trosbekjennelse
    .description = Historiske trosbekjennelser

creed__apostles = apostolske
    .description = Den apostolske trosbekjennelse

creed__athanasian = athanasiske
    .description = Den athanasiske trosbekjennelsen

creed__chalcedon = kalsedon
    .description = Den kalsedonske definisjonen

creed__nicene = nikanske
    .description = Den nikanske trosbekjennelsen

creed__nicene325 = nikanske325
    .description = Den nikanske trosbekjennelse (325 e.Kr.)

creed__nicene381 = nikanske381
    .description = Den nikanske trosbekjennelse (381 e.Kr.)

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

notice = varsel
    .description = Vis varsel om avvikling av tekstkommandoer
