# General error messages

generic-error = En feil oppstod
no-private-message = Denne kommandoen er ikke tilgjengelig i private meldinger
only-private-message = Denne kommandoen er kun tilgjengelig i private meldinger
missing-required-argument = Det nødvendige argumentet `{ $name }` mangler
cooldown-error = Du kan prøve igjen om { PERIOD($period) }.
user-on-cooldown =
    Du har brukt denne kommandoen for mange ganger. Du kan prøve igjen om { PERIOD($period) }.
command-on-cooldown =
    `{ $command }` har blitt brukt for mange ganger i denne kanalen. Du kan prøve igjen om { PERIOD($period) }.
missing-permissions = Du har ikke de riktige tillatelsene til å kjøre denne kommandoen
cannot-paginate =
    Jeg trenger tillatelsen "{ $permission ->
        [embed-links] Bygg inn lenker
        [send-messages] Send meldinger
        [add-reactions] Legg til reaksjoner
       *[read-message-history] Les meldingshistorikk
    }"


# Bible Cog

## Commands

prefs__setdefault = settstandard
    .description = Still inn din standard bibelversjon
    .PARAM--version--name = versjon
    .PARAM--version--description = Bibelversjon
    .response = Versjon satt til `{ $version }`

verse = vers
    .description = Slå opp et vers
    .PARAM--reference--name = referanse
    .PARAM--reference--description = En versreferanse
    .PARAM--version--name = versjon
    .PARAM--version--description = Versjonen der du skal slå opp verset
    .PARAM--only_me--name = bare_meg
    .PARAM--only_me--description = Om du skal vise verset til deg selv eller alle

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

notice = varsel
    .description = Vis varsel om avvikling av tekstkommandoer
