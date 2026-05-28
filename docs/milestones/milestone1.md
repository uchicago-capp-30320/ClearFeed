# ClearFeed

## List of Team Members
- Grace Kluender
- Yuri Chang
- Ganon Evans
- Khushi Desai 
- Teddy Kolios

## Problem Statement
On social media, users are fed an endless stream of content, and many are concerned with understanding what’s on their feed, who posted it, and why it’s showing up. This ranges from having a seemingly misaligned feed relative to their interests, to having things like hate speech or dog whistles start to crop up in comments or posts. 

## Scenarios / Personas / Stories

**Leon**

Leon is a tech savvy student in his mid-20s who left X because he was frustrated with the changes to the platform after Elon Musk took over. Now, as an active TikTok user, he has noticed an uptick in dog whistles and hate speech in the comments. He gets upset when these hate speech comments are repurposed into memes, which are then circulated by individuals who don’t understand the origin of the slang. For example, the term “noticing” originated as an antisemitic trope, but Leon is upset when people use it as a synonym for “woke.” Leon is not sure what type of engagement in the app attracts these types of comments or posts the most. 

**Yoshi**

Yoshi is an Instagram, Twitter (X), and Youtube user who hates seeing bots that are used to advertise in his feed. Oftentimes, these ads are AI generated and posted by bots who are trying to fit in as real users. He hates this feeling of being deceived. Yoshi would be interested in a tool that would help demarcate ads from user-generated content.  

**Barbara**

Barbara is a middle-aged woman without a lot of experience using social media, however, her kids occasionally send her content, and her online presence has been growing as a result. Barbara mostly just goes along with whatever is immediately shown on her feed, and has been increasingly fed political-related content with occasionally radical opinions in the post/comments. Barbara and her kids are interested in where this content is coming from and/or how to filter it off her profile entirely.

**Jillian**

Jillian is a 30-year-old woman who works in the tech industry and is also an active Instagram reels user. She scrolls at night for news and entertainment, but she often finds herself feeling drained by the content she consumes. Jillian would be interested in better understanding the type of content she is being fed (entertainment vs. politics vs. sports, for example) so that she can adjust her feed to better suit the type of content she would prefer to consume. Because she relies on social media for getting a lot of her news, she is interested in understanding the general political leaning of the content she is being fed, as well as the political leanings of the comments in her feed.  

## Ideation Exercise

To address a common concern that users have about bots and advertisements dominating their feed, we considered building a bot detector application that would analyze a user’s feed. Our initial deterrents for this included the fact that APIs were not scalable to the largescale analysis we wanted to do and often had paywalls. Similarly, outside of somewhere like X, there were limited tools that could reliably detect a bot in the ways we wanted to – it’s easy to see something advertising a cryptocoin in garbled text to be suspicious, but not a random opinion online.

We then started to think more broadly of a “feed analysis dashboard” to demonstrate to someone what sort of topics and contents were coming up in their feed. We thought about additions such as a way to analyze the sort of bias in the posts, for instance. 

Early ideas include a browser extension that actively tracks and scores content in real-time to produce a “feed report card” displayed to users in a Spotify-wrapped style summary of their feed. We looked into user-focused tools on platforms like Bluesky to potentially build an API or filter that automatically adjusts a user’s feed to avoid hate content. 

The idea is to convey the inferred identity the platform has built around you based on your feed. 

## Wireframes

Pipeline Overview (Original Whiteboard Exercise) 

<img width="644" height="341" alt="Screenshot 2026-04-06 at 8 27 21 PM" src="https://github.com/user-attachments/assets/83fdd9a0-721f-4e5f-9310-4fd3de18ca5e" />

ChatGPT Generated Version of Pipeline Overview (for readability) 

<img width="545" height="352" alt="Screenshot 2026-04-06 at 8 28 04 PM" src="https://github.com/user-attachments/assets/a99a723c-3a90-4ddb-9152-11e9021e6359" />

Dashboard Analysis Results Page

<img width="537" height="393" alt="Screenshot 2026-04-06 at 8 28 27 PM" src="https://github.com/user-attachments/assets/9eb61916-7a45-4f18-8eb5-5a600515368d" />

ChatGPT Generated Version of Dashboard Analysis Results page (for readability) 

<img width="889" height="515" alt="Screenshot 2026-04-06 at 10 02 23 PM" src="https://github.com/user-attachments/assets/6113b992-1f42-445d-952b-b22c8871fd6b" />

Onboarding/Landing Page

<img width="591" height="428" alt="Screenshot 2026-04-06 at 8 28 59 PM" src="https://github.com/user-attachments/assets/02b64a1d-9a9f-4840-9e47-df5ef468bc72" />

Feed Analysis (Over Time) Wireframe 

<img width="932" height="607" alt="Screenshot 2026-04-06 at 10 03 19 PM" src="https://github.com/user-attachments/assets/4e4e23af-1db4-4c70-a685-c4a05113beb2" />

ChatGPT Generated Version of Temporal Analysis of the user's feed (for readability)

<img width="930" height="444" alt="Screenshot 2026-04-06 at 10 03 46 PM" src="https://github.com/user-attachments/assets/f66745e3-e76a-4224-83c0-1b7d628d5cae" />

## User Feedback Plan

We will plan to conduct user-feedback interviews over the next week and a half, with the goal of being wrapped up by the end of Week 3. Because of our issue pertaining to social media and the wide breadth of people who use various apps, we will each conduct 2-3 individual interviews among a diverse group of people. A couple of us will try to conduct our interviews in a group session for the sake of increasing idea generation across potential users. 

We will formalize the questions we will be asking users in our next group meeting on Thursday, April 8th, but below are some questions that we have brainstormed:
1. What do you want to come up with on your social media feed? What actually comes up most?
2. Who do you see the most on your social media that isn’t someone you follow or track?
3. What would you do if you knew the accounts or posts most recommended to you?
4. What is your biggest concern about content when using social media? What do you wish you didn’t see?
5. Are there any aspects of your social media usage you intentionally track/control? Do you feel like you have control over your algorithm now?
6. What aspects of your social media usage are you most curious about? 

## Meeting Times

We will meet on Mondays from 3:00 PM to 5:00 PM and Thursday from 9:00 to 11:00 AM. We have Sunday evenings as a backup meeting time as well. James marked Mondays from 4:00 PM to 5:00 PM and Thursday from 9:00 AM to 10:30 AM as potential open office hours. 

## Questions
1. Do you have any tips for vetting pretrained models that we find on HuggingFace, for example?
2. Given that we likely will be integrating numerous different ML models and LLMs into our pipeline, I worry that processing time could become lengthy. Do you have thoughts on how long would be a reasonable processing time for our application from uploading the JSON file to getting the user their results?