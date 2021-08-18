# littleshot
webpage screenshot and metadata capture webapp

idea for this came from urlquery.net (it no longer exists) and urlscan.io. i wanted to be ablet to screenshot pages and get some metadata surrounding the requests. i also wanted to be able to search for things in the dataset. urlscan is great and this isn't exactly replacing it. Urlscan can ID phishing pages, has great searching features, and provides threat intel. If you don't want to be limited by api, need to be able to search metadata, or just take screenshots, this project should work.

check more branches here: https://github.com/BoredHackerBlog/littleshot/branches

# Use case
- screenshot url's
- searchable dataset of requests and responses and metadata surrounding the requests
- modular so you can add other features

# Technologies
- Docker - https://www.docker.com/
- Python - https://www.python.org/
- Flask - https://flask.palletsprojects.com/en/1.1.x/
- Mongodb - https://www.mongodb.com/
- Mongoexpress - https://github.com/mongo-express/mongo-express
- Redis - https://redis.io/
- Python-rq - https://python-rq.org/
- RQ Dashboard - https://github.com/Parallels/rq-dashboard
- Minio - https://min.io/
- Caddy - https://caddyserver.com/
- Yara - https://virustotal.github.io/yara/

# Design
- Caddy works as a reverse proxy for app and minio
- app is the webui that lets you scan sites and search data
- minio hosts images
- mongodb stores metadata
- worker gets scan tasks and does the screenshot and metadata capture parts and uploads screenshot to minio and metadata to mongodb

scan workflow: you click scan, you submit your url, there is a task added, worker gets the task and performs the work, worker sends output to minio and mongodb, you finally see results on results page.

# Running the project
## requirements
- Docker - easy way to install: https://get.docker.com/
- Docker-compose - https://docs.docker.com/compose/install/

please review docker-compose file and code before running.

```
git clone https://github.com/BoredHackerBlog/littleshot
cd littleshot
docker-compose up --build -d caddy
```

installing everything on ubuntu 20.04 (the steps can change in the future, read the official docs)
```
sudo apt update
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
git clone https://github.com/BoredHackerBlog/littleshot
cd littleshot
docker-compose up --build -d caddy
```

# Usage
Visit http://your_docker_host_ip:8888/

- Index page - shows links and most recent 10 scans
- Scan page - takes in a url, make sure http:// or https:// is provided
- Search page - lets you search. string search should work fine. field equal to and not equal to search can be done as well.

using with python:

```
import requests
headers = {'Authorization': 'Basic YWRtaW46Y2hhbmdlbWU=',} #base64 of username:password
data = {'url': 'https://www.google.com'} #url to scan
# data = { 'url': 'https://www.eff.org', 'private': 'on'}  # use this for private scans
response = requests.post('http://SERVER:8888/scan', headers=headers, data=data, verify=False)
taskid = response.url.split('/')[-1] #returns task id
results = requests.get(f'http://SERVER:8888/json/results/{taskid}', headers=headers, verify=False) #returns the data on results page
print(results.json().keys())
content = requests.get(f'http://SERVER:8888/json/content/{taskid}', headers=headers, verify=False) #returns html body that's on the content page
print(content.json().keys())
```

To run multiple workers, edit the docker-compose and add replicas like shown below:

```
    worker:
        build: ./worker
        deploy:
          replicas: 2 # number of workers
```

# Modifying the project
- to perform additional tasks with data collected or do additional things, edit worker.py
- if your addition produces data then store it in mongodb, just add `data['yourfield'] = yorudata` to worker.py
- to render/view your data, edit results.html and just add taskinfo.yourfield. it's jinja template.

since docker-compose is being used, you can just rebuild and deploy containers when you make your modifications.

# Warning
Read through the docker-compose file comments and comments in the code. Be sure to change default passwords as well. Be careful with where/how you host this project and who has access to use it. By screenshotting other sites, you could be revealing your IP. In addition to that, there may be some injection vulns with how queries to mongodb are done. (feel free to use this app as a target for your next CTF)

# screenshots
Check the screenshots folder for more screenshots

![Index page](/screenshots/index.png)
![Results](/screenshots/results1.png)
