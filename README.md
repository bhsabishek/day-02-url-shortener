# Day 2 - "Two pipelines, one app"

**Stack:** Python 3.12 + Flask + SQLite (a URL shortener)
**Tools today:** Jenkins (L1, new) · GitHub Actions (L2) · Docker (L2) · Git (L2) · Linux (L2)
**Time box:** about 3 to 4 hours. Part 5 is a stretch goal.

## The ticket

> The team is migrating from Jenkins to GitHub Actions, but for a few weeks
> **both** have to run. This URL shortener has failing tests and has never been
> containerized. Fix it, then build the same pipeline in both tools so you can
> compare them, and deploy the image the Jenkins pipeline builds.

## Carried over from Day 1 (now expected as standard)
- Work on a **feature branch** and open a **PR**. Do not commit to `main`.
- GitHub Actions triggers on **push and pull_request**, uses **caching**,
  and pins its action versions.
- Docker image is **non-root** and has **no dev dependencies**.
- Test the success path of every endpoint, not just errors.
- Commit messages that say what changed.

## API contract

| Method | Path | Expected behaviour |
|--------|------|--------------------|
| GET | `/health` | `200` `{ "status": "ok" }` |
| POST | `/shorten` | body `{ "url": "..." }`. `201` `{ "code", "url" }`. `400` unless it is a valid `http` or `https` URL |
| GET | `/<code>` | `302` redirect to the original URL. Counts a hit. `404` if unknown |
| GET | `/stats/<code>` | `200` `{ code, url, hits, created_at }`. `404` if unknown |

Configuration:
- `DB_PATH`: where the SQLite file lives (default `./shortener.db`)
- `PORT`: port to listen on (default `5000`)

Production rules: the Flask development server must **not** run in the container,
debug mode must be off, and data must **survive** the container being recreated.

## Your job

**Part 1 - Fix the app**
- Get `pytest` fully green locally. (You will need to work out what a clean machine needs installed.)
- Some defects only show up outside the test suite, so keep a list as you go.

**Part 2 - Git + GitHub Actions**
- New public repo, feature branch, PR.
- Workflow: lint-free install with pip caching, run tests, then (only if tests pass)
  build the image and prove it works with a `/health` call. The job must fail if it does not respond.

**Part 3 - Docker**
- Production-style image per the rules above. Run it locally or on EC2 and prove that
  a link created before you `docker rm -f` the container still works after you start a new one.

**Part 4 - Jenkins** (the new tool)
- Install Jenkins on your EC2 instance (not in a container this time). Follow the official Linux install
  guide for your distro. Make sure it is reachable on port 8080 **from your IP only**.
- Install the plugins you need. Write down which ones and **why** each is needed.
- Create a **Pipeline job** that reads a `Jenkinsfile` from your repo (Pipeline script from SCM).
- The Jenkinsfile (declarative) must have these stages: checkout, test, build image, smoke test, deploy.
  - Test results must show up in Jenkins (not just in the console log).
  - A failing test must fail the build and stop the later stages.
  - Clean up after itself (containers and workspace).
  - No secrets or IPs hardcoded in the file.
- Make a build go red on purpose, then green.

**Part 5 - Stretch**
- Trigger Jenkins automatically from GitHub (webhook, or SCM polling if you prefer).
- Push the image to a registry using Jenkins **credentials** (never paste a token in the Jenkinsfile).
- Paste one failed Jenkins console log into an AI assistant and ask it to diagnose. Record what it got
  right and what it got wrong.

## Done when (send me these)
1. Repo link and the PR link.
2. GitHub Actions: a red run, a green run, and evidence of a cache hit.
3. Jenkins: a red build and a green build (screenshot of Stage View and the test results page).
4. `curl` output from outside the server: shorten, redirect (show `302`), stats with hits.
5. Proof of persistence after container recreation.
6. Your documentation (template below).

## Documentation template
1. **Scenario** - in your own words
2. **Bugs found** - symptom, root cause, fix, and where it showed up (tests / container / Jenkins)
3. **GitHub Actions pipeline** - each step and why
4. **Jenkins** - install steps, plugins and why, job config, Jenkinsfile explained stage by stage
5. **Dockerfile** - why each line
6. **Deployment** - where, how, verification, persistence test
7. **GitHub Actions vs Jenkins** - a comparison table (setup effort, config location, secrets, runners, plugins, hosting, cost, where you would choose each)
8. **Errors you hit** and how you got unstuck
9. **Clean-up**
10. **3 interview questions** this prepared you for

## Rules
- Stuck for 20 minutes? Docs first, then ask me for **Hint 1**, **2** or **3**.
- You write the workflow, Dockerfile and Jenkinsfile yourself.
- No secrets, tokens, or AWS account numbers in your repo or screenshots. Crop your terminal prompt (it shows your IP).
- Jenkins and the app port should only be open to your IP. When done, stop or terminate the EC2 instance.
