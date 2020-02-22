import json
import logging
import time
import os
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class VIRL:
    def __init__(self, virl_username, virl_password, virl_server, alert_time_seconds):
        self.virl_username = virl_username
        self.virl_password = virl_password
        self.url = 'https://' + virl_server
        self.bearer_token = ''
        self.diagnostics = dict()
        self.alert_time_seconds = alert_time_seconds
        self.old_labs_results_list = list()

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
            r_utf = r.content.decode()
            self.diagnostics = json.loads(r_utf)
            return True
        except Exception as e:
            logger.warning(e)
            return False

    def parse_diagnostic_for_old_labs(self):
        logger = logging.getLogger(__name__)
        epoch_time_now = int(time.time())
        results_list = list()
        labs_str = ''
        for k in self.diagnostics['user_roles']['labs_by_user']:
            labs = self.diagnostics['user_roles']['labs_by_user'][k]
            temp_list = list()
            if len(labs) > 0:
                for x in labs:
                    created_seconds = int(self.diagnostics['labs'][x]['created'])
                    seconds = epoch_time_now - created_seconds
                    if seconds > self.alert_time_seconds:
                        temp_list.append(dict(lab=x, uptime=seconds))
                if len(temp_list) > 0:
                    email_add = self.diagnostics['user_list'][k]['fullname']
                    if email_add:
                        temp_dict = dict()
                        temp_dict[email_add] = temp_list
                        results_list.append(temp_dict)
        self.old_labs_results_list = results_list


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
            r_utf = r.content.decode()
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
    while True:
        FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(filename="{0}/{1}.log".format('./', 'VIRL_alert'), level=logging.INFO)
        logger = logging.getLogger(__name__)
        bearer_token = os.environ['ACCESS_TOKEN']
        virl_username = os.environ['VIRL_USERNAME']
        virl_password = os.environ['VIRL_PASSWORD']
        virl_servers = os.environ['SERVER_LIST'].split(',')
        alert_time_seconds = 172800
        for virl_server in virl_servers:
            virl = VIRL(virl_username, virl_password, virl_server, alert_time_seconds)
            virl.get_token()
            virl.get_diagnostics()
            virl.parse_diagnostic_for_old_labs()
            if virl.old_labs_results_list:
                for user in virl.old_labs_results_list:
                    web = WebEx(bearer_token)
                    message = 'Your VIRL labs on server ' + virl_server + ' are over 24 hours old: \n'
                    for k in user:
                        webex_email = k
                        id = web.get_id_from_email(webex_email)
                        for lab in user[webex_email]:
                            delta = time.time() - lab['uptime']  # returns seconds
                            days = int(delta // 86400)
                            hours = int(delta // 3600 % 24)
                            minutes = int(delta // 60 % 60)
                            seconds = int(delta % 60)
                            message += '        ** Lab Id ' + lab['lab'] + ': ' + str(days) + ' days ' + str(
                                hours) + ' hours ' + str(minutes) + ' minutes ' + str(seconds) + ' seconds' + '\n'
                        message += 'Perhaps you would consider using the "VIRL delete lab" command to free server resources.'
                        message += "\nType 'help' to see how I can assist you"
                        web.send_message(message)
                        logging.info('User ' + k + ' : ' + message)
        time.sleep(86400)
