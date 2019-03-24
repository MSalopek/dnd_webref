# dnd_webref

Currently, this is just a quick reference guide that I use in my home games that works on desktop and mobile devices.
This is not a replacement for actual game books. 

## This code is a work in progress. Please note that this code is UNSAFE for deployment. 
I have only run it IN A PRIVATE NETWORK. The code is buggy and hacky in places and is by no means SAFE. This was developed quickly and will be refactored in the future. 

### Setting up and running the app sever
1. setup a Python3.6 virtual environment on your machine and activating it
2. navigate to the app folder path_to_folder/dnd_webref/
3. install dependencies: 
```pip install -r requirements.txt```
4. init database using flask: 
```flask init-db```
Since flask is running in dev mode dnd_webref/instance folder is created
5. setup db: 
```python tools run_all --db '.../path_to_db'```
(in dev mode db is in instance folder so path points to .../dnd_webref/instance/data.sqlite)
6. export environment variables:
```export FLASK_APP=app```
``` export FLASK_ENV=development```
7. a) run app in local network:
```flask run --host=0.0.0.0 --port=8080```
-- acces in browser at: (private_ip):8080/reference/
(hostname -I fetches your private ip on linux)

### OR  
7. b) run app on localhost:
 ```flask run --port=8080```
        -- access app at: localhost:8080/reference/

## future work
    1. combat initiative tracker
    2. encounter builder
    3. major refactoring
    4. making the app deployment ready
