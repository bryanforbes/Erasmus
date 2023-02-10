# Version UNRELEASED

* Improved Daily Bread resiliency
* Improve output of `/confess search`

# Version 23.2.0

* Fixed bug in Daily Bread fetching

# Version 23.1.1

* Fixed `/daily-bread status` showing the wrong time

# Version 23.1.0

* Added Daily Bread functionality:
  * `/daily-bread show`
  * `/daily-bread status`
  * `/serverprefs daily-bread set` (Administrator only)
  * `/serverprefs daily-bread stop` (Administrator only)

# Version 22.11.1

* Added The Second Helvetic Confession
* Added The Augsburg Confession

# Version 22.10.0

* Renamed some commands:
  * `/prefs setdefault` -> `/version set`
  * `/prefs unsetdefault` -> `/version clear`
  * `/serverprefs setdefault` -> `/serverprefs version set`
  * `/serverprefs unsetdefault` -> `/serverprefs version clear`
* Added `/version show`
* Added `/serverprefs version show` (Administrator only)
* Fixed verse display incorrectly italicizing Jesus' words
* Added version and shard number to activity display

# Version 22.9.7

* Fixed searching confessions with no section titles

# Version 22.9.6

* Added Luther's 95 theses

# Version 22.9.5

* Improved verse lookup regular expressions
* Fixed searching NRSV
* Switched to Brenton Septuagint for LXX

# Version 22.9.4

* Fixed a bug in message lookup that ignored brackets

# Version 22.9.3

* Re-enable bracket notation (`[John 1:1]`)
* Added `/news` command

# Version 22.9.2

* Added The London Baptist Confession of Faith (1646)
* Renamed "The Second London Baptist Confession of Faith" to "The London Baptist Confession of Faith (1689)"

# Version 22.9.1

* Added Baptist Faith & Message

# Version 22.9.0

* Removed text-based commands
* Added version number to `/about`
