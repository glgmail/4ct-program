# What protects this repository

Applied and verified against `glgmail/4ct-program` on 2026-09-27.

The repository is **public**. That is what makes the protections below
available: on the account's GitHub Free plan they are free for public
repositories and would need GitHub Pro for a private one. It is also what
makes the fork-pull-request rules below matter.

> The plan of record says this repository is private. It is not. That
> conflict is Gabriel's to resolve — see "Open question" at the end.

## Branch protection on `main`

| Setting | Value |
| --- | --- |
| Required status checks | `lean-build`, `checks` — strict (branch must be up to date) |
| Required approving reviews | 1 |
| Code-owner review | required |
| Dismiss stale reviews on push | yes |
| Require approval of the most recent push | yes |
| Conversation resolution | required |
| Force pushes | blocked |
| Branch deletion | blocked |
| Fork syncing | blocked |
| `enforce_admins` | **off** — see below |

`enforce_admins` is deliberately off for now: `lean-build` cannot report
until the self-hosted runner exists, so with it on, nothing could be merged
at all. **Turn it on once the runner is registered:**

```bash
gh api -X POST repos/glgmail/4ct-program/branches/main/protection/enforce_admins
```

Until then, Gabriel can merge past a pending check. Nobody else can: everyone
else is stopped by the required review and the required checks.

## Release tags

Ruleset `protect-release-tags`, active, target `tag`, matching
`refs/tags/v*`, with rules `creation`, `update`, `deletion` and
`non_fast_forward`, and a bypass for the **repository admin role only**.

In practice: only Gabriel can create, move or delete a `v*` tag. Everyone
else — every agent credential included — is blocked at the push.

## Releases

The `public-release` environment has **Gabriel as a required reviewer**. A
`release` workflow run pauses until he approves it in the Actions UI.

`.github/workflows/release.yml` is gated four ways over and above that:
`workflow_dispatch` is its only trigger, it runs only when
`github.actor == github.repository_owner`, it requires the literal input
`RELEASE`, and it holds `contents: read` with no `administration`
permission — so it cannot create a release, push a tag, or change
visibility. It builds an archive, attaches it to the run, and stops.
Publishing anywhere else stays manual.

## Fork pull requests

The repository is public, so anyone can fork it and open a pull request.

- **Workflows on fork pull requests require approval from all outside
  contributors** (`all_external_contributors`), the strictest policy GitHub
  offers. Nothing from a fork runs until someone approves that run.
- Forking itself cannot be disabled: GitHub only allows that on
  organisation-owned private repositories.
- A fork pull request's `GITHUB_TOKEN` is read-only and it cannot read
  secrets.

**This is the sharpest edge in the whole setup.** A self-hosted runner plus a
public repository means one careless "Approve and run" executes a stranger's
code on Gabriel's machine. `.github/RUNNER.md` opens with the mitigations;
they are not optional.

## Everything else

- Default `GITHUB_TOKEN` permission is **read**, and
  `can_approve_pull_request_reviews` is **false** — no workflow can approve a
  pull request.
- `allow_auto_merge` is off, so nothing merges itself.
- `allow_rebase_merge` off, `delete_branch_on_merge` on, wiki and projects
  off.
- `.github/CODEOWNERS` makes Gabriel the owner of everything, and of
  `lean/Statements/`, the toolchain pins, the licences and CI explicitly.
  Combined with required code-owner review, every pull request needs him.
- `.github/workflows/claude.yml` runs only when the actor is the repository
  owner, and holds `contents` / `pull-requests` / `issues` write and nothing
  more: no administration, no release rights.

## Agent credentials

The Claude GitHub App is installed on this repository only, with
**contents, pull requests and issues** write access and nothing else. Check
it at <https://github.com/settings/installations>. If it ever asks for
`administration`, decline.

Note what the tag ruleset adds here: even holding `contents: write`, an agent
cannot create a `v*` tag, because the ruleset bypass is admin-only.

## History

An earlier revision of this file recorded that none of the above was
available, because the repository was private on a Free plan and GitHub
refused all four protections. Making the repository public removed that
limitation. `.github/workflows/guard.yml`, which reported violations after
the fact because nothing could prevent them, has been deleted — real
protection replaces it.

## Open question

The plan of record says, and `README.md` repeats:

> This repository is private. Nothing leaves it except as a tagged public
> release approved by Gabriel.

That is no longer true, and the program's stated position is "no outreach
until a tier 3 or tier 4 result needs referees". A public repository is a
form of outreach whether or not anyone is reading it.

Either the plan of record changes to match the repository, or the repository
goes back to private and these protections need GitHub Pro. Nobody but
Gabriel should decide which, and until he does, `README.md` is left as it
stands rather than quietly edited to match the new state.
