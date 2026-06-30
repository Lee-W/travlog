# Publishing a draft with auto-merge

## Repository setup

1. Enable **Allow auto-merge** under **Settings → General → Pull Requests**.
2. Protect `main` and require the existing pull-request `check` status check.
3. Add a repository Actions secret named `PUBLISH_TOKEN`. Use a fine-grained
   personal access token limited to this repository with **Contents: Read and
   write** permission.
4. Use squash merge for publishing pull requests so the metadata preparation
   commit is folded into the `new post` commit.

The separate token is necessary because commits pushed with the workflow's
built-in `GITHUB_TOKEN` do not normally trigger another workflow run. CI must
run against the prepared commit before GitHub completes auto-merge.

## Publishing flow

1. Open a pull request whose title starts with `new post:`.
2. Leave `Status: draft` in the post metadata.
3. The pull-request `check` job fails and reports the changed draft posts.
4. Select **Enable auto-merge** and confirm squash merge.
5. The `Prepare publication` workflow updates `Date`, removes `Status: draft`,
   and pushes a metadata commit to the pull-request branch.
6. CI runs against the new commit. GitHub merges it after all required checks
   pass, then the existing `main` workflow deploys the site.

Only Markdown posts changed relative to the pull request's base branch are
prepared. Pull requests from forks are intentionally unsupported because the
workflow writes back to the source branch.
