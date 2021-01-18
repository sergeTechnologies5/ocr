from app import app, db,socketio
from app.models import User, Checkin
from engineio.payload import Payload

Payload.max_decode_packets = 500

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Checkin': Checkin}

if __name__ == '__main__':
    socketio.run(app, debug=True,host='127.0.0.1')