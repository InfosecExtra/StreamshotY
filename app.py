import requests, threading, time, certstream

#Static variables
headers = {'Authorization': 'Basic YWRtaW46Y2hhbmdlbWU=',}
littleshot_server = "http://localhost:8888"
ls_max_threads = 2
ls_sema = threading.Semaphore(value=ls_max_threads)
ls_threads_list = list()
file_write_lock = threading.Lock() #making lock
list_of_domains=[]

yara_match_file = "YaraMatches.txt"

yara_match_file_io = open(yara_match_file, "a")

def writetofile(taskid, domain, yara_match):
    file_write_lock.acquire() #need to lock cant have to threads write to single file at same time
    debug("Writing to file")
    yara_match_file_io.write(f'{taskid}, {domain}, {yara_match}\n')

    file_write_lock.release() #let go after write

#print debug messages
def debug(message):
    debugmsg = True
    if debugmsg:
        print(message)

debug("Starting everything")

def littleshot_lookup(domain):
    ls_sema.acquire() #got thread acquired

    data = {'url': f'https://{domain}'} #url to scan
    debug("Starting request")
    response = requests.post(f'{littleshot_server}/scan', headers=headers, data=data, verify=False)
    time.sleep(10)
    taskid = response.url.split('/')[-1] #returns task id
    debug("Getting results")
    results = requests.get(f'{littleshot_server}/json/results/{taskid}', headers=headers, verify=False) #returns the data on results page
    if results.status_code != 200: # error handling for none 200.
        time.sleep(5)#wait 5 sec
        results = requests.get(f'{littleshot_server}/json/results/{taskid}', headers=headers, verify=False) #retry
    #make sure that block contains yara matches if so skip over print error
    try: # testing this next block with try
        debug("Checking yara matches")
        if "rule" in results.json()['yara_matches']: # found rule match
            debug("it matches yara rule")
            writetofile(taskid, domain, results.json()['yara_matches'])
    except: #if the last block didnt work then except this.
        debug("got an error getting data back")

    ls_sema.release()

def certstream_process(message, context):
    if message['message_type'] == "certificate_update":
        all_domains = message['data']['leaf_cert']['all_domains']

        if len(all_domains) == 0:
            domain = "NULL"
        else:
            domain = all_domains[0]

        if domain != "NULL":
            if "*" not in domain:
                if "office" in domain:
                    debug(f'got the domain {domain}')
                    if domain not in list_of_domains: #check if domain is not in list
                        list_of_domains.append(domain)#add to list so no repeats
                        thread = threading.Thread(target=littleshot_lookup, args=(domain,))#get thread for littleshot
                        ls_threads_list.append(thread)
                        thread.start()

debug("Starting certstream")
certstream.listen_for_events(certstream_process, url='wss://certstream.calidog.io/')
