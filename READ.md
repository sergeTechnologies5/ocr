
# INSTALLATION

## Steps
1. Navigate to ocr directory by cd command
2. Activate environment by source venv/bin/activate command
3. Install dependancies by pip install -r requirements.txt

### RUNNING APPLICATION
1. python flaskapp.py
2. Configure your android application with the ip you get below
3. ifconfig to get your local ip

###  FILES TO BE UPDATED BEFORE RUNNING

1. flask.py
    1. line 12 put host to your local ip
2. object_detection_yolo.py
    1. line 67 put the ip you specified as your host
3. vehicles.html
    1. line 367 update ip accordingly
4. checkins.html
    1. line 320 update ip accordingly


