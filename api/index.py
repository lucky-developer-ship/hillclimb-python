import os

os.environ["VERCEL"] = "1"

from server.app import app

handler = app
