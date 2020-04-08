# colabot-alert
Alerts VIRL simulation users with labs running over 8 hours via WebEx Teams 

## Deploying locally with docker-compose
### Environment Config
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
