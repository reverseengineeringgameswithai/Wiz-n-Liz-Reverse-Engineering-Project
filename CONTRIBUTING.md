# Contributing

Forks, fixes and new findings are welcome.

- **License.** By submitting a contribution you agree to license it under the
  license of the files it changes (MIT unless a file says otherwise; see
  [NOTICE.md](NOTICE.md)) and confirm that you have the right to do so.
- **No game content.** Never commit a ROM, a rebuilt or patched ROM, extracted
  graphics/audio/text, bulk disassembly, traces, save states or recordings.
  Keep them in the ignored `local/` directory.
- **Workflow.** Read [START_HERE.md](START_HERE.md) and open `vault/` in
  Obsidian. Findings record evidence, confidence and how to reproduce them;
  keep observations separate from interpretation.
- **Checks.** Before opening a pull request, run:

  ```sh
  python3 tools/project.py test
  python3 tools/project.py check-vault
  python3 tools/project.py check-hygiene
  ```

  Native changes also need `python3 tools/project.py test --preset debug`.
