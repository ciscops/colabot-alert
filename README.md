# colabot-alert
Alerts VIRL simulation users with labs running over os.environ['ALERT_TIMER_HOURS'] of hours via WebEx Teams 

## Deployment
#### Local
The alert script requires the below environment variables:
```
ACCESS_TOKEN=[YOUR ACCESS TOKEN]
SERVER_LIST=server1.example.com,server2.example.com,server3.example.com
VIRL_USERNAME=virl
VIRL_PASSWORD=foo
PROGRAM_LOOP_HOURS=12
ALERT_TIMER_HOURS=8  # Hours before owner of lab needs to extend lab time
# note .env is a shell file so there can't be spaces around =
```
Build and run the bot:
```
docker-compose up
```
#### Pipeline
Ideally this repository is linked to the CPN COLABot Jenkins instance, in which a pipeline has been created enabling
automatic deployment when new code is pushed to the repository.

## Operation
This script executes every os.environ['PROGRAM_LOOP_HOURS'] and checks VIRL servers, os.environ['SERVER_LIST'].split(','),
for labs with uptime over os.environ['ALERT_TIMER_HOURS']. If labs are over os.environ['ALERT_TIMER_HOURS'], a 
WebEx Teams message is sent to the user from the WebEx Teams account with token os.environ['ACCESS_TOKEN'].