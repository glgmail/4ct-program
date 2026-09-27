# What protects this repository, and what does not

Checked against `glgmail/4ct-program` on 2026-09-27.

The account is on **GitHub Free**. On a Free plan, a **private** repository
gets none of GitHub's branch, ruleset, tag or environment protections. Every
probe below was run against this repository and the response recorded.

| Protection | Available | What GitHub said |
| --- | --- | --- |
| Classic branch protection (`PUT /repos/../branches/main/protection`) | **no** | `403 Upgrade to GitHub Pro or make this repository public to enable this feature.` |
| Repository rulesets (`POST /repos/../rulesets`) | **no** | `403 Upgrade to GitHub Pro or make this repository public to enable this feature.` |
| Tag protection (`POST /repos/../tags/protection`) | **no** | `404` — GitHub retired this API; tags are protected by rulesets, which need Pro |
| Environment required reviewers | **no** | `422 Failed to create the environment protection rule. Please ensure the billing plan supports the required reviewers protection rule.` |

Making the repository public would unlock all four. The plan of record
forbids it, so that is not an option.

## What is in place instead

Preventive, and actually enforced:

- The repository is private, and `has_wiki` / `has_projects` are off.
- `allow_auto_merge` is **false**, so nothing can merge itself.
- `allow_rebase_merge` is off; `delete_branch_on_merge` is on.
- The default `GITHUB_TOKEN` is **read-only** and
  `can_approve_pull_request_reviews` is **false**, so no workflow can approve
  a pull request.
- `.github/workflows/release.yml` has no trigger but `workflow_dispatch`, runs
  only when `github.actor == github.repository_owner`, requires the literal
  string `RELEASE` as an input, holds `contents: read` and no
  `administration` permission — so it cannot create a release, push a tag, or
  change visibility — and fails if the repository has stopped being private.
- `.github/workflows/claude.yml` runs only when the actor is the repository
  owner, and holds `contents` / `pull-requests` / `issues` write and nothing
  more.
- `.github/CODEOWNERS` makes Gabriel the owner of everything, and of
  `lean/Statements/`, the toolchain pins, the licences and CI explicitly.

Detective, reported after the fact by `.github/workflows/guard.yml`:

- a push to `main` that came from no pull request opens an issue and fails;
- a `v*` tag pushed by anyone but Gabriel opens an issue and fails;
- any push while the repository is not private opens an issue and fails.

## The gap, stated plainly

Nothing above can **stop** a direct push to `main`, a force-push, a branch
deletion, or a `v*` tag. Nothing makes the `lean-build` and `checks`
workflows *required* — they run on every pull request and report, but GitHub
will not block a merge on them. The discipline is real but it is
conventional, not enforced.

Practically, the exposure is small right now: Gabriel is the only human with
write access. It grows the moment anyone else, or any agent credential,
can push.

## Closing the gap

**GitHub Pro** (about $4/month) turns all four back on for private
repositories. After upgrading, run these — they are the exact payloads that
were refused, so they should apply as they stand.

### 1. Protect `main`

```bash
cat > /tmp/bp.json <<'JSON'
{
  "required_status_checks": { "strict": true, "contexts": ["lean-build", "checks"] },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1,
    "require_last_push_approval": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": false
}
JSON
gh api -X PUT repos/glgmail/4ct-program/branches/main/protection --input /tmp/bp.json
```

`enforce_admins` is deliberately `false`: Gabriel must be able to merge the
first pull request before the self-hosted runner exists, since `lean-build`
cannot report until it does. Set it to `true` once the runner is up.

### 2. Protect `v*` tags

```bash
cat > /tmp/rs-tags.json <<'JSON'
{
  "name": "protect-release-tags",
  "target": "tag",
  "enforcement": "active",
  "bypass_actors": [
    { "actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always" }
  ],
  "conditions": { "ref_name": { "include": ["refs/tags/v*"], "exclude": [] } },
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    { "type": "creation" }
  ]
}
JSON
gh api -X POST repos/glgmail/4ct-program/rulesets --input /tmp/rs-tags.json
```

`actor_id: 5` is the repository **admin** role, so only Gabriel can create a
`v*` tag; everyone else is blocked by the `creation` rule.

### 3. Require Gabriel's review on releases

```bash
gh api -X PUT repos/glgmail/4ct-program/environments/public-release \
  -F wait_timer=0 -F prevent_self_review=false \
  -F 'reviewers[][type]=User' -F 'reviewers[][id]=334307874'
```

The `public-release` environment already exists, with no protection rules on
it. This adds Gabriel as the required reviewer, so a `release` run pauses
until he approves it.

### 4. Then

Delete `.github/workflows/guard.yml` — real protection replaces the
tripwires — and set `enforce_admins` to `true` once `lean-build` can pass.

## Agent credentials

The Claude GitHub App is installed on this repository only, with
**contents, pull requests and issues** write access and nothing else: no
administration, no ability to create a release or push a tag. Check it at
<https://github.com/settings/installations>. If the app ever asks for
`administration` or `Contents: admin`, decline.
