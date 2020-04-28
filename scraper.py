# IMPORTS
import re
import datetime as dt
import requests
import os
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta

# Class to store entry info
class ArchiveEntry():
	def __init__(self, date):
		self.date = date 									# date of the entry, same as the key in parent dictionary
		self.day = (self.date-dt.date(2005, 4, 30)).days 	# days since 2005-4-30, the start of the Collage Journal
		self.links = {} 									# dictionary that stores (title, link) as (key, value) pair
		self.posted = False									# bool to check if the post has been made before
		pass

# Class for the archive of posts with the various methods to fetch and compile images and posts
class Archive():
	# Initialization
	def __init__(self, start_day):
		self.journal_start = start_day 	# class is created with the date of the first post that's archived
		self.dir = {}					# the archive, which stores (date, ArchiveEntry) as (key, value) pair
		self.day = dt.date.today()		# current day
		self.posts = []					# list of twitter posts to make, updated daily
		print(f"Archive intialized on {self.day} with start at {self.journal_start}")
		pass

	# Method to add entry to the archive dictionary, 
	#  returns boolean to indicate whether a new ArchiveEntry was created
	def addEntry(self, date, title, link):
		if date in self.dir:
			self.dir[date].links[title] = link 	# add new (title, link) entry to exsiting ArchiveEntry.links dictionary
			return False
		else:
			new_entry = ArchiveEntry(date)
			new_entry.links[title] = link
			self.dir[date] = new_entry			# add newly created ArchiveEntry to archive
			return True

	# Function that returns the number of months since the the first archive entry
	def nMonth(self):
		return (self.day.year-self.journal_start.year)*12+(self.day.month-self.journal_start.month)

	# Function that returns the number of days since the start of the Collage Journal (2005-4-30)
	def daysSince(self):
		return (self.day-dt.date(2005, 4, 30)).days

	# Method that compiles the initial archive,
	#  ideally only called once, subsequent entries to be added using self.update()
	def compile(self, warnings=False):
		self.day = dt.date.today()													# update date
		y, m = self.journal_start.year, self.journal_start.month
		month_links = []
		# create list of links that refer to the monthly overviews of the Collage Journal website
		for i in range(self.nMonth()):
			month_links.append(f"http://thecollagejournal.blogspot.com/{y}/{m:02d}/")
			m += 1
			if m>12:
				m=1
				y += 1
		# gather links of all posts per month
		for month in month_links:
			soup = BeautifulSoup(requests.get(month).text, 'html.parser')			# grab HTML
			for post in soup.find_all("div", class_="post hentry")[::-1]: 			# individual posts are indicated by the "post hentry" class tag
				title = post.find("h3")												# get post title
				published = post.find("abbr", class_="published")["title"]			# get timestamp from "published" tag
				dates = [int(val) for val in published.split('T')[0].split('-')]	# format date
				date = dt.date(*dates)
				try:
					link = title.a["href"]											# get post link
					self.addEntry(date, title.contents[1].contents[0], link)		# add archive entry for new link
				except:
					if warnings:
						print(f"Warning: entry could not be added on {date}")
					pass
		pass

	# Method to update archive with new posts from the frontpage of the Collage Journal blog
	#  returns list of dates of newly created entries
	def update(self, warnings=False):
		self.day = dt.date.today()																		# update date
		soup = BeautifulSoup(requests.get("http://thecollagejournal.blogspot.com/").text, 'html.parser')# grab HTML
		new_posts = []																					# list of new entries
		# gather links on frontpage
		for post in soup.find_all("div", class_="post hentry"):											# individual posts are indicated by the "post hentry" class tag
			title = post.find("h3")																		# get post title
			published = post.find("abbr", class_="published")["title"]									# get timestamp from "published" tag
			date = dt.date(*[int(val) for val in published.split('T')[0].split('-')])					# format date
			link = title.a["href"]																		# get post link
			if self.addEntry(date, title.contents[1].contents[0], link):								# add archive entry for new link, if link already exist the addEntry method makes no changes
				new_posts.append(date)																	# if new, add to new entries
		return new_posts

	# Method to compile the list of daily twitter posts
	#  gathers all previous posts of the same date
	def compilePosts(self):
		self.posts = []										# empty post list
		date=self.day
		step = (4 if date.month==2 and date.day==29 else 1)	# exception for leap years
		while date>=self.journal_start:
			self.posts.append(date)							# add post
			date = date - relativedelta(years=step)			# move back a year
		pass

	# Function to grab the image link from a given post link (somewhat static due to string checking)
	def imageScrape(self, link):
		soup = BeautifulSoup(requests.get(link).text, 'html.parser')		# grab HTML
		image = soup.find("div", class_="post-body entry-content").a["href"]# get image link
		request = requests.get(image)										# request image
		# check for link tags:
		#  's1600' indicates live image link
		#  's1600-h' indicates irregular embedding
		if 's1600' in image:
			if 's1600-h' in image:
				try: 														# try to access the irregular embedding
					embedded = BeautifulSoup(request.text, 'html.parser')	# grab embedded HTML
					embedded_image = embedded.body.img["src"] 				# get new image link
					image_link = embedded_image
				except:
					image_link = None										# if irregular embedding could not be accessed, return None
			else:
				image_link = image
			return image_link
		else:
			return None														# if dead image link, return None

	# Method to download an image specified by a given (link, date) pair
	#  returns boolean do indicate successful download
	def dlLink(self, link, date):
		image = self.imageScrape(link)				# get image link
		if not image:
			print(f"Image not available: {date}")
			return False							# indicate failure to grab image link
		try:										# try to download scraped link
			path = f"./images/{date}.jpg"			# specify download path
			with open(path, 'wb') as f:
				f.write(requests.get(image).content)# write new image
			return True								# indicate successful download
		except:
			print(f"Download failed: {date}")
			return False							# indicate failed download

	# Generator to sequentially download images, specified by the self.posts list
	#  yields the post text and deletes the downloaded image before the next download
	def genImagePosts(self):
		for date in self.posts:							# iterate over posts
			if date in self.dir:
				entry = self.dir[date]					# get entry of given date, if entry exists
			else:
				yield (None, None)						# yield similar to StopIteration in outer control flow
				continue
			for title in entry.links:					# iterate over (title, link) pairs in the dictionary
				link = entry.links[title]				# get post link
				post_text = f"{date} (Day {entry.day}) visit @ {link}"
				if entry.posted:						# if post has been made before,
					yield (date, "RT: "+post_text)		#  yield with retweet indicator
					continue
				if not self.dlLink(link, date):			# try to download image at link
					continue							#  if download failed, move on to next post
				else:
					yield (date, post_text)				# yield tuple of date and post text and  
					os.remove(f"./images/{date}.jpg")	# delete downloaded image
					yield None							# empty yield to trigger deletion