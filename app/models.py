from datetime import datetime

from . import db

class Video:
	def __init__(self, url, raw_url, name, res, mime_type, file_size):
		self.url = url
		self.raw_url = raw_url
		self.name = name
		self.res = res
		self.mime_type = mime_type
		self.file_size = file_size

class Poster:
	def __init__(self, url, mime_type, file_size):
		self.url = url
		self.mime_type = mime_type
		self.file_size = file_size

class Audio:
	def __init__(self, path, mime_type, file_size):
		self.path = path
		self.mime_type = mime_type
		self.file_size = file_size


class AnsweredCommentsId(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	author = db.Column(db.String(50), nullable=False)
	text = db.Column(db.String(255), nullable=False)
	date = db.Column(db.DateTime, default=datetime.utcnow)

	commet_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False, on_delete='CASCADE')
	comment = db.relationship("Comment", back_populates="answered_messages_id")


class Comment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	author = db.Column(db.String(50), nullable=False)
	text = db.Column(db.String(255), nullable=False)
	date = db.Column(db.DateTime, default=datetime.utcnow)
	is_answer = db.Column(db.Boolean, default=False)

	answered_messages_id = db.relationship("AnsweredCommentsId", back_populates="comment")