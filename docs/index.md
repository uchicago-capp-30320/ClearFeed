# ClearFeed

Social media platforms send users an endless stream of content determined by algorithms with unknown weights and functions. People scroll through hundreds of posts daily without understand the big picture of what is being recommended to them and whether this actually aligns with their interests.

ClearFeed is a tool designed to give users a simple summary of who and what is showing up in their scrolling. The project begins as a modification of [Zeeschuimer](https://github.com/digitalmethodsinitiative/zeeschuimer), a browser extension that collects data from various online social media web interfaces. Using this tool, ClearFeed takes the metadata from posts and uses a local LLM to summarize content genres, common users, and analyze sentiment.

## Documentation Layout

* decisions/ - Specific stylistic or operational choices on content
* endpoints/ - All pages and endpoints of where data and requests are being sent across the project
* milestones/ - Originally written milestones for evaluation of this project in CAPP's Software Engineering for Civic Tech course.
* testing/ - Presenting endpoints and functionalities for full end-to-end testing of the project
* architecture.md - Overview of the technical layout of the project
* index.md - This page, an overview of the documentation
* Model_Resource_Documentation.md - Definitions for all data types used in Clearfeed's API from data collection to analysis
* models.md - Methodology and brief description of LLM models used to produce analysis