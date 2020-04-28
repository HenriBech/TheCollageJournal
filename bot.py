# IMPORTS
import tweepy as tp
import time
import datetime as dt
from scraper import Archive
from PIL import Image

# TWITTER API CREDENTIALS (do not commit to GitHub!)
consumer_key = "consumer_key"
consumer_secret = "consumer_secret"
access_token = "access_token"
access_secret = "access_secret"

# TWITTER LOGIN
auth = tp.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tp.API(auth)

delay = 3600 													# delay (in s) before next post

# INITIALIZATION
arch = Archive(dt.date(2009, 11, 1))							# initialize archive
arch.compile()													# compile initial archive
arch.compilePosts()												# compile initial batch of posts
images = arch.genImagePosts()									# create generator object to generate posts

# BOT LOOP
while True:
	new_posts = arch.update()									# check for new posts
	if new_posts:
		arch.compilePosts()										# compile new posting list
		images = arch.genImagePosts()							# restart post generator
	(date, caption) = next(images, (None, None))				# generate post; at StopIteration, the generator yields None
	if date is None:											#  in this case the loop will wait and skip posting until new posts are created
		time.sleep(delay)
		continue
	elif caption.startswith("RT: "):							# check for retweet indicator
		search = f"\"{date}\" (from:collage_journal) filter:links"
		search_results = api.search(search, result_type=recent)	# if post has been made before, twitter search for the respective post
		n = len(search_results)									# number of posts for that date
		for result in search_result:
			if not result.retweeted:
				api.rt(result)									# retweet found posts which are not retweets
				time.sleep(int(delay/n))						# wait shortened s/t all RTs of the same day occur within the usual delay
		continue
	image = Image.open(f"./images/{date}.jpg")
	image.show()
	print(caption)
	try:														# try to post the downloaded image with the generated caption to twitter
		response = api.media_upload(f"./images/{date}.jpg")		# upload media
		api.update_status(status=caption, media_ids=[response.media_id_string])
		arch.dir[date].posted = True							# indicate that the entry has now been posted
	except:
		print(f"Warning: failed to post to twitter at {dt.datetime.now()}")
	next(images)												# control flow call to trigger the deletion of the downloaded image
	time.sleep(delay)											# wait