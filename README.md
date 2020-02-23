# colabot-alert
Alerts WebEx Teams users with labs running over 48 hours

## Deploying locally with docker-compose
### Environment Config
store your secrets and config variables in here
only invited collaborators will be able to see your .env values
reference these in your code with process.env.SECRET
```
ACCESS_TOKEN=[YOUR ACCESS TOKEN]
SERVER_LIST=server1.example.com,server2.example.com,server3.example.com
VIRL_USERNAME=virl
VIRL_PASSWORD=foo
MONGO_INITDB_ROOT_USERNAME=cisco
MONGO_INITDB_ROOT_PASSWORD=password
MONGO_SERVER=mongodb.example.com
MONGO_PORT=27017
MONGO_PORT=27017
MONGO_DB=myproject
MONGO_COLLECTIONS=documents
# note .env is a shell file so there can't be spaces around =
```
Build and run the bot:
```
docker-compose up
```
