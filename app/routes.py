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
import pyqrcode

thread = None
thread_lock = Lock()

@app.route('/')
def index():

    users = User.query.all()
    checkins = Checkin.query.all()

    return render_template('index.html', users=users, checkins=checkins)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        return redirect(url_for('index'))
    return render_template('login.html', async_mode=socketio.async_mode)

@app.route('/qr', methods=['POST'])
def qrget():
    data = request.get_json() or {}
    user  = User.query.filter_by(national_id=data['national_id']).first()
    if user :
        return {'name':user.name,'national_id':user.national_id,'number_plate':user.number_plate,'phone_number':user.phone_number,'purpose':user.purpose,'gender':user.gender,'department':user.department}
    else :
        return {'name':''}

@app.route('/user', methods=['POST'])
def user():
    data = request.get_json() or {}
    user  = User.query.filter_by(number_plate=data['number_plate'],national_id=data['national_id']).first()
    if user :
        return {'name':user.name,'national_id':user.national_id,'number_plate':user.number_plate}
    user = User()
    user.number_plate = data['number_plate']
    user.phone_number = data['phone_number']
    user.name = data['name']
    national_id = data['national_id']
    user.national_id = national_id
    user.department = data['department']
    user.gender = data['gender']
    user.purpose = data['purpose']
    user.qr_code_status = 'ok'
    db.session.add(user)
    db.session.commit()
    url = pyqrcode.create(national_id)
    url.svg(national_id+'.svg', scale=8)
    return {'name':user.name}

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
    user.qr_code_status='null'
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
    return {"data" :"response"}

@app.route('/qr', methods=['POST'])
def generateqr():
    data = request.get_json() or {}
    national_id = data['national_id']
    url = pyqrcode.create(national_id)
    url.svg(national_id+'.svg', scale=8)

def background_thread():
    main()

@socketio.on('my_event', namespace='/test')
def test_message(message):
    print(message)
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})

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

