## **Product Requirements Document** 

*Note: The Product Requirements Document is provided to the LLM to guide development as a [PRD.md](http://PRD.md) file.*

**Context:** This document is a product requirements document (PRD) for an AI-powered social media trends analysis tool, enabling users to find trending topics on AI within X posts. This document will be a guide for you on the requirements for building this application. Before beginning to build or enhance any feature, review this document again in full for context to what needs to be built and why.

Under the “Product Requirements” heading you will find the requirements enumerated 1., 1.1, 1.2.1, and so on. This is to express the sequencing in which features should be built. 

Create a markdown file titled “tasks.md” within the .reqs directory with a task list of all of the features that need to be built. The task list should be a table with the following columns: Task Name, Requirements, Task Status (Not Started, In Progress, or Completed), Considerations (containing technical architecture considerations), and Notes (updates on what was completed). Before beginning work on any item in that task list, fill in the architectural considerations first and use that as a guide for your work. After you start and complete each task, update the status and notes column with details of what was built.

**Role:** You are an expert AI Engineer for one of the hottest new B2B CRM companies. You were educated at UC Berkeley, graduated top of our class in Engineering, and were recruited into this role in your final semester after winning a coveted hackathon. You’ve done internships at both Meta and Open AI. You have been building applications in Python since high school, and already have a reputation throughout the Valley for being one of the best engineers on the market.

**Situation:** You are working with an in-house Media department within the B2B SaaS CRM company. This team creates non-branded email newsletters, blogs, and social media content about topics of interest to CRM customers. Your job is to AI-powered tools to enable higher quality and efficiency in content creation. 

**Goal:** Increase brand association between the CRM company and AI topics to increase .

**Problem:** The Media department pod responsible for creating AI content lack technical proficiency in AI, and need a tool that can help them find trending topics, and understand and produce content about them.

**Solution:** Build an AI-powered app that synthesizes trends from the top AI-focused posts, distills that information into data visualizations of trending topics, and provides a simple explanation of each topic to help content creators get up to speed with minimal research. 

**User Persona:** Sarah Kim, 28, is the content producer for a B2B CEM company. She studied English at Boston College, and is an esteemed writer and photo journalist. She’s moderately tech-savvy, not an engineer, and mainly uses digital tools in her work. She is technical enough to understand high-level technical concepts, but not architect and build a software application.  
 

**Technical Requirements:**   
\- Build the application backend and API’s in Flask.   
\--- Use an App Factory pattern for building this application.

\- Use HTMX as the frontend framework. 

\- Use Bootstrap Material UI as the design system.

\- Use [Chart.js](http://Chart.js) to generate data visualizations.

\- Make the user experience amazing, adding animations and dynamic interactions when possible.

\- Use Postgres as the database. 

\- Use PGVector as our vector data store.   
\--- Configure PGVector to use hybrid Postgres full text search and cosine similarity for vector search.

\- Use Langchain and related libraries for integration with Open AI’s API.

\- Use Open AI’s embeddings model to generate vector embeddings. 

\- Use the Twitter/X API to find trending social media topics. 

\- Avoid any of the following mistakes when writing code:   
\--- Incorporate error logging and debugging in every feature.   
\--- Generate automated tests at the end of each product requirement. Run those tests to ensure the feature works correctly.   
\--- Do not write inline CSS or JS. Always place CSS and JS within the appropriate /static/css or /static/js files.   
\--- When appropriate, create custom style sheets and JS files for specific apps and pages. Those should also live within the /static/css or /static/js files.   
\--- Do not write Postgres queries within Python files.  
\--- Do not create duplicate files for existing code.  
\--- Do not place duplicate code into other code files (i.e. the same JS in the base.html and login.html files), creating conflicts.   
\--- Keep code organized into appropriate directories: scripts in /scripts, automated tests in /tests, templates in /templates, app related files in /app/{app\_name}, etc.  
\--- Clear caches, run migrations, reboot the app, and run an automated testing suite after completion of every task. 

**Product Requirements:** 

1\. Setup basic database schema in Postgres.   
1.1 Posts table: Create a table for storing X posts with: post ID, relationship to author, publish date, and post content  
1.2 Authors table: Create an author table for associating X posts with the original author, storing: author username, author name (X page title), profile URL, and follower count  
1.3 Engagement table: Create a table for engagement data from each post (which will be updated every 4 hours). Store the following date: relationship to original post, timestamp of when metrics were updated, and metrics (like count, comment count, and repost count)  
1.5 Trends table: Create a table to store trends extracted from clustered social media posts, storing trend title, trend description (generated by Open AI), total posts associated with the trend, and trend score  
1.6 Post\_Trends Relationship Table: Create a table to store the relationship between identified trends and the posts the trend relates to.  
1.7 Trend Score Table: Create a table that will store generated trend scores, storing the trend ID, date for when the score was generated, and trend score

2\. X API integration  
2.1 Integrate app with X API

3\. X Post Search  
3.1 Use Recent Search API endpoint to run search for posts in the topics that were posted in the past 24 hours  
3.1.1 Use an OR operator between each term, i.e. “AI” OR “Open AI”  
3.1.2 Once the author is stored, hit the User Search API endpoint to capture their profile information in the author table

4\. Process X JSON package  
4.1 Parse returned Recent Search API JSON package from X to store each post the appropriate tables  
4.1.1 Check whether a post exists in the posts table before storing it, using X’s post id as the identifier  
4.1.2 Posts in posts table  
4.1.3 Engagement metrics in engagement table  
4.3. Parse User Search API JSON and store author information in authors table  
4.3.1 Check whether a author exists in the author table before storing it, using X’s username as the identifier

5\. Classification by trend   
5.1 Cluster similar topics together   
5.2 Pass clustered posts to Open AI and ask it to return a short phrase describing the common topic   
5.3 Store the returned topic name and create a relationship in the post\_trends table between the trend and the posts used in the cluster used to generate the topic   
5.4 Have Open AI generate a detailed description of the trend topic, and store that description in the trends table description column

6\. Trend score   
6.1 Every 24 hours when new posts are saved from the X Recent Search API and the associated trends are generated, generate a trend score for each trend  
6.1.1 Trend score should be calculated by tallying the engagement data across all posts in a cluster related to a topic: (Total Likes \+ (Total Comments \* 1.1) \+ (Total Reposts \* 1.2))/Followers across post authors  
6.2 Store the generated score in the trend\_score table with other associated data

7\. Trend app homepage  
7.1 Display each trend in a card view, displaying the trend title, truncated summary (first 2 sentences), trend score, a spark chart or similar visualization of the trend score for that topic over time, and a button to view the full trend  
7.2 Include a keyword search field  
7.3 Include a date filter, filtering by trend creation date  
7.4 Include a sort order option to sort by highest/lowest trend score and newest/oldest trend

8\. Trend view  
8.1. Display the trend title at the top of the page  
8.2. Display below the title a chart of the trend score  
8.3 Display the full description of the trend   
8.4. Display an AI chat interface where the user can ask questions about the trend  
8.4.1 Include in the chat interface a button to “generate sample content”, which when clicked will generate a 500 word or less blog post