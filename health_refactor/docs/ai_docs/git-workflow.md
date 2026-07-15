# Git workflow

How we branch, review, and release code in **product-dashboard-ai**.

Both **`dev`** and **`main`** are protected. Do not push directly to them — always use pull requests.

## Branch roles

| Branch | Purpose |
|--------|---------|
| **`dev`** | Integration branch. All feature and fix PRs merge here first. |
| **`main`** | Production. Only receives code that has been tested on `dev`. |
| **`feature/...`** | New work (e.g. `feature/chat-streaming`). |
| **`fix/...`** | Bug fixes (e.g. `fix/retrieval-timeout`). |

## Flow overview

```text
feature/xyz ──PR──► dev ──PR (release)──► main
                      │
                      └── Actions → Deploy to Dev (manual, Render)
```

CI (lint + test) runs on every PR and push to **`dev`** and **`main`**
(`.github/workflows/ci.yml`).

Deploy to the Render **dev** environment is **manual**: after CI passes on
`dev`, run **Actions → Deploy to Dev** (`.github/workflows/deploy-dev.yml`).

---

## Starting new work

Always branch from the latest **`dev`**, not `main`.

```bash
git checkout dev
git pull origin dev
git checkout -b feature/my-change
# or: git checkout -b fix/my-bug
```

Make changes, commit, and push:

```bash
git add .
git commit -m "Describe the change"
git push -u origin feature/my-change
```

Open a **pull request into `dev`** on GitHub.

Before opening the PR, run locally:

```bash
make lint
make test
```

Wait for CI to pass, get review if required, then merge the PR into **`dev`**.

---

## Deploying to dev (Render)

1. Your change is merged into **`dev`**.
2. Confirm CI is green on `dev`.
3. GitHub → **Actions → Deploy to Dev → Run workflow**.
4. Verify the Render dev service updated.

Pushing to `dev` does **not** auto-deploy; the deploy workflow is manual only.

---

## Releasing to production

When a batch of work on **`dev`** is ready for prod:

1. Open a pull request **`dev` → `main`** (release PR).
2. CI runs on that PR — lint and tests must pass.
3. Review and merge into **`main`**.
4. Deploy production from **`main`** (per your Render/prod setup).

You do **not** merge `dev` → `main` before starting each new feature. That
step is only for **releases**.

---

## Checklist

- [ ] Pulled latest **`dev`** before creating the branch
- [ ] Branch name is `feature/...` or `fix/...`
- [ ] PR targets **`dev`** (not `main`) for normal work
- [ ] `make lint` and `make test` pass locally
- [ ] CI green on GitHub
- [ ] Manual **Deploy to Dev** after merge (when you want Render dev updated)

---

## Common mistakes

| Mistake | Correct approach |
|---------|------------------|
| Branch from `main` for new work | Branch from **`dev`** |
| PR feature straight to `main` | PR to **`dev`** first |
| Merge `dev` → `main` before every feature | Only merge **`dev` → `main`** for releases |
| Push directly to `dev` or `main` | Open a PR (branches are protected) |
| Expect push to `dev` to deploy | Run **Deploy to Dev** manually in Actions |

---

## Quick reference

```bash
# New feature or fix
git checkout dev && git pull origin dev
git checkout -b feature/short-description
# ... work, commit ...
git push -u origin feature/short-description
# Open PR → dev on GitHub

# After merge to dev (optional deploy)
# GitHub Actions → Deploy to Dev → Run workflow

# Release to prod
# Open PR dev → main on GitHub, merge when CI passes
```
