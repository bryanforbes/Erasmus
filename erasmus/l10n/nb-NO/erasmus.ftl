# General error messages

generic-error = Noe gikk galt
no-private-message = Denne handlingen er ikke tilgjengelig i private meldinger
only-private-message = Denne handlingen er bare tilgjengelig i private meldinger
missing-required-argument = Du mangler `{ $name }`
cooldown-error = Du kan prøve igjen om { PERIOD($period) }.
user-on-cooldown = Du har utført denne handlingen for mange ganger. Du kan prøve igjen om { PERIOD($period) }.
command-on-cooldown = Du har utført denne handlingen for mange ganger i denne kanalen. Du kan prøve igjen om { PERIOD($period) }.
missing-permissions = Du har ikke tilgang til denne handlingen
cannot-paginate =
    { $permission ->
        [embed-links] Jeg trenger tillatelsen "Bygg Inn Lenker"
        [send-messages] Jeg trenger tillatelsen "Send Meldinger"
        [add-reactions] Jeg trenger tillatelsen "Legg Til Reaksjoner"
       *[read-message-history] Jeg trenger tillatelsen "Les Meldingshistorikk"
    }

# Bible Cog


## Commands

-bible-version =
    { $number ->
       *[singular] Bibel versjon
        [plural] Bibel versjoner
    }
serverprefs = serverpreferanse
    .description = Server instillinger
serverprefs__unsetdefault = fjernstandard
    .description = Fjern standard versjonen for denne serveren
    .deleted = Versjonen som blir brukt på serveren har blitt slettet
    .already-deleted = Versjonen som blir brukt på serveren har allerede blitt slettet
verse = vers
    .description = Søk etter et vers
    .PARAM--reference--name = referanse
    .PARAM--reference--description = Vers referanse
    .PARAM--version--name = versjon
    .PARAM--version--description = Hvilke versjon som har verset
    .PARAM--only_me--name = bare_meg
    .PARAM--only_me--description = Velg om du vil vise verset til bare deg selv, eller alle

## Errors


# Confessions Cog


## Commands

confess = forkynnelse
    .description = Trosbekjennelser
confess__cite = siter
    .description = Siter en seksjon fra en trosbekjennelse
    .PARAM--source--name = Kilde
    .PARAM--source--description = Trosbekjennelsen du vil sitere
    .PARAM--section--name = Seksjon
    .PARAM--section--description = Seksjonen du vil sitere
confess__search = søk
    .description = Søk etter begrep i en trosbekjennelse
    .PARAM--source--name = kilde
    .PARAM--source--description = Velg hvilke trosbekjennelse du søker i
    .PARAM--terms--name = uttrykk
    .PARAM--terms--description = uttrykk du søker etter
    .title = Resultater fra { $confession_name }
    .no-results = Jeg fant resultater
    .footer = Side { $current_page }/{ $max_pages } ({ $total } resultater)
    .stop-button = Stop
    .unknown-error = Noe gikk galt, beklager!
    .embed-links-error = Din bruker har ikke tillatelse å poste dette i denne kanalen.
    .cannot-be-controlled-error = Denne handlingen er dessverre ikke tilgjengelig
    .modal-title = Gå rett til side
    .modal-input-label = Side
    .modal-input-placeholder = Side nummer
    .modal-generic-error = Det har skjedd en feil
    .modal-not-a-number-error = Du må skrive inn et nummer

## Errors

no-section =
    { $section_type ->
       *[CHAPTERS] `{ $confession }` har ikke et paragraf `{ $section }`
        [QA] `{ $confession }` har ikke et spørsmål `{ $section }`
        [ARTICLES] `{ $confession }` har ikke en artikkel `{ $section }`
    }
no-sections =
    { $section_type ->
       *[chapters] `{ $confession }` har ingen kapitler
        [paragraphs] `{ $confession }` har ingen paragrafer
        [articles] `{ $confession }` har ingen artikler
    }

# Creeds Cog


## Commands

creed = trosbekjennelse
    .description = Historiske trosbekjennelser
creed__apostles = apostlene
    .description = Apostlenes trosbekjennelse
creed__athanasian = athanasian
    .description = Athanasian trosbekjennelse
creed__chalcedon = chalcedon
    .description = Chalcedonian trosbekjennelse
creed__nicene = nicene
    .description = Nicene trosbekjennelse
creed__nicene325 = nicene325
    .description = Nicene trosbekjennelse (325 e.Kr.)
creed__nicene381 = nicene381
    .description = Nicene trosbekjennelse (381 e.Kr.)

# Misc Cog


## Commands

invite = inviter
    .description = Bruk en link for å inivitere Erasmus til din server
about = informasjon
    .description = Informasjon om Erasmus
    .title = Om Erasmus
    .guilds = Guilds
    .channels = Kanaler
    .footer = Laget av discord.py v{ $version }
    .invite = Inviter Erasmus
    .support-server = Offisiell Discord support server
notice = varsel
    .description = Vis text-kommando
