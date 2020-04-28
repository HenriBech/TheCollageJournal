import tweepy as tp
import time
import datetime as dt
from scraper import Archive
from PIL import Image

#CREDENTIALS
consumer_key = "consumer_key"
consumer_secret = "consumer_secret"
access_token = "access_token"
access_secret = "access_secret"

#LOGIN
auth = tp.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tp.API(auth)

delay = 3600

arch = Archive(dt.date(2009, 10, 30))
arch.compile()
arch.compilePosts()
images = arch.compileImages()
while True:
	new_posts = arch.update()
	if new_posts:
		arch.compilePosts()
		images = arch.compileImages()
	else:
	(date, text) = next(images, (None, None))
	if date is None:
		time.sleep(delay)
		continue
	response = api.media_upload(f"./images/{date}.jpg")
	api.update_status(status=text, media_ids=[response.media_id_string])
	next(images)
	time.sleep(delay)