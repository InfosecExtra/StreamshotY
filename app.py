import requests, threading, time, certstream # import stuff

#Static variables
headers = {'Authorization': 'Basic YWRtaW46Y2hhbmdlbWU=',} #for little shot api
littleshot_server = "http://localhost:8888"  #location of littleshot server
ls_max_threads = 1 #for scaling need to fix multi threading
ls_sema = threading.Semaphore(value=ls_max_threads)
ls_threads_list = list()
file_write_lock = threading.Lock()

yara_match_file = "YaraMatches.txt" #list of urls and rule matched

yara_match_file_io = open(yara_match_file, "a")

def writetofile(taskid, domain, yara_match):
    file_write_lock.acquire() # get thread
    debug("Writing to file")
    yara_match_file_io.write(f'{taskid}, {domain}, {yara_match}\n')

    file_write_lock.release() #release thread it

#print debug messages
def debug(message):
    debugmsg = True
    if debugmsg:
        print(message)

debug("Starting everything")

#Talking to little shot
def littleshot_lookup(domain):
    ls_sema.acquire()

    data = {'url': f'https://{domain}'} #url to scan
    debug("Starting request")
    response = requests.post(f'{littleshot_server}/scan', headers=headers, data=data, verify=False)
    time.sleep(30)
    taskid = response.url.split('/')[-1] #returns task id
    debug("Getting results")
    results = requests.get(f'{littleshot_server}/json/results/{taskid}', headers=headers, verify=False) #returns the data on results page
    debug("Checking yara matches")
    if "open_dir" in results.json()['yara_matches']: #only looking at 1 yara rule for ease rn
        debug("it matches yara rule")
        writetofile(taskid, domain, results.json()['yara_matches'])

    ls_sema.release()

#certstream running in loop
def certstream_process(message, context):
    if message['message_type'] == "certificate_update":
        all_domains = message['data']['leaf_cert']['all_domains']

        if len(all_domains) == 0:
            domain = "NULL"
        else:
            domain = all_domains[0]

        if domain != "NULL":
            if "*" not in domain:
                if "office" in domain: #match this word in domains to continue
                    debug(f'got the domain {domain}')
                    thread = threading.Thread(target=littleshot_lookup, args=(domain,)) #send to littleshot as thread.
                    ls_threads_list.append(thread)
                    thread.start()

debug("Starting certstream")
certstream.listen_for_events(certstream_process, url='wss://certstream.calidog.io/')
