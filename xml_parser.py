import sys
import xml.sax
from datetime import timedelta, datetime as dt
from collections import defaultdict
import re
import string
import argparse
import os
import logging
import pickle
import time

logging.basicConfig(filename='xml_parser.log', filemode='w', level=logging.INFO)

symbols = re.sub(r'[.]+', '', string.digits + string.punctuation)

example = '''
	usage examples:

	python3 xml_parser.py /home/user/test.xml  -->  shows stats for all days and people
	python3 xml_parser.py /home/user/test.xml -d 22-11-2020  -->  shows stats for 22-11-2020 by all people
	python3 xml_parser.py /home/user/test.xml -d 22-11-2020 29-11-2020  -->  shows stats for date interval by all people
	python3 xml_parser.py /home/user/test.xml -n i.ivanov i.petrov  -->  shows stats for all days by typed persons
	python3 xml_parser.py /home/user/test.xml -d 22-11-2020 29-11-2020 -n i.ivanov  -->  shows stats for date interval by typed persons
	python3 xml_parser.py /home/user/test.xml -d 22-11-2020 -s  -->  shows stats for date without parsing XML
'''


def get_argsparser():
	parser = argparse.ArgumentParser(prog='xml_parser',
									description='Parse XML files',
									epilog=example,
									formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument('Path', metavar='path', help='absolute path to XML file')
	parser.add_argument('-d', '--date', help='filter by date', action='store', nargs='+')
	parser.add_argument('-n', '--name', help='filter by name', action='store', nargs='+')
	parser.add_argument('-s', '--search', help='search info in parsed file without new parsing (for large XML files)', action='store_true')
	return parser.parse_args()


class CustomHandler(xml.sax.handler.ContentHandler):
	def __init__(self):
		self.full_name = ''
		self.result = defaultdict(dict)
		self.time = []

	def startDocument(self):
		self.start_time = time.time()
		print('*** Start parsing XML file ***\n')

	def endDocument(self):
		print(f'*** Finished parsing XML file for {time.time() - self.start_time} seconds ***\n')

	def startElement(self, name, attrs):
		if self._locator.getLineNumber() % 1000 == 0:
			print(f'Processed {self._locator.getLineNumber()} lines of file')
		if name == 'person':
			self.full_name = attrs.get('full_name', '').lower()
			self.full_name = re.sub('[.]+', '.', ''.join(
				[letter for letter in self.full_name if letter not in symbols]))
			if not self.full_name:
				logging.warning(f'Full_name field = {attrs.get("full_name") if attrs.get("full_name") else None}'
						f' does not contain valid information, skipping this XML block')

	def endElement(self, tag):
		if tag == 'person' and self.full_name:
			try:
				if self.time[0].date() == self.time[1].date():
					self.result[self.time[0].date()][self.full_name] = self.time[1]-self.time[0]
				else:
					days = (self.time[1].date() - self.time[0].date()).days
					for i in range(days + 1):
						if i == 0:
							self.result[self.time[0].date() + timedelta(days=i)][self.full_name] = (
								self.time[0].replace(hour=23, minute=59, second=59)-self.time[0])
						elif i == days:
							self.result[self.time[0].date() + timedelta(days=i)][self.full_name] = (
								self.time[1] - self.time[1].replace(hour=0, minute=0, second=0))
						else:
							self.result[self.time[0].date() + timedelta(days=i)][self.full_name] = timedelta(hours=24)
				self.time = []
			except IndexError:
				logging.warning(f'Time block {[str(x) for x in self.time]} does not contain two timestamps, skipping this XML block')
				self.time = []

	def characters(self, content):
		content = content.strip()
		if self.full_name and content:
			content = re.sub(r'[.,:;\/\\_]+', '-', content)
			try:
				self.time.append(dt.strptime(content, '%d-%m-%Y %H-%M-%S'))
			except ValueError:
				logging.warning(f'Datetime object in XML {content} does not match datetime format, skipping this XML block')
				self.time = []
				self.full_name = ''

	def parse(self, filename):
		xml.sax.parse(filename, self)
		return self.result


def get_summary(parsed_data, dates, names):
	if dates and names:
		for date in dates:
			print(f'date: {date.date()}, total_time:'
					f' {sum([parsed_data.get(date.date(), {}).get(x, timedelta(0)) for x in names], timedelta(0))}')
			for name in names:
				print(''.ljust(5) + f'{name}: {parsed_data.get(date.date(), {}).get(name, timedelta(0))}')
			print(50 * '-')
	elif dates:
		for date in dates:
			print(f'date: {date.date()}, total_time: {sum(parsed_data.get(date.date(), {}).values(), timedelta(0))}')
			for person, time in parsed_data.get(date.date(), {}).items():
				print(''.ljust(5) + f'{person}: {time}')
			print(50 * '-')
	elif names:
		for date in parsed_data.keys():
			print(f'date: {date}, total_time: {sum([parsed_data[date].get(x, timedelta(0)) for x in names], timedelta(0))}')
			for name in names:
				print(''.ljust(5) + f'{name}: {parsed_data[date].get(name, timedelta(0))}')
			print(50 * '-')
	else:
		for date, name in parsed_data.items():
			print(f'date: {date}, total_time: {sum(name.values(), timedelta(0))}')
			for person, time in name.items():
				print(''.ljust(5) + f'{person}: {time}')
			print(50 * '-')


def main(args):
	dates, names = [], []
	if args.Path:
		if os.path.exists(args.Path):
			dump_file = (os.path.join(os.path.dirname(os.path.abspath(__file__)),
						'data',
						os.path.basename(args.Path).replace('.xml', '.pkl')))
			if args.search and os.path.exists(dump_file):
				with open(dump_file, 'rb') as f:
					people = pickle.load(f)
			else:
				people = CustomHandler().parse(args.Path)
				with open(dump_file, 'wb') as f:
					pickle.dump(people, f)
		else:
			print('\n*** ERROR: XML file not found, please check path ***')
			logging.error(f'File {args.Path} not found')
			sys.exit(1)
		if args.date:
			if len(args.date) < 3:
				try:
					dates = sorted([dt.strptime(x, '%d-%m-%Y') for x in args.date])
				except ValueError:
					print('\n*** ERROR: Wrong date format (use %d-%m-%Y format), check it and try again ***')
					logging.error(f'Wrong date format in {args.date}')
					sys.exit(2)
				if len(dates) == 2:
					days = (dates[1].date() - dates[0].date()).days
					dates = [dates[0] + timedelta(days=i) for i in range(days + 1)]
			else:
				print('\n*** ERROR: Number of dates should be less than 3 ***')
				logging.error(f'Wrong number of dates {args.date}')
				sys.exit(3)
		if args.name:
			pattern = re.compile(r'[a-zA-Z]{1}\.[a-zA-Z]+')
			names = [x.lower() for x in args.name if re.match(pattern, x) and x == re.match(pattern, x).group()]
			if len(args.name) != len(names):
				print('\n*** ERROR: Wrong name format, check it and try again ***')
				logging.error(f'Wrong name format in {args.name}')
				sys.exit(4)
		get_summary(people, dates=dates, names=names)


if __name__ == '__main__':
	main(get_argsparser())