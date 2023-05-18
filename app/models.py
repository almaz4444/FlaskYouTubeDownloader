from datetime import datetime

from . import db

class Video:
	def __init__(self, url, name, static_path, res, mime_type, file_size):
		self.url = url
		self.name = name
		self.static_path = static_path
		self.res = res
		self.mime_type = mime_type
		self.file_size = file_size

class Poster:
	def __init__(self, path, mime_type, file_size):
		self.path = path
		self.mime_type = mime_type
		self.file_size = file_size

class Audio:
	def __init__(self, path, mime_type, file_size):
		self.path = path
		self.mime_type = mime_type
		self.file_size = file_size


class Comment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	author = db.Column(db.String(50), nullable=False)
	text = db.Column(db.String(255), nullable=False)
	date = db.Column(db.DateTime, default=datetime.utcnow)
	answer_to_id = db.Column(db.Integer, default=0)