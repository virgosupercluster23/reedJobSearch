import requests
import sqlite3
import os
import json
from reed import ReedClient
from time import sleep

with open(os.getcwd()+"/config.json") as f:
    CONFIG = json.load(f)

DB = os.getcwd() +   '/jobs.db' #assumes script runs from the cwd
ELASTICAPIKEY =      CONFIG['ELASTICAPIKEY']
REEDAPIKEY =         CONFIG['REEDAPIKEY']
EMAILFROM =          CONFIG['EMAILFROM']
EMAILTO =            CONFIG['EMAILTO']
JOBSEARCH =          CONFIG['JOBSEARCH']
WORDFILTER =         [ i.lower() for i in CONFIG['WORDFILTER']   ]
PHRASEFILTER =       [ i.lower() for i in CONFIG['PHRASEFILTER'] ]


#get jobsearch results
client = ReedClient(REEDAPIKEY)
response = client.search(**JOBSEARCH)
targets = ['jobId', 'employerName', 'jobTitle', 'locationName', 'date', 'expirationDate', 'applications', 'jobUrl', 'jobDescription']
results = [{key: item[key] for key in targets if key in item} for item in response]


#populate db with jobsearch results
conn = sqlite3.connect(DB)
conn.execute('''CREATE TABLE IF NOT EXISTS jobs
    (jobId INTEGER, employerName TEXT, jobTitle TEXT, locationName TEXT, date TEXT,
    expirationDate TEXT, applications INTEGER, jobUrl TEXT, jobDescription TEXT, emailed BOOLEAN DEFAULT FALSE)''')
cursor = conn.cursor()
existing_job_ids = set(cursor.execute("SELECT jobId FROM jobs").fetchall())
for job in results:
    cursor.execute(
        '''INSERT INTO jobs
        (jobId, employerName, jobTitle, locationName, date, expirationDate, applications, jobUrl, jobDescription)
        SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?
        WHERE NOT EXISTS (
                SELECT 1 FROM jobs WHERE jobId = ? )''',
        (job['jobId'], job['employerName'], job['jobTitle'], job['locationName'], job['date'],
         job['expirationDate'], job['applications'], job['jobUrl'], job['jobDescription'], job['jobId'])
    )
conn.commit()
conn.close()


#read out jobsearch results
conn = sqlite3.connect(DB)
cursor = conn.cursor()
cursor.execute("SELECT * FROM jobs")
rows = cursor.fetchall()
column_names = [desc[0] for desc in cursor.description]
jobsearch_results = [{column_names[i]: row[i] for i in range(len(column_names))} for row in rows]
cursor.close()
conn.close()


def prettykeys(key):
    ''' unCamelCase keys in function below '''
    import re
    words = re.findall(r'[a-z]+|[A-Z][a-z]*', key)
    title_case = ' '.join(word[0].upper() + word[1:] for word in words)
    return title_case


def generate_html_from_dictionary(dictionaryitem):
    ''' generate email body html, neatly formatted items in a result '''
    html = '''<html><head><style>
            .box {background-color: #f5f5f5; border-radius: 5px; padding: 10px; margin-bottom: 10px;}
            .title {font-weight: bold; margin-bottom: 5px;}
            .info {margin-bottom: 5px;}
        </style></head><body>'''
    for key, value in dictionaryitem.items():
        if key not in ["jobId", "emailed"]:
            key = prettykeys(key)
            html += '''<div class="box"><div class="title">{}</div><div class="info">{}</div></div>'''.format(key, value)
    html += '''</body></html>'''
    return html


def emailer(html_content, jobTitle, employerName):
    ''' sends email via elastic API, with formatted subjectline and htmlbody '''
    url = 'https://api.elasticemail.com/v2/email/send'
    from_address = EMAILFROM
    to_address = EMAILTO
    subject = "REED JOB AD: {} vacancy posted by {}".format(jobTitle, employerName)
    message = html_content
    payload = {'apikey': ELASTICAPIKEY, 'from': from_address, 'to': to_address, 'subject': subject, 'bodyHtml': message}
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print('Email sent successfully.')
    else:
        print('Failed to send email. Error:', response.text)


def emailedTrue(job_id):
    ''' updates db with "sent" emails (reliable sender/receiver platforms) '''
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("UPDATE jobs SET emailed = 1 WHERE jobId = ?", (job_id,))
    conn.commit()
    conn.close()


def logBlockedEmail(i):
    ''' keep a log of "emailed"/filtered jobs '''
    text = str(i['jobId'])+':'+i['jobTitle']+':'+i['jobUrl']+"\n"
    with open("filtered.txt", "a+") as f:
        f.write(text)


def toFilter(jobtitle, jobDescription):
    ''' filters are lowercase, jobtitle is lowercase '''
    if any(keyword in jobtitle.lower() for keyword in WORDFILTER):
        return True
    if any(phrase in jobtitle.lower() for phrase in PHRASEFILTER):
        return True
    if any(phrase in jobDescription.lower() for phrase in PHRASEFILTER):
        return True
    else:
        return False

#for every jobsearch, if not previously emailed, if not filtered, email/update db emailed
for i in jobsearch_results:
    if i['emailed'] == 0:
        if toFilter(i['jobTitle'], i['jobDescription']) == True:
            logBlockedEmail(i)
            emailedTrue(i['jobId'])
        else:
            emailer(generate_html_from_dictionary(i), i['jobTitle'], i['employerName'])
            emailedTrue(i['jobId'])
            sleep(2)
