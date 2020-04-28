# IMPORTS
import re
import datetime as dt
import requests
import os
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta

class ArchiveEntry():
	def __init__(self, date):
		self.date = date
		self.day = (self.date-dt.date(2005, 4, 30)).days
		self.links = {}

class Archive():
	#initialization
	def __init__(self, start_day):
		self.journal_start = start_day
		self.dir = {}
		self.day = dt.date.today()
		self.posts = []
		print(f"Archive intialized on {self.day} with start at {self.journal_start}")
		pass

	def addEntry(self, date, title, link):
		if date in self.dir:
			self.dir[date].links[title] = link
			return False
		else:
			new_entry = ArchiveEntry(date)
			new_entry.links[title] = link
			self.dir[date] = new_entry
			return True

	def nMonth(self):
		return (self.day.year-self.journal_start.year)*12+(self.day.month-self.journal_start.month)

	def daysSince(self):
		return (self.day-dt.date(2005, 4, 30)).days

	def dateFromTitle(self, title):
		date = [i for i in title.split() if '/' in i]
		date = date[0].split('/')
		date[2] = re.sub("[^0-9]", "", date[2])
		year = int(date[2] if len(date[2])==4 else "20"+date[2])
		month = int(date[0])
		day = int(date[1])
		return dt.date(year, month, day)

	def compile(self, warnings=False):
		self.day = dt.date.today()
		y, m = self.journal_start.year, self.journal_start.month
		tcj_archive = []
		for i in range(self.nMonth()):
			tcj_archive.append(f"http://thecollagejournal.blogspot.com/{y}/{m:02d}/")
			m += 1
			if m>12:
				m=1
				y += 1
		for month in tcj_archive:
			soup = BeautifulSoup(requests.get(month).text, 'html.parser')
			for post in soup.find_all("div", class_="post hentry")[::-1]:
				title = post.find("h3")
				try:
					date = self.dateFromTitle(title.contents[1].contents[0])
				except:
					if warnings:
						print(f"Warning: unparseable date on {prev_date-dt.timedelta(days=1)}")
					continue
				try:
					link = title.a["href"]
					self.addEntry(date, title.contents[1].contents[0], link)
				except:
					if warnings:
						print(f"Warning: irregular HTML on {date}")
					pass
				prev_date = date
		pass

	def update(self, warnings=False):
		soup = BeautifulSoup(requests.get("http://thecollagejournal.blogspot.com/").text, 'html.parser')
		self.day = dt.date.today()
		new_posts = []
		for post in soup.find_all("div", class_="post hentry"):
				title = post.find("h3")
				try:
					date = self.dateFromTitle(title.contents[1].contents[0])
				except:
					if warnings:
						print(f"Warning: unparseable date")
					continue
				link = title.a["href"]
				if self.addEntry(date, title.contents[1].contents[0], link):
					new_posts.append(date)
		return new_posts

	def compilePosts(self):
		date=self.day
		step = (4 if date.month==2 and date.day==29 else 1)
		while date>=self.journal_start:
			self.posts.append(date)
			date = date - relativedelta(years=step)
		pass

	def imageScrape(self, link): #hacky af
		soup = BeautifulSoup(requests.get(link).text, 'html.parser')
		image = soup.find("div", class_="post-body entry-content").a["href"]
		request = requests.get(image)
		if 's1600-h' in image: #ipretendidonotseeit.jpeg
			try:
				deep_soup = BeautifulSoup(request.text, 'html.parser')
				deep_image = deep_soup.body.img["src"]
				re = deep_image
			except:
				re = image
		else:
			re = image
		return re

	def dlLink(self, link, date):
		try:
			image = self.imageScrape(link)
			if 'show_photo' in image:
				print(f"Image not available: {date}")
				return False
		except:
			print(f"Image could not be saved: {date}")
			return False
		path = f"./images/{date}.jpg"
		with open(path, 'wb') as f:
			f.write(requests.get(image).content)
		return True

	def compileImages(self):
		for date in self.posts:
			entry = self.dir[date]
			for title in entry.links:
				link = entry.links[title]
				if not self.dlLink(link, date):
					continue
				else:
					post_text = f"{date} (Day {entry.day}) visit @ {link}"
					yield (date, post_text)
					os.remove(f"./images/{date}.jpg")
					yield None