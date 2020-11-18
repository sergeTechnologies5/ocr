from flask import render_template, flash, redirect, url_for,session,copy_current_request_context,request
from app import app, socketio,db
from app.forms import LoginForm
from app.models import User, Checkin
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from threading import Lock
from datetime import datetime
from  app.cv.object_detection_yolo import main
from base64 import b64encode
import requests
from requests.auth import HTTPBasicAuth
import json
import datetime as dt
thread = None
thread_lock = Lock()

@app.route('/')
def index():
    
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        return redirect(url_for('index'))
    return render_template('login.html', async_mode=socketio.async_mode)

@app.route('/user', methods=['POST'])
def user():
    data = request.get_json() or {}
    user  = User.query.filter_by(number_plate=data['number_plate']).first()
    if user :
        return {'name':user.name,'national_id':user.national_id,'number_plate':user.number_plate}
    user = User()
    user.number_plate = data['number_plate']
    db.session.add(user)
    db.session.commit()
    return {'name':'null'}

@app.route('/noplate', methods=['POST'])
def noplate():
    data = request.get_json() or {}
    user  = User.query.filter_by(number_plate=data['number_plate']).first()
    if user:
        user.national_id = data['national_id']
        user.name = data['name']
        user.phone_number = data['phone_number']
        db.session.commit()
        return {'name':user.name}
    return {'name':'null'}
@app.route('/checkin', methods=['POST'])
def checkin():
    data = request.get_json() or {}
    user  = User.query.filter_by(number_plate=data['number_plate']).first()
    if user :
        checkin = Checkin.query.filter_by(number_plate=data['number_plate']).first()
        if checkin :
            if checkin.checkin_status == 'in':
                checkin.checkin_status = 'out' 
            else:
                checkin.checkin_status = 'in' 
            db.session.commit()
            return {'checkin': checkin.checkin_status}
        
        checkin = Checkin(vehicle =user)
        checkin.number_plate = data['number_plate']
        checkin.checkin_status = 'in'
        db.session.add(checkin)
        db.session.commit()
        return {'check':checkin.checkin_status}
    user = User()
    user.number_plate = data['number_plate']
    db.session.add(user)
    db.session.commit()
    return {'check':'null'}

@app.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json() or {}
    checkin = Checkin.query.filter_by(number_plate=data['number_plate']).first()
    if checkin :
        checkin.timestamp_check_out = datetime.now()
        db.session.commit()
        return {'check_in' :checkin.timestamp,'check_out' :checkin.timestamp_check_out}
    return {'check':'null'}

@app.route('/pay', methods=['POST'])
def pay():
    data = request.get_json() or {}
    consumer_key = "jJMVK098pTNas1GdmiEUGwVARaI5zOs3"
    consumer_secret = "LMmzbd6qzELQfR5f"
    api_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    access_token = json.loads(r.text)["access_token"]
    print(r.json)
    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = { "Authorization": "Bearer %s" % access_token }
    timestamp = str(dt.datetime.now()).split(".")[0].replace("-", "").replace(" ", "").replace(":", "")
    business_short_code = "174379"
    pass_key = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
    password = "{}{}{}".format(business_short_code,pass_key,str(timestamp))
    data_bytes = password.encode("utf-8")
    #password encoding base64 
    password = b64encode(data_bytes)
    # hustle to change password and timestamp
    password = password.decode("utf-8")
    req = {
        "BusinessShortCode": business_short_code,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": data['amount'],
        "PartyA": "254708374149",
        "PartyB": "174379",
        "PhoneNumber": data['phonumber'],
        "CallBackURL": "https://e07f93d4.ngrok.io/pesa/b2c/v1",
        "AccountReference": "account",
        "TransactionDesc": "test" ,
    }
    response = requests.post(api_url, json = req, headers=headers)
    return {"data" :"response"}

def background_thread():
    main()

@socketio.on('my_event', namespace='/test')
def test_message(message):
    print(message)
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('my_broadcast_event', namespace='/test')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('join', namespace='/test')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('leave', namespace='/test')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close_room', namespace='/test')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         room=message['room'])
    close_room(message['room'])


@socketio.on('my_room_event', namespace='/test')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         room=message['room'])


@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been
    # received and it is safe to disconnect
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)


@socketio.on('my_ping', namespace='/test')
def ping_pong():
    emit('my_pong')


@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)

