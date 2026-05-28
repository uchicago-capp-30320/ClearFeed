# Clearfeed Work Plan

## Q1: How is your team going to communicate? 

Our team will do a daily check-in via Slack. If a team member doesn’t have an update one day, just note what you plan to do next and when. We will use GitHub for project management and tracking issues. We explored using Jira, but found that GitHub's project management tools fit our project too and reduced the number of alternative platforms we needed. We’ve scheduled our in-person meeting times with James and have been emailing regularly. We will reach out and email Praveen and invite him to our meetings too. 

## Q2: How is your team going to coordinate & plan?

At our recurring group meetings, our team will delegate tasks for the week and determine reasonable internal deadlines for each. To track these tasks and issues on our project, we will utilize GitHub Projects & Issues. We have begun using this Issue Tracker – see below:  

<img width="1273" height="442" alt="image" src="https://github.com/user-attachments/assets/b8dbb79b-28f0-4051-874b-77fb0e6baf45" />

How we intend to utilize GitHub Projects:

1. All PRs should be linked to the issue associated with the task.

2. When an individual completes their task/issue, they should close out the issue and add a comment with details on what changes were made and what documentation was referenced to complete the task. 

3. If multiple team members are assigned to a task, each member should leave a comment in the comment section of the issue when they have completed their portion of the issue. If you are the last team member to complete their portion of the issue, leave a comment with the details of what you did, and close the issue. 

4. All issues should be completed by their target date. If delays are encountered, those delays should be communicated with the team, and first with team members who may be blocked by the issue not being completed on time.  


## Q3: How are decisions going to be made on your team?

Generally, the individual tasked with a certain responsibility will be responsible for coming up with a solution/process for completing that task. The most agency over decision making should be given to the individual tasked with that part of the project. That said, most decisions should be run by the team. See below for the breakdown of our decisionmaking.

What requires consensus:

- Languages used 

- Tools used to manage project/issues 

- The goal will be that our team discusses at our meetings what each of us are responsible for doing over the next week, which means there should be a general consensus on what that process will look like. If, once a team member starts working on the task and realizes a better process might exist, they should throw it in the Slack chat for group approval  

- If a task only impacts the backend or the frontend, consensus within the backend team and frontend team is enough.  

What roles correspond to what kind of decisions:

- Backend developers have ownership to make major decisions regarding backend 

- Frontend developers have ownership over frontend 

- Agreement assumed within each of those groups on major decisions affecting the entire project’s pipeline  

How will disagreements be handled? 

- We will aim to discuss the disagreements first. It should be expected that both sides of the argument fully consider the alternative approach being proposed. If after discussion/debate, no consensus has been reached, we will reach out to James or Praveen to get guidance on which approach seems better. 

- If there still is not clear consensus, we will do a group vote. 

## Q4: git branching

### Git Workflow and Branching Strategy 

### Overview Of Git Workflow Strategy 

Our project implements the Git Flow branching model to support development with a clear separation between ongoing development, preparations for releases, production-ready code, and emergency production fixes. 

The model includes two long-lived branches: 

- `main` — represents stable, production-ready code. 
 
- `develop` — represents the integration branch for completed features. 
 
The other branches involved in the workflow are temporary: feature/*, release/*, and hotfix/*. 

Together, these branches support structured development, controlled releases, and production stability across Development, Staging, and Production environments. 

### When And How Each Branch Should Be Used 

### main 

Purpose: 

- Represents production-ready code 

- Must always be stable and deployable 

Rules: 

- No direct commits allowed 

- The main branch is updated only through: 

- release/* branches 

- hotfix/* branches 

Environment: Production 

### develop 

Purpose: 

- Integration branch for completed features 

- Pulls together feature work before getting ready for a release 

Rules: 

- No direct commits allowed 

Updated only through: 

- feature/* branches 

- Merges from release/* 

- Merges from hotfix/* 

Environment: Development 

### feature/* 

Purpose: 

- Used for developing new features 

- A new feature branch should be created for each issue; after the issue/tasks is completed and the PR is merged into main, the branch should be deleted by the branch owner 

    - Branches should be named so to be descriptive of what was done in the branch: 

        - EX: feature_integrate_db_with_zeeschuimer 

        - EX: bug_fix_missing_button 

Lifecycle: 

1. Branch from develop 

2. Implement feature 

3. Open pull request into develop 

4. Merge after review 

5. Delete branch 

Environment: Development (before dev integration) 

### release/* 

Purpose: 

- Used to prepare a production release 

- A space to clean up documents, make version bumps, fix minor bugs, and make adjustments to configurations. Importantly, this is not a place to add new features! 

Lifecycle: 

1. Branch from develop 

2. Apply release-related changes 

3. Merge into main 

4. Merge back into develop 

5. Delete branch 

Environment: Staging (before prod integration) 

### hotfix/* 

Purpose: 

- Used for urgent production fixes 

Lifecycle: 

1. Branch from main 

2. Implement fix 

3. Merge into main 

4. Merge into develop 

5. Delete branch 

### Environment: Production 

How Branches Interact With Each Other 

Below is a graph that visualizes the interactions between branch types: 

<img width="268" height="133" alt="Screenshot 2026-04-10 at 7 33 02 PM" src="https://github.com/user-attachments/assets/8854f6a7-cda7-4d74-9e87-f329cce9e8a9" />

 
### Key Interaction Rules: 

- Features must always merge into develop first 

- Production releases must go through a release/* branch 

- Emergency fixes originate from main (they happen in production!) 

- All production changes must be merged back into develop to ensure consistency 

- Temporary branches are deleted after successful merges 

- This workflow ensures production stability, traceable history, controlled release cycles, and a clear separation of responsibilities.  

### Branch Protection Rules 

To prevent accidental production changes, we will configure branch protection rules for main and develop. 

Because the main branch represents production-ready code, it is important that there are strict controls on it. Therefore, we configured rules to ensure that direct pushes to main are disabled, and all changes must be introduced through pull requests. Additionally, we disabled force pushes and branch deletion to make sure commit histories are preserved. Finally, we require at least one approval before merging.  

We also configured rules for the develop branch. We disabled direct pushes, and require pull requests for all merges. We also disabled force pushes and branch deletion. Unlike main, we do not require approval before merging.  

## Q5: Continuity

If a team member will be unavailable for an extended period of time, we will need to convene for a group meeting where we re-delegate that individual’s tasks across team members. This might mean members on the backend team would work on frontend tasks, and vice versa. If we feel that the amount of additional work is infeasible, we will reach out to James to discuss potential deadline changes, or to see if he has capacity to assist in any way.  

If possible before their absence, the missing teammate should provide all of their most recent code and ensure their codebase is up-to-date so other teammates can immediately start working on it. 

If possible, the team member who is unavailable will try to be accessible on Slack to answer questions.

We are a small team, and we all recognize that our final quarter is a busy between job applications and other classes. However, we want to prioritize communication and responsibility to ensure that the next six weeks are productive and that parts of the project are not left behind. 

## Q6: Generative AI

DO’s 

- Understanding code such as Zeeschuimer with a large codebase that we are integrating into our workflow 

- Debugging – understanding error messages, but any suggestions from AI should be vetted 

- Using it to make our wireframes more visually appealing/readable 

Must be able to understand all code that you commit, and to be able to explain it. If GenAI is used to assist in any coding, that must be cited in the issue tracker and references to documentation that confirm proper coding practices should be included. 

DONT’s 

- Claude Code or other autonomous coding agents that work inside our codebase 

- No AI-generated imagery, logos, or other visual aspects in the front-end. 

- Code that is fully generated by AI.  

We understand the value of using AI as a tool to help us understand code, but we want to be considerate of the fact that we are working with sensitive data. We want to avoid giving any sort of free control over that code to an AI.

## Q7: Values & Ethics

Ethical Considerations: 

1. The data collected by Zeeschuimer is personal feed data, which inherently makes it sensitive. We will need to ensure secure data privacy practices. For example, team members should not access the database with the goal of snooping on user’s social media feeds. We will integrate anonymity, but this will be especially important during the testing phase before this is integrated. 

2. We will consider filters or other professional handling of explicit content in someone’s feed such as pornography. When we present this tool, we can maybe present an option or give a warning to make users aware of their summary. 

3. Similarly, if we develop a way to flag extremism or dogwhistles on someone’s feed, we’ll have to ensure accuracy in the identification and consider the present to not make slurs or harmful language appear on the dashboard. 

Values: 

1. As team members, we value transparency. We want team members to feel comfortable sharing their thoughts and opinions on how team dynamics and development of the tool is working for them.  

2. As team members, we value strong communication skills. We understand that a project of this scope in such a short timeline requires consistent and clear communication.  

3. As team members, we value reliability. It is important that team members are committed to meeting their deadlines, as long as they are feasible and no extenuating circumstances arise. That is why it is important that all team members are involved in the assignment of internal deadlines, especially when the task is theirs to complete. 

4. As software developers, we value transparency in explaining to users how their data is used and analyzed. We want users to feel that their privacy is maintained, such that they feel comfortable scrolling, and feel assured that this analysis is for them, and only them. 

## Q8: Team Roles

Group Roles 

- Ganon: Front-end/UI UX Engineer, Database Research (secondary role) 

- Grace: Project Manager, Backend Developer (secondary role) 

- Khushi: Front-end/UI UX Engineer, ML/Data Engineering (secondary role) 

- Teddy: QA Engineer, Backend Developer/Machine Learning (secondary role) 

- Yuri: Data Engineering, Machine Learning (secondary role) 

Our team can be divided into two general groups: Yuri, Teddy, and Grace on the backend then Ganon and Khushi on the frontend. Given our small team size, we expect a lot of collaboration across the different functions of these two parts of our project. For instance, both Ganon and Khushi have experience in graphic design and will work together to create the user's dashboard.

Grace: 

- Project Management: 25% 

- Backend Development & Data Engineering: 50% 

- Feature/Final Product Ideation: 25% 

Teddy: 

- QA Engineer: 25% 

- Backend Development & Data Engineering: 50% 

- Project Management: 15% 

- Machine Learning: 10% 

Yuri: 

- Data Engineering: 40% 

- Backend Developer: 20% 

- Project Management: 25% 

- Machine Learning: 15% 

Ganon: 

- Front-End Engineer: 50% 

- UI/UX Design and User Research: 20%

- Data Engineering: 30% 

- Good Vibes: 1% 

Khushi: 

- Front-End Engineer: 50%

- UI/UX Design and User Research: 20%

- Machine Learning: 30%

## Q9: Internal Milestones

1. Integrate Zeeschuimer into PostgreSQL database (decide on database) 

    - Build database schemas and tables in PostgreSQL (through Django) 

    - Modify forked Zeeschuimer extension code to send data to PostgreSQL 

2. Conduct user research and finalize dashboard options 

    - We have an interview questionnaire created, but need to run it by our team and then start administering it. Our goal is to interview 20 people. 

3. Finalize which HuggingFace models will be used in our analysis, and pipe outputted data into PostgreSQL database (formatted for frontend use) 

4. Develop onboarding page for frontend 

    - Integrate redirects to Zeeschuimer extension and back to the site for analysis results 

    - Integrate log-in procedures between front-end and backend 

    - Pinpoint how most clearly and easily users can upload files and establish trust in using the extension 

5. Finalize working beta version of application (functional visualizations of analysis on real Zeeschuimer data)

Generally, the initial steps in the front-end and back-end processes will be developed in tandem; that is, Steps 1 and 3 will be worked on concurrently as steps 2 and 4, with time given to connect the two parts of the project or delegate members.

## Q10: Architecture/Dependencies Under Consideration

The goal is to build a traditional web application whose webpage is built in Django or Vue. In the front end, the website asks users to authorize and use the adjusted Zeeschuimer extension. In the back end, Zeeschuimer sends the user’s scrolling data to the PostgresSQL database through a data pipeline. Once there, a local model such as HuggingFace is used to categorize posts so that classified summary statistics of the scrolling data can be back to the database. Over time, we have considered whether the user’s previous summary statistics may also feed into the model. Depending on the output of HuggingFace, we may use Polars to calculate the statistics, such as percentage of a certain topic over all posts read. After this process, the user will engage with a dashboard of the summary statistics, ranging from basic categorizations to flagging accounts  posting extremist content. 

## Questions

1. We were trying to set-up our management in Github and ran into a paywall when trying to create protected branch rules on the repository. It says we need to upgrade to a GitHub Team or Enterprise account. Do we have a budget for this or there an alternative you recommend? 