# Milestone 3

Link to repository: https://github.com/uchicago-capp-30320/ClearFeed.git 

## Repository Checklist

- [x] `.gitignore` - ensures "junk" files, private files, etc. are not tracked by Git
- [x] `README.md` - an entrypoint to the project for other developers: what is this? how do I interact with it?
- [x] `pyproject.toml` and `uv.lock` - tracking dependencies
- [x] `LICENSE` - license of your project
- [x] Issue Tracker configured (GitHub or elsewhere)
- [x] Each member makes at least one **pull request** from their local machine, that PR is merged by another member.
    - Ganon: https://github.com/uchicago-capp-30320/ClearFeed/pull/45 
    - Khushi: https://github.com/uchicago-capp-30320/ClearFeed/pull/44
    - Yuri: https://github.com/uchicago-capp-30320/ClearFeed/pull/17 
    - Grace: https://github.com/uchicago-capp-30320/ClearFeed/pull/47 
    - Teddy: Submitting PR before midnight
- [x] CI Linter task - a task that automatically runs a linter on every commit

Details on these files below.

## Optional

- [x] Branch Protection: [Link](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [x] pre-commit - <https://pre-commit.com> - ensures your teammates run the linters/etc. before committing in the first place.
- [ ] CI Test task - Similar to your linting task, something that runs your `pytest`s (and other tests) locally. Can be set up later, but wouldn't hurt to set up now and run a single simple `1+1=2` test or two that can be added to.

## Data Model Exercise

- teams/ClearFeed/m3_data_model.dbml
- teams/ClearFeed/m3_data_model.md
- teams/ClearFeed/m3_data_model.svg


## More Details

### README.md

This file should, at a minimum, provide the project name, some basic details, installation instructions (even if just `poetry install` for now) and an explanation of how the repository is laid out.

You might also add some badges: https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/adding-a-workflow-status-badge once you get your CI set up.

Top-level directories that you plan to use should be documented, taking special care to consider the following:

* If you are developing a project with a frontend & backend that will be run, it's probably good to make those separate repositories.
* Be sure not to mix data & code directories, data should have its own directory(ies) that are not co-mingled with code.
* Consider if your team wants to store notes or team administrative info in the repo itself, and if so give that its own directory as well.
* Avoid clutter in the root  of the repository, some files like `.gitignore` and `pyproject.toml` are fine, but generally anything that isn't config  should have a better place.

### .gitignore

.gitignore files ensure that large files, unimportant files, or sensitive files do not get added to git accidentally.

Your repository should have one that includes things like `*.pyc` to avoid adding python cache files, 
as well as your data directories where you might store large files.

Language specific `.gitignore` files: [Link](https://github.com/github/gitignore)

You may use these but should customize these to your needs, e.g. combine Python & JS ignores, add directories you plan to use for large files, etc.

### LICENSE

Add a LICENSE file of your chosen license, be sure to fill in details like name/year.

Details: [Link](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)

### pyproject.toml or equivalent

Have a file with your dependencies along with instructions in the README on how to use this.

A `poetry` refresher if needed: [Link](https://people.cs.uchicago.edu/~jturk/capp30320/guides/python/)

### Issue Tracker configured

We are using GitHub's issue tracker: https://github.com/orgs/uchicago-capp-30320/projects/13/views/3 


### each member makes at least one commit from their local machine

Have each team member make at least one commit, it can be adding their name to a repository, or just a test commit that edits the file.

I'd suggest each person make a branch and submit a PR to go through that process once.


### CI Test Task

You should have a GitHub CI (or equivalent) job that runs your tests.

You may not have tests yet, but you can create a single test and ensure it runs.

We'll be sharing a resource with more details on this soon and available for helping teams get this working as needed.

### CI Linter Task

You should have a GitHub CI (or equivalent) job that runs code linting.

This should run a tool like `ruff` or `flake8` to ensure your code quality is up to the team's standards.

Refer to those tool's documentation for details on how to configure them, but the default configurations are fine for most purposes, if you want to relax any of them (or turn on more for ruff) that's fine too.

It is up to you whether you enforce this via branch rules (see branch protection as well) but highly recommended.

### Branch Protection

It's a good idea to protect your main branch at a minimum, you can enforce the concept that nobody pushes to main, so that all commits will flow through a PR.
This *really* helps avoid mistakes as people get used to the workflow. For more information on branch protection, visit here: [Link](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)