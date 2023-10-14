message = This is a message
    .attribute = This is an attribute
    .another-attribute = This is another attribute with { $something }

another-message = This is another message with { $something }

interval-message = There are { INTERVAL($interval) } left
interval-message-implicit = There are { $interval } left
interval-message-format-short = There are { INTERVAL($interval, format: "short") } left
interval-message-format-narrow = There are { INTERVAL($interval, format: "narrow") } left
interval-message-separator = There are { INTERVAL($interval, separator: ", ") } left
