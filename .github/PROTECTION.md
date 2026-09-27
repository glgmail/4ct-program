# What protects this repository

Applied and verified against `glgmail/4ct-program` on 2026-09-27.

The repository is **public**. That is what makes the protections below
available: on the account's GitHub Free plan they are free for public
repositories and would need GitHub Pro for a private one. It is also what
makes the fork-pull-request rules below matter.

> Public is the settled choice, made on 2026-09-27, and the plan of record
> has been updated to match — see the last section.

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

### Why `enforce_admins` stays off

**Do not turn it on while Gabriel is the only collaborator.** It would
deadlock the repository permanently.

GitHub does not let anyone approve their own pull request. `main` requires
one approving review, and `enforce_admins` removes the admin's ability to
merge past an unmet requirement. Gabriel is the sole collaborator, so he
authors every pull request, cannot approve any of them, and — with
`enforce_admins` on — could not merge any of them either. There would be no
way out short of an admin turning the setting back off.

With it off, the configuration does what was actually wanted:

- **Everyone other than Gabriel** is bound by the required review, the
  required code-owner review, and both required status checks. An agent
  holding `contents: write` cannot merge anything.
- **Gabriel** merges his own pull requests using the admin bypass. His
  judgement is the approval; the checks still run and still show red or
  green on the pull request, he is simply not blocked by the
  self-approval rule.

Revisit this the moment a second person gets write access. At that point
turn it on, because the deadlock disappears:

```bash
gh api -X POST repos/glgmail/4ct-program/branches/main/protection/enforce_admins
```

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

`.github/workflows/claude.yml` authenticates with the **`ANTHROPIC_API_KEY`**
repository secret, so runs bill to Anthropic API credits rather than to a
Claude subscription. Two properties of that worth keeping in mind on a public
repository: a workflow run from a forked pull request is never given repository
secrets, and such a run additionally needs an owner's approval before it
starts. The key is reachable only from branches in this repository.

## History

An earlier revision of this file recorded that none of the above was
available, because the repository was private on a Free plan and GitHub
refused all four protections. Making the repository public removed that
limitation. `.github/workflows/guard.yml`, which reported violations after
the fact because nothing could prevent them, has been deleted — real
protection replaces it.

## Settled: the repository stays public

Gabriel decided on 2026-09-27 that the repository stays public. `README.md`
has been updated to match, keeping the release discipline that the original
wording carried: readable is not released, and a result is announced only as
a tagged release he approves.

What that decision changes, and does not:

- **Unchanged.** No agent may alter visibility, publish a release, push a
  tag, or post to arXiv. The `v*` ruleset and the `public-release`
  environment enforce the last two, and agent credentials carry no admin
  rights.
- **Unchanged.** A tier 3 or tier 4 claim is formalized in Lean before
  release approval or referee contact. Being publicly readable is not a
  claim.
- **Changed.** Work in progress is visible as it happens, including wrong
  turns and dead ends. The `notes/` logs are written to be read that way:
  results under the trust rule, everything else filed as a lead.
- **Changed.** Fork pull requests are possible, which is why the
  fork-PR rules above and the runner mitigations in `.github/RUNNER.md`
  exist.

One thing to check before task F3 lands the data. Git LFS quotas are
per-account and are not lifted for public repositories, while a public
repository means anyone can clone and draw on the bandwidth allowance.
F3 imports 8,202 configuration files plus the discharging rules. Check the
account's LFS storage and bandwidth allowance against that before the import,
rather than discovering it when LFS starts refusing fetches.

The plan of record has been updated to match: its decisions, checklist and
README draft now say public, and its kickoff prompt is kept verbatim as the
record of what was originally asked, with a dated note above it saying which
of its premises have since changed.
