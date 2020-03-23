import gc
import pymongo
import json
import logging
import time
import os
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class VIRL:
    def __init__(self, virl_username, virl_password, virl_server, alert_timer_seconds):
        self.virl_username = virl_username
        self.virl_password = virl_password
        self.url = 'https://' + virl_server
        self.bearer_token = ''
        self.diagnostics = dict()
        self.alert_timer_seconds = alert_timer_seconds
        self.old_labs_results_list = list()
        self.stop_result = ''
        self.wipe_result = ''
        self.delete_result = ''
        self.all_labs = list()

    def get_token(self):
        logger = logging.getLogger(__name__)
        api_path = '/api/v0/authenticate'
        headers = {
            'Content-Type': 'application/json'
        }
        u = self.url + api_path
        body = {'username': self.virl_username, 'password': self.virl_password}
        try:
            r = requests.post(u, headers=headers, data=json.dumps(body), verify=False)
            if r.status_code != 200:
                logger.warning('Failed to get token on server ' + virl_server + ' Code: ' + str(r.status_code))
                return False
            else:
                self.bearer_token = json.loads(r.text)
                return True
        except Exception as e:
            logger.warning(e)
            return False

    def get_diagnostics(self):
        logger = logging.getLogger(__name__)
        api_path = '/api/v0/diagnostics'
        u = self.url + api_path
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'cache-control': "no-cache",
            "Authorization": "Bearer " + self.bearer_token
        }
        try:
            r = requests.get(u, headers=headers, verify=False)
            if r.status_code != 200:
                logger.warning('Failed to get server diagnostics ' + virl_server + ' Code: ' + str(r.status_code))
                return False
            else:
                r_utf = r.content.decode()
                self.diagnostics = json.loads(r_utf)
                return True
        except Exception as e:
            logger.warning(e)
            return False

    def delete_lab(self, lab_id):
        logger = logging.getLogger(__name__)
        api_path = '/api/v0/labs/' + lab_id
        u = self.url + api_path
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'cache-control': "no-cache",
            "Authorization": "Bearer " + self.bearer_token
        }
        try:
            r = requests.delete(u, headers=headers, verify=False)
            r_utf = r.content.decode()
            self.delete_result = json.loads(r_utf)
            return True
        except Exception as e:
            logger.warning(e)
            return False

    def stop_lab(self, lab_id):
        logger = logging.getLogger(__name__)
        api_path = '/api/v0/labs/' + lab_id + '/stop'
        u = self.url + api_path
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'cache-control': "no-cache",
            "Authorization": "Bearer " + self.bearer_token
        }
        try:
            r = requests.put(u, headers=headers, verify=False)
            r_utf = r.content.decode()
            self.stop_result = json.loads(r_utf)
            return True
        except Exception as e:
            logger.warning(e)
            return False

    def wipe_lab(self, lab_id):
        logger = logging.getLogger(__name__)
        api_path = '/api/v0/labs/' + lab_id + '/wipe'
        u = self.url + api_path
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'cache-control': "no-cache",
            "Authorization": "Bearer " + self.bearer_token
        }
        try:
            r = requests.put(u, headers=headers, verify=False)
            r_utf = r.content.decode()
            self.wipe_result = json.loads(r_utf)
            return True
        except Exception as e:
            logger.warning(e)
            return False

    def parse_diagnostic_for_old_labs(self):
        epoch_time_now = int(time.time())
        results_list = list()
        for k in self.diagnostics['user_roles']['labs_by_user']:
            labs = self.diagnostics['user_roles']['labs_by_user'][k]
            temp_list = list()
            if len(labs) > 0:
                for x in labs:
                    created_seconds = int(self.diagnostics['labs'][x]['created'])
                    seconds = epoch_time_now - created_seconds
                    if seconds > self.alert_timer_seconds:
                        temp_list.append(dict(lab=x, uptime=seconds, created_seconds=created_seconds))
                if len(temp_list) > 0:
                    email_add = self.diagnostics['user_list'][k]['fullname']
                    if email_add:
                        temp_dict = dict()
                        temp_dict[email_add] = temp_list
                        results_list.append(temp_dict)
        self.old_labs_results_list = results_list

    def parse_diagnostics_for_all_labs(self):
        for k in self.diagnostics['user_roles']['labs_by_user']:
            self.all_labs.extend(self.diagnostics['user_roles']['labs_by_user'][k])


class WebEx:
    def __init__(self, webex_token):
        self.webex_token = webex_token
        self.user_id = ''

    def get_id_from_email(self, webex_email):
        logger = logging.getLogger(__name__)
        uri = 'https://api.ciscospark.com/v1/people?email=' + webex_email
        headers = {
            'Content-Type': 'application/json',
            "Authorization": "Bearer " + self.webex_token
        }
        try:
            r = requests.get(uri, headers=headers, verify=False)
            if r.status_code != 200:
                logger.warning('Failed to connect to WebEx Teams API ' + virl_server + ' Code: ' + str(r.status_code))
                return False
            r_utf = r.content.decode()
            if not json.loads(r_utf)['items']:
                logger.warning(
                    'Failed to find user WebEx Teams API ' + webex_email + ' on ' + virl_server + ' Code: ' + str(
                        r.status_code))
                return False
            self.user_id = json.loads(r_utf)['items'][0]['id']
            return True
        except Exception as e:
            logger.warning(e)
            return False

    def send_message(self, message):
        logger = logging.getLogger(__name__)
        uri = 'https://api.ciscospark.com/v1/messages'
        headers = {
            'Content-Type': 'application/json',
            "Authorization": "Bearer " + self.webex_token
        }
        body = {
            "toPersonId": self.user_id,
            "text": message,
        }
        try:
            r = requests.post(uri, headers=headers, data=json.dumps(body), verify=False)
            return True
        except Exception as e:
            logger.warning(e)
            return False


if __name__ == '__main__':
    MONGO_INITDB_ROOT_USERNAME = os.environ['MONGO_INITDB_ROOT_USERNAME']
    MONGO_INITDB_ROOT_PASSWORD = os.environ['MONGO_INITDB_ROOT_PASSWORD']
    MONGO_SERVER = os.environ['MONGO_SERVER']
    MONGO_PORT = os.environ['MONGO_PORT']
    MONGO_DB = os.environ['MONGO_DB']
    MONGO_COLLECTIONS = os.environ['MONGO_COLLECTIONS']
    mongo_url = 'mongodb://' + MONGO_INITDB_ROOT_USERNAME + ':' + MONGO_INITDB_ROOT_PASSWORD + '@' + MONGO_SERVER + ':' + MONGO_PORT

    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT, filename="{0}/{1}.log".format('./', 'VIRL_alert'), level=logging.INFO)
    logger = logging.getLogger(__name__)
    bearer_token = os.environ['ACCESS_TOKEN']
    virl_username = os.environ['VIRL_USERNAME']
    virl_password = os.environ['VIRL_PASSWORD']
    virl_servers = os.environ['SERVER_LIST'].split(',')

    program_loop_hours = float(os.environ['PROGRAM_LOOP_HOURS'])
    alert_timer_hours = float(os.environ['ALERT_TIMER_HOURS'])  # default hours for lab without request for extension
    dead_timer_hours = float(os.environ['DEAD_TIMER_HOURS'])  # hours after alert time until termination without extens

    program_loop_seconds = program_loop_hours * 60 * 60
    alert_timer_seconds = alert_timer_hours * 60 * 60
    dead_timer_seconds = dead_timer_hours * 60 * 60

    while True:
        try:
            epoch_time_now = int(time.time())
            with pymongo.MongoClient(mongo_url) as client:
                db = client[MONGO_DB]
                posts = db[MONGO_COLLECTIONS]

                for virl_server in virl_servers:
                    virl = VIRL(virl_username, virl_password, virl_server, alert_timer_seconds)
                    if not virl.get_token():
                        continue
                    if not virl.get_diagnostics():
                        continue
                    virl.parse_diagnostics_for_all_labs()

                    # Reconcile DB with reality of VIRL server
                    db_per_server_labs = list()
                    for post in posts.find({'server': virl_server}):
                        db_per_server_labs.append(post['lab_id'])
                    for lab in db_per_server_labs:
                        if lab not in virl.all_labs:
                            delete_lab_filter = {'server': virl_server, 'lab_id': lab}
                            print('lab deleted')
                            try:
                                r = posts.delete_many(delete_lab_filter)
                            except Exception as e:
                                print('Could not remove stale records from DB')
                                logger.warning(e)
                                continue

                    # Main process old lab for messaging and possible termination
                    virl.parse_diagnostic_for_old_labs()
                    if virl.old_labs_results_list:
                        for user in virl.old_labs_results_list:
                            web = WebEx(bearer_token)
                            message = 'Your VIRL labs on server ' + virl_server + ' are over {} hours old: \n'.format(
                                alert_timer_hours)
                            for k in user:
                                webex_email = k
                                if not web.get_id_from_email(webex_email):  # web.user_id
                                    continue
                                for lab in user[webex_email]:
                                    delta = epoch_time_now - lab['created_seconds']  # total time since lab was deployed
                                    days = int(delta // 86400)
                                    hours = int(delta // 3600 % 24)
                                    minutes = int(delta // 60 % 60)
                                    seconds = int(delta % 60)

                                    query_lab_filter = {'server': virl_server,
                                                        'user_id': web.user_id,
                                                        'lab_id': lab['lab']}
                                    try:
                                        result = posts.find_one(query_lab_filter)  # Q: Is this lab already in DB?
                                    except Exception as e:
                                        print('Failed to connect to DB')
                                        logger.warning(e)
                                        continue

                                    if result is None:  # A: Nope
                                        query_lab_filter['warning_date'] = epoch_time_now
                                        query_lab_filter['renewal_flag'] = False
                                        try:
                                            post_id = posts.insert_one(query_lab_filter).inserted_id
                                            message += '        ** Lab Id ' + lab['lab'] + ': AGE =' + str(
                                                days) + ' days ' + str(
                                                hours) + ' hours ' + str(minutes) + ' minutes ' + str(
                                                seconds) + ' seconds' + '\n'
                                        except Exception as e:
                                            print('Failed to connect to DB')
                                            logger.warning(e)
                                            continue
                                    elif (alert_timer_seconds > (epoch_time_now - result['warning_date'])) and result[
                                        'renewal_flag'] is True:  # Q: Been renewed and less than alert_time
                                        pass
                                    elif (alert_timer_seconds < (epoch_time_now - result['warning_date'])) and result[
                                        'renewal_flag'] is True:  # Q: Been renewed but now again past alert_time
                                        try:
                                            doc = posts.find_one_and_update(
                                                {'_id': result['_id']},
                                                {'$set': {'warning_date': epoch_time_now, 'renewal_flag': False}
                                                 }
                                            )
                                            result = posts.find_one(query_lab_filter)
                                            message += '        ** Lab Id ' + lab['lab'] + ': AGE =' + str(
                                                days) + ' days ' + str(
                                                hours) + ' hours ' + str(minutes) + ' minutes ' + str(
                                                seconds) + ' seconds' + '\n'
                                        except Exception as e:
                                            print('Failed to connect to DB')
                                            logger.warning(e)
                                            continue
                                    elif dead_timer_seconds > (epoch_time_now - result[
                                        'warning_date']):  # Q: Past alert_time but less than dead time
                                        life_delta = epoch_time_now - result[
                                            'warning_date']  # Time since last warning or update
                                        to_death_delta = dead_timer_seconds - life_delta

                                        dead_days = int(to_death_delta // 86400)
                                        dead_hours = int(to_death_delta // 3600 % 24)
                                        dead_minutes = int(to_death_delta // 60 % 60)
                                        dead_seconds = int(to_death_delta % 60)
                                        message += 'TEST        ** TERMINATION WARNING! Lab Id ' + lab[
                                            'lab'] + ': DEAD IN ' + str(dead_days) + ' days ' + str(
                                            dead_hours) + ' hours ' + str(dead_minutes) + ' minutes ' + str(
                                            dead_seconds) + ' seconds' + '\n'
                                    else:  # These labs are getting terminated
                                        try:
                                            r = posts.delete_one(query_lab_filter)
                                            message += 'IN TEST MODE = NOT REALLY TERMINATED        ** TERMINATED Lab Id ' + \
                                                       lab['lab'] + '\n'
                                            # if virl.stop_lab(lab['lab']):  # This will delete labs from VIRL
                                            #     logger.info('User: ' + user + ' Server: ' + virl_server + ' Lab: ' + lab['lab'] + 'STOPPED')
                                            #     if virl.wipte_lab(lab['lab']):  # This will delete labs from VIRL
                                            #         logger.info('User: ' + user + ' Server: ' + virl_server + ' Lab: ' + lab['lab'] + 'WIPED')
                                            #         if virl.delete_lab(lab['lab']):  # This will delete labs from VIRL
                                            #             logger.info(
                                            #                 'User: ' + user + ' Server: ' + virl_server + ' Lab: ' + lab[
                                            #                     'lab'] + 'TERMINATED')
                                            # else:
                                            #     logger.info(
                                            #         'User: ' + user + ' Server: ' + virl_server + ' Lab: ' + lab[
                                            #             'lab'] + 'ERROR TERMINATING')
                                        except Exception as e:
                                            print('Failed to connect to DB')
                                            logger.warning(e)
                                            continue
                                message += 'TEST Unless already TERMINATED, You can extend the life of your lab. Please message me "@COLABot VIRL extend lab $lab_id"\n            ** Example - "@COLABot VIRL extend lab a1234z"'
                                message += '\n\nPerhaps you would consider using the "VIRL delete lab" command to free server resources.'
                                message += "\nType 'help' to see how I can assist you"
                                web.send_message(message)
                                # print(message)
                                logging.info('User ' + k + ' : ' + message)
            # for post in posts.find():
            #     print(post)
        except Exception as e:
            print('Exception in body')
            logger.warning(e)
        gc.collect(generation=2)
        time.sleep(program_loop_seconds)
