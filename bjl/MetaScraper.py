import urllib2
import re
import urlparse

from bs4 import BeautifulSoup
import html5lib

is_array = lambda var: isinstance(var, (list, tuple))

class MetaScraper:	
	def loadhtml (self, url):
		response = urllib2.urlopen(url)
		html = response.read()
		return html

	def parse(self, url):
		data = {}

		try:
			html = self.loadhtml(url)
		except:
			data["error"] = "cannot load html from the provided url"
			return data

		# The default python parser is too strict for
		# real-world html - html5lib is much more lenient
		soup = BeautifulSoup(html,"html5lib")

		# OpenGraph has been around longer than Twitter Cards, so we'll start with that
		for og_data in soup.findAll('meta', attrs={"property":re.compile("og(.*)", re.IGNORECASE)}):
			prop = og_data.get('property')[3:]
			ctnt = og_data.get('content')

			if prop in data:
				data[prop].append(ctnt)
			else:
				# We create everything as an array initially
				data[prop] = [ctnt]

		for prop in data:
			# Convert single length arrays to scalars
			if len(data[prop]) == 1:
				data[prop] = data[prop][0] 

		# Now let's fall back onto Twitter Cards - only overwrite, not append
		for twitter_data in soup.findAll('meta', attrs={"name":re.compile("twitter(.*)", re.IGNORECASE)}):
			prop = twitter_data.get('name')[8:]
			ctnt = twitter_data.get('content')

			if prop not in data:
				data[prop] = ctnt


		# Fallback for non or partial opengraph/twittercards sites
		# - again, overwrite only, not append
		if "url" not in data:
			data["url"] = url

		if "title" not in data:
			# First try the title tag
			title = soup.title.contents[0]

			# If that doesn't exist, resort to the first h1
			if len(title) == 0:
				title = soup.h1.contents[0]

			# Sometimes the title could have extraneous data at the end,
			# usually for SEO purposes and starting with a pipe
			if title.find("|") > 0:
				title = title[:title.find("|")]

			data["title"] = title.strip()

		if "description" not in data:
			# The only reliable alternative is to try for a meta description
			meta_desc = soup.find('meta', attrs={"name":re.compile("description", re.IGNORECASE)})
			if meta_desc is not None:
				data["description"] = meta_desc.get('content')		

		if "image" not in data:
			# Some sites use Schema.org itemprop="image"
			image = soup.find(attrs={"itemprop":"image"})
			if image is not None:
				data["image"] = image.get("src") or image.get("href")
			else:
				if soup.h1 is not None:
					# The most reliable image to look for is the first one *after* the first h1
					# as others can be icons or non-related
					image = soup.h1.findNext("img")
				
					if image is not None:
						# TODO: Check image dimensions and fall-over 
						#		if they are too small
						data["image"] = image.get("src")
					else:
						# We look for apple-touch-icons
						image = soup.find("link", attrs = { "rel": "apple-touch-icon" })
						if image is not None:
							data["image"] = image.get("href")

		# Ensure that any relative image urls are converted to absolute
		if "image" in "data":
			if is_array(data["image"]):
				for index, item in enumerate(data["image"]):
					data["image"][index] = urlparse.urljoin(url, item)
			else:
				data["image"] = urlparse.urljoin(url, data["image"])

		# Final tidy up - remove newlines and multiple spaces
		for prop in data:
			if data[prop] is not None:
				data[prop] = re.sub("[\n ]+", " ", data[prop])

		return data