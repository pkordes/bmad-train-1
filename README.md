# bmad-train-1

## BMAD Update

This project runs the **BMAD v7 preview alpha** (BMAD-METHOD `main`) with
**bmad-loop** from its `main` branch. Both change often and can break things
between updates, so update once a week on purpose rather than letting drift
pile up. Run every command from the project root.

### Weekly steps

1. **Read what changed.** Skim the recent commits and changelogs before
   updating, so a breaking change doesn't surprise you:
   - BMAD-METHOD: <https://github.com/bmad-code-org/BMAD-METHOD/commits/main>
   - bmad-loop: <https://github.com/bmad-code-org/bmad-loop/blob/main/CHANGELOG.md>

   While you're there, check whether v7 has been released (see
   [When v7 is released](#when-v7-is-released)).

2. **Start from a clean tree.** Commit or stash your work, so the update shows
   up as its own diff and is easy to roll back:

   ```bash
   git status
   ```

3. **Update the BMAD skills and runtime.** Open Claude Code in the project and
   ask:

   ```text
   bmad setup
   ```

   This runs `npx skills update -p -y` (it updates the BMAD-METHOD *and*
   bmad-loop skills listed in `skills-lock.json`), refreshes `_bmad/`, asks any
   new config questions, offers to delete renamed or retired skills, and offers
   any migration that applies. Read each offer before you accept it.

4. **Update the bmad-loop orchestrator tool.** `--reinstall` is required: a
   plain upgrade reuses the cached Git commit and won't pull new code.

   ```bash
   bmad-loop --version
   uv tool upgrade bmad-loop --reinstall
   bmad-loop --version
   ```

5. **Refresh the bmad-loop hooks.** This is safe to re-run: it leaves an
   existing `.bmad-loop/policy.toml` untouched and only re-registers hooks if
   they changed.

   ```bash
   bmad-loop init --project . --cli claude --cli codex --cli copilot --no-skills
   ```

   Keep `--no-skills`. Don't use `--force-skills` or `/bmad-loop-setup upgrade`
   here: on v7 the `bmad-loop-*` skills are managed by `npx skills` (step 3),
   and `--force-skills` would overwrite them with the tool's bundled copies.

6. **Verify.** In Claude Code, ask `bmad status`. Then run the bmad-loop
   preflight:

   ```bash
   bmad-loop validate --project .
   ```

   Every module should show as current, and `validate` should report no new
   failures compared with last week.

7. **Review and commit the update.**

   ```bash
   git status
   git diff
   ```

   If something broke, `git restore` / `git clean` the update and try again next
   week, or report it on the project's GitHub Issues.

### Known issue to recheck

- `bmad-retrospective` failed to install on 2026-10-26 because of a YAML error
  in its upstream `SKILL.md`. `bmad setup` (step 3) offers it again. Once it
  installs, delete this note.

### When v7 is released

The weekly steps stay the same: the skills track `main`, which becomes the v7
release line. Once v7 is out, consider pinning the bmad-loop tool to a release
tag for stability instead of following `main`:

```bash
uv tool install --force "bmad-loop[tui] @ git+https://github.com/bmad-code-org/bmad-loop.git@v<X.Y.Z>"
```

Then read the v7 release notes for any final migration step (`bmad setup`
offers it), and update this section.
