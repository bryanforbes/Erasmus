# General error messages

generic-error = Noe gikk galt
no-private-message = Denne handlingen er ikke tilgjengelig i private meldinger
only-private-message = Denne handlingen er bare tilgjengelig i private meldinger
missing-required-argument = Du mangler `{ $name }`
cooldown-error = Du kan prøve igjen om { PERIOD($period) }.
user-on-cooldown = Du har utført denne handlingen for mange ganger. Du kan prøve igjen om { PERIOD($period) }.
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
serverprefs = { "" }
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


## Errors


# Creeds Cog


## Commands


# Misc Cog


## Commands

notice = varsel
    .description = Vis text-kommando
