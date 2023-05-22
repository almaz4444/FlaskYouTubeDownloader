from datetime import datetime

from flask_login import UserMixin

from . import db

class Video:
	def __init__(self, id, raw_url, name, res, mime_type, file_size, itag, with_audio):
		self.id = id
		self.raw_url = raw_url
		self.name = name
		self.res = res
		self.mime_type = mime_type
		self.file_size = file_size
		self.itag = itag
		self.with_audio = with_audio

		self.res_num = int(self.res.replace('p', '').replace('s', ''))

		if '720' in res:
			self.prefix = 'HD' 
		elif '1080' in res:
			self.prefix = 'Full HD'
		elif '1440' in res:
			self.prefix = '2K'
		elif '2160' in res:
			self.prefix = '4K'

class Poster:
	def __init__(self, mime_type, file_size, url = None, path = None):
		self.url = url
		self.path = path
		self.mime_type = mime_type
		self.file_size = file_size

class Audio:
	def __init__(self, mime_type, file_size):
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
 
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    login = db.Column(db.String(1000), unique=True)