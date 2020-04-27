import tweepy as tp
import time
import datetime as dt
from scraper import Archive
from PIL import Image

#CREDENTIALS
#consumer_key = 
#consumer_secret = 
#access_token = 
#access_secret = 

#LOGIN
#auth = tp.OAuthHandler(consumer_key, consumer_secret)
#auth.set_access_token(access_token, access_secret)
#api = tp.API(auth)

arch = Archive(dt.date(2018, 11, 1))
arch.compile()
arch.compilePosts()
images = arch.compileImages()
for (date, text) in images:
	#response = api.media_upload(f"./images/{date}.jpg")
	#api.update_status(status=text, media_ids=response.media_id_string)
	image = Image.open(f"./images/{date}.jpg")
	image.show()
	print(text)
	#time.sleep(3600)
