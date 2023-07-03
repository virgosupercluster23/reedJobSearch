# reedJobSearch
A bot which watches search profiles on reed co uk jobsearch API, filters blocked phrases and emails individual job ads.

I felt that jobsearch websites job alert emails were poor, the search terms themselves return too much spam, the emails can be summaries of e.g. 5 of an indicated 15 jobs, expecting you to click through to the site, the 5 shown can include obvious spam or jobs unrelated to the search term.

So i made a script to remove spam/mismatched results and email individual job ads, so at a glance in the inbox you can see relevant jobs as they are announced on the site, and never need to click through unless you want to apply.

The user creates the folder per search profile, the script remains unedited, the config.json is edited with the search profile, the flitered word/phrase list, and the API keys. The script generates a db and a log file.

The search profile in the config.json is complete for me but the reed jobsearch API shows more options. Any changes there would need to be reflected in the main scripts db code as well as the config.json

I use PythonAnywhere to set multiple search profiles up on task schedules, it currently needs multiple scheduled tasks, although it could be rewritten to bring them all under the one program. I run it hourly, 24/7, this gives me new jobs. It will give you all jobs that are live on first run, after that, new stuff trickles through slowly, especially if you developed the blocked word/phrase list. That can be initiated by looking at the first runs db population (jobTitle/jobDescription), and looking for the jobs you don't like "sales", or "work from home", might be spam among your intended jobs, they tend to be jobs which post spam on all job types.

Elastic email API is easy to set up. Reed Jobsearch API is easy to set up too.
