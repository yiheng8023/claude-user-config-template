# Contributing

Contribute reusable public-safe structure, documentation, validation and setup.
Keep private memory, credentials, machine paths and account configuration out.
Run the explicit public gate and regression tests before opening a pull request:

```bash
python -B scripts/verify.py --public
python -B -m unittest discover -s tests -p "test_*.py" -v
node --test tests/*.test.js
```

The public CI gate cannot be changed by a local visibility-policy override.
