# Relationship Map

```text
claude-user-config-template
  -> public-safe template, placeholder examples, validation, setup guidance

private claude-user-config
  -> real Claude Code configuration, memory, commands, hooks, local policy

optional sibling templates
  -> may reuse the same pattern without becoming dependencies or authority
```

This repository is independently buildable and verifiable. The template never
back-writes a private repository. Private improvements may
be promoted into the template only after filtering, review, and declassification.
