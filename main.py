import gc
import json
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
        api_path = '/api/v0/authenticate'
        headers = {
            'Content-Type': 'application/json'
        }
        u = self.url + api_path
        body = {'username': self.virl_username, 'password': self.virl_password}
        try:
            r = requests.post(u, headers=headers, data=json.dumps(body), verify=False)
            if r.status_code != 200:
                print('Failed to get token on server ' + virl_server + ' Code: ' + str(r.status_code))
                return False
            else:
                self.bearer_token = json.loads(r.text)
                return True
        except Exception as e:
            print(e)
            return False

    def get_diagnostics(self):
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
                print('Failed to get server diagnostics ' + virl_server + ' Code: ' + str(r.status_code))
                return False
            else:
                r_utf = r.content.decode()
                self.diagnostics = json.loads(r_utf)
                return True
        except Exception as e:
            print(e)
            return False

    def delete_lab(self, lab_id):
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
            print(e)
            return False

    def stop_lab(self, lab_id):
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
            print(e)
            return False

    def wipe_lab(self, lab_id):
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
            print(e)
            return False

    def parse_diagnostic_for_old_labs(self):
        epoch_time_now = int(time.time())
        results_list = list()
        for k in self.diagnostics['user_roles']['labs_by_user']:
            labs = self.diagnostics['user_roles']['labs_by_user'][k]
            temp_list = list()
            if len(labs) > 0:
                for x in labs:
                    nodes = self.diagnostics['labs'][x].get('nodes')
                    running_flag = False
                    max_running = 0
                    for node in nodes:
                        if self.diagnostics['labs'][x]['nodes'][node]['state'] == 'DEFINED_ON_CORE' or \
                                self.diagnostics['labs'][x]['nodes'][node]['state'] == 'STOPPED':
                            pass
                        else:
                            running_flag = True
                            if self.diagnostics['labs'][x]['nodes'][node]['state_times'].get('BOOTED', 0) > max_running:
                                max_running = self.diagnostics['labs'][x]['nodes'][node]['state_times'].get('BOOTED', 0)
                    if running_flag and max_running > self.alert_timer_seconds:
                        created_seconds = int(self.diagnostics['labs'][x]['created'])
                        seconds = epoch_time_now - created_seconds
                        temp_list.append(
                            dict(lab=x, uptime=seconds, created_seconds=created_seconds, max_running=max_running))

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
        uri = 'https://api.ciscospark.com/v1/people?email=' + webex_email
        headers = {
            'Content-Type': 'application/json',
            "Authorization": "Bearer " + self.webex_token
        }
        try:
            r = requests.get(uri, headers=headers)
            if r.status_code != 200:
                print('Failed to connect to WebEx Teams API ' + virl_server + ' Code: ' + str(r.status_code))
                return False
            r_utf = r.content.decode()
            if not json.loads(r_utf)['items']:
                print(
                    'Failed to find user WebEx Teams API ' + webex_email + ' on ' + virl_server + ' Code: ' + str(
                        r.status_code))
                return False
            self.user_id = json.loads(r_utf)['items'][0]['id']
            return True
        except Exception as e:
            print(e)
            return False

    def send_message(self, message):
        uri = 'https://api.ciscospark.com/v1/messages'
        headers = {
            'Content-Type': 'application/json',
            "Authorization": "Bearer " + self.webex_token
        }
        body = {
            "toPersonId": self.user_id,
            "markdown": message,
        }
        try:
            r = requests.post(uri, headers=headers, data=json.dumps(body))
            return True
        except Exception as e:
            print(e)
            return False


if __name__ == '__main__':
    print('Starting....')
    bearer_token = os.environ['ACCESS_TOKEN']
    virl_username = os.environ['VIRL_USERNAME']
    virl_password = os.environ['VIRL_PASSWORD']
    virl_servers = os.environ['SERVER_LIST'].split(',')

    program_loop_hours = float(os.environ['PROGRAM_LOOP_HOURS'])
    alert_timer_hours = float(os.environ['ALERT_TIMER_HOURS'])  # default hours for lab without request for extension

    program_loop_seconds = program_loop_hours * 60 * 60
    alert_timer_seconds = alert_timer_hours * 60 * 60

    while True:
        try:
            for virl_server in virl_servers:
                virl = VIRL(virl_username, virl_password, virl_server, alert_timer_seconds)
                if not virl.get_token():
                    continue
                if not virl.get_diagnostics():
                    continue
                virl.parse_diagnostics_for_all_labs()

                virl.parse_diagnostic_for_old_labs()
                if virl.old_labs_results_list:
                    for user in virl.old_labs_results_list:
                        web = WebEx(bearer_token)
                        message = 'You have running lab(s) on VIRL server ' + virl_server + ' \n'
                        for k in user:
                            webex_email = k
                            if not web.get_id_from_email(webex_email):  # web.user_id
                                continue
                            for lab in user[webex_email]:
                                delta = lab.get('max_running', 0)
                                days = int(delta // 86400)
                                hours = int(delta // 3600 % 24)
                                minutes = int(delta // 60 % 60)
                                seconds = int(delta % 60)
                                if not web.get_id_from_email(webex_email):  # web.user_id
                                    continue
                                message += ' - Lab Id: ' + lab['lab'] + ' Uptime: ' + str(
                                    days) + ' days ' + str(hours) + ' hours ' + str(minutes) + ' minutes ' + str(
                                    seconds) + ' seconds' + '\n'

                            message += '\n\nPlease consider using the ***"VIRL stop lab"*** or '
                            message += '***"VIRL delete lab"*** commands to free server resources. \n\n'
                            message += 'Type "help" to see how I can assist you'
                            web.send_message(message)
                            print('User ' + k + ' : ' + message)
        except Exception as e:
            print('Exception in body')
            print(e)
        gc.collect(generation=2)
        time.sleep(program_loop_seconds)
