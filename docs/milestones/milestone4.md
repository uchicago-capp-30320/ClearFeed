# Milestone 4: Preliminary Documentation

This milestone has three goals:

- encourage your team to carefully consider the work remaining between you and your goal
- allow us to provide detailed feedback & help identify potential gaps
- create documentation that will be useful in fostering communication within your team

Most questions about "are we documenting too much/too little" can be answered by considering these three goals. Otherwise, please ask!

Unlike prior milestones, this milestone should be implemented as a branch against *your* repository (not this one). For submission, make a PR against your repository (e.g. from feature/m4-docs to main) and add Praveen & I as reviewers.

There are a few requirements for this milestone:

## 1. Issue Tracker

GitHub Issues Tracker: https://github.com/orgs/uchicago-capp-30320/projects/13/views/3 

## 2. Model/Resource Documentation

Model_Resource_Documentation.md
Additional documentation on our data model can be found in docs/milestones/milestone3
 
## 3. Endpoint Documentation

docs/endpoints/admin.md
docs/endpoints/analysis.md

## 4. Architecture Documentation


See decisions/dependency-graph.md for a dependency graph
Write a high-level summary of your application's architecture aimed at onboarding a new team member.

What key details do they need to know to understand how evertthing fits together?

Think of this as the starting point of your documentation, it can refer people to the model/endpoint documentation as needed.

Key questions to consider, not all will apply to your project:

* Where does data come from?
* How does data flow through the system?
* What is the relationship between different modules? (I strongly suggest creating a dependency graph to show which modules depend upon which. If your graph is convoluted that is a sign that you may need to consider refactoring at some point.)
* What key concepts does the user need to understand?

---

## Format & Tools

Your documentation should live within your team's repository, preferably in a folder named `docs/`, unless a tool you choose dictates otherwise.

I'd recommend writing your documentation in markdown files, though you may also explore [restructuredText](https://sphinx-tutorial.readthedocs.io/step-1/) if you wish to use the popular Sphinx tool.

You are not required to use a documentation tool of any kind, but you may.  The two most common in Python are:

**Sphinx**
(`uv add sphinx`)

Quickstart: https://www.sphinx-doc.org/en/master/usage/quickstart.html

Example: https://flask.palletsprojects.com/en/3.0.x/

Autodoc plugin: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html

**zensical** (formerly mkdocs-material)
(`uv add zensical`)

Quickstart:  https://zensical.org/docs/get-started/

Example: https://docs.pydantic.dev/latest/

You may of course use any other tool your team is familiar with or interested in trying.

### Example Layout of `docs/`

* index.md - front page, short explanation of your project and documentation layout
* architecture.md - introduce core concepts / document architecture
* models.md - model documentation
* endpoints/auth.md 
* endpoints/images.md
    - endpoint documentation grouped by topic
- changelog.md - documentation of major changes for team to reference
- decisions - directory with short write-ups of key technical decisions

Only the sections indicated above in **Requirements** are required.  The others are suggestions of things your team might want to track over time. As a guiding principle: focus on what is helpful to your team now first, and then what might be useful to successors/new members.

If your project has specific needs, consider those too. Example: it uses a poorly-documented 3rd party API, so you wind up writing your own documentation for how your project uses that API as you explore it.