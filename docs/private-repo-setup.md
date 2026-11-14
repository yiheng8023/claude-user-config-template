# Private Repository Setup

1. Create a private derivative of this public template.
2. Replace placeholder global guidance and add reviewed private commands/hooks.
3. Change `config/repository-policy.json` visibility to `private`, and change the
   derivative CI verification flag to `--private`.
4. Keep credentials in local environment variables or local-only config files.
5. Run the private validator and behavior checks before committing.

```bash
python -B scripts/verify.py --private
python -B -m unittest discover -s tests -p "test_*.py" -v
node --test tests/*.test.js
python -B scripts/install.py --dry-run
python -B scripts/install.py
```

Default restore adds missing fields/files and retains existing configuration.
Use `--overwrite-files` only for reviewed file updates; it backs up existing
files and retains unrelated commands/hooks. Settings remain missing-only.
For a return to the public template, declassify and run `--public`; private
validation is not evidence of public safety. Do not publish private state.
