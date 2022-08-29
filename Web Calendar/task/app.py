import datetime
import sys

from flask import Flask
from flask_restful import Api, Resource, reqparse, inputs, fields, marshal_with, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///event.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

api = Api(app)

post_parser = reqparse.RequestParser()
post_parser.add_argument('date', type=inputs.date,
                         help="The event date with the correct format is required! The correct format is YYYY-MM-DD!",
                         required=True)
post_parser.add_argument('event', type=str, help="The event name is required!", required=True)

get_parser = reqparse.RequestParser()
get_parser.add_argument('start_time', type=inputs.date,
                        help="The event date with the correct format is required! The correct format is YYYY-MM-DD!",
                        required=False)
get_parser.add_argument('end_time', type=inputs.date,
                        help="The event date with the correct format is required! The correct format is YYYY-MM-DD!",
                        required=False)

db = SQLAlchemy(app)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String(80), nullable=False)
    date = db.Column(db.Date, nullable=False)


db.create_all()

resource_fields = {"id": fields.Integer,
                   "event": fields.String,
                   "date": fields.String}


class EventResource(Resource):
    @marshal_with(resource_fields)
    def get(self):
        args = get_parser.parse_args()
        if args['start_time'] is None and args['end_time'] is None:
            return Event.query.all()
        return Event.query.filter(Event.date.between(args['start_time'].date(), args['end_time'].date())).all()

    def post(self):
        args = post_parser.parse_args()
        event = Event(event=args['event'], date=args['date'].date())
        db.session.add(event)
        db.session.commit()
        return {"message": "The event has been added!",
                "event": args['event'],
                "date": str(args['date'].date())}


class TodayEventResource(Resource):
    @marshal_with(resource_fields)
    def get(self):
        return Event.query.filter(Event.date == datetime.date.today()).all()


class EventById(Resource):
    @marshal_with(resource_fields)
    def get(self, event_id):
        event = Event.query.filter(Event.id == event_id).first()
        if event is None:
            abort(404, message="The event doesn't exist!")
        return event

    def delete(self, event_id):
        event = Event.query.filter(Event.id == event_id).first()
        if event is None:
            abort(404, message="The event doesn't exist!")
        db.session.delete(event)
        db.session.commit()
        return {"message": "The event has been deleted!"}


api.add_resource(EventResource, '/event', '/')
api.add_resource(TodayEventResource, '/event/today')
api.add_resource(EventById, '/event/<int:event_id>')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
