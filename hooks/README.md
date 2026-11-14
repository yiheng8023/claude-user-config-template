# Hooks

The supplied settings guardian is inert without a private declaration. It only
adds absent env keys and never restores permission grants. Copy the empty
`guarded-fields.example.json` to `guarded-fields.json` in a private derivative,
then deploy reviewed files through `scripts/install.py --overwrite-files`.
Existing values and unrelated hooks remain. Keep automatic upload/push hooks and
personal declarations in your private repository. See the root README for checks.
