from bs4 import BeautifulSoup as bsoup
from urllib.request import Request, urlopen
import urllib
import csv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as SIA

#Sentiment analyzer
analyzer = SIA()
base_url = 'http://nfs.sparknotes.com/hamlet/page_%d.html'

class Page:
	def __init__(self, act, scene, soup):
		self.act = act
		self.scene = scene
		self.soup = soup

	def make_scene(self):
		return Scene(self.act, self.scene)

class Line:
	def __init__(self, character, text):
		self.character = character
		self.text = text
		self.length = len(text.split(' '))
		self.polarity_scores = analyzer.polarity_scores(text)

	def __str__(self):
		return '%s (%d): %s' % (self.character, self.length, self.text)

class Scene:
	def __init__(self, act, scene):
		self.act = act
		self.scene = scene
		self.length = 0
		self.characters = {}
		self.lines = []

	def __iadd__(self, line):
		self.lines.append(line)
		self.length += line.length
		character = line.character
		if character in self.characters:
			self.characters[character] += line.length
		else:
			self.characters[character] = line.length
		return self

	def __getitem__(self, key):
		lines = []
		for line in self.lines:
			if line.character == key:
				lines.append(line)
		return lines

	def __repr__(self):
		return '<Scene act=%d, scene=%s>' % (self.act, self.scene)

	def matches(self, page):
		return self.act == page.act and self.scene == page.scene

def get_page(page_num):
	url  = base_url % (page_num)
	try:
		url_request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
		html = urlopen(url_request).read()
		soup = bsoup(html, 'html.parser')
		title = soup.title.string
		nums = [int(s) for s in title.replace(',', '').split() if s.isdigit()]
		act = nums[0]
		scene = nums[1]
		return Page(act, scene, soup)
	except:
		return None

def parse_tag(tag):
	if tag.string:
		return ' '.join(tag.string.split())
	text = ''
	for child in tag.children:
		text += parse_tag(child) + ' '
	return ' '.join(text.split())

def analyze_lines(lines):
	text = ''
	for line in lines:
		text += line.text + ' '
	return analyzer.polarity_scores(text)

def print_lines(lines):
	for line in lines:
		print(line)

curr_scene = Scene(1, 1)
scenes = []
scenes.append(curr_scene)
curr_speakers = []
for i in range(0, 500):
	page = get_page(i)
	if page:
		if not curr_scene.matches(page):
			curr_scene = page.make_scene()
			scenes.append(curr_scene)

		modern_text = page.soup.find_all('td', 'noFear-right')
		for cell in modern_text:
			for child in cell.children:
				name = child.name
				if name == 'b':
					curr_speakers = child.string.split(', ')
					print('\n' + str(curr_speakers))
				elif name == 'div' and 'modern-line' in child['class']:
					print(parse_tag(child))
					for speaker in curr_speakers:
						curr_scene += Line(speaker, parse_tag(child))

main_characters = ['HAMLET', 'CLAUDIUS', 'GERTRUDE', 'OPHELIA', 'LAERTES']

with open('hamlet_sent.csv', 'wt') as f:
	writer =  csv.writer(f, delimiter=',', lineterminator='\n')
	header = ['SCENE'] + main_characters
	writer.writerow(header)
	for scene in scenes:
		curr_row = ['Act %d, Scene %d' % (scene.act, scene.scene)]
		for mc in main_characters:
			curr_row.append(analyze_lines(scene[mc])['compound'])
			if curr_row[-1] == 0:
				curr_row[-1] = None
		writer.writerow(curr_row)
