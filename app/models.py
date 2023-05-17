from datetime import datetime

from . import db

class Video:
	def __init__(self, url, name, path, static_path, res, mime_type, file_size):
		self.url = url
		self.name = name
		self.path = path
		self.static_path = static_path
		self.res = res
		self.mime_type = mime_type
		self.file_size = file_size

	def __repr__(self):
		return """
URL: {}
Name: {}
Path: {}
Static path: {}
Resolution: {}
Mime type: {}
File size: {}
""".format(self.url, self.name, self.path, self.static_path, self.res, self.mime_type, self.file_size)

class Comment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	author = db.Column(db.String(50), nullable=False)
	text = db.Column(db.String(255), nullable=False)
	likes_count = db.Column(db.Integer, default=0)
	date = db.Column(db.DateTime, default=datetime.utcnow)