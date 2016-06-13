import datetime
import os
import re
import sys

import requests

import pandas as pd

from bs4 import BeautifulSoup
from io import StringIO

import scraper

def generate_metadata_destinations():
	destinations = []
	for i in range(0, 39):
		baseURL = 'http://quote.jpx.co.jp/jpx/template/qsearch.exe?F=tmp%2Fe_stock_list&KEY1=&KEY5=&shijyo0=1stSec&shijyo1=2ndSec&shijyo2=Mothers&shijyo8=JQ%2CJQStandard%2CJQStandardF%2CJQGrowth%2CJQGrowthF&shijyo3=1stF&shijyo4=2ndSecF&shijyo5=MothersF&shijyo6=E%2CFE%2CCE&shijyo9=EN&shijyo7=R&shijyo10=TPM%2CTPMF&KEY3=&kind=TTCODE&sort=%2B&MAXDISP=100&KEY2=1stSec%2C2ndSec%2CMothers%2C1stF%2C2ndSecF%2CMothersF%2CE%2CFE%2CCE%2CR%2CJQ%2CJQStandard%2CJQStandardF%2CJQGrowth%2CJQGrowthF%2CEN%2CTPM%2CTPMF&KEY6=&REFINDEX=%2BTTCODE'

		if i > 0:
			url = baseURL + '&GO_BEFORE=&BEFORE='+ str(i*100)
		else:
			url = baseURL
		destinations.append(url)
	return destinations

def transform_metadata(body, url=''):
	df = pd.read_html(body)[0]
	df = df.dropna(how='all')
	df = df.ix[:,0:1]
	df.columns = ['Code', 'Name']
	df = df.dropna(axis='rows')
	df = df[df[df.columns[0]].apply(lambda x: x.isnumeric())]
	df['Code'] = 'http://quote.jpx.co.jp/jpx/template/quote.cgi?F=tmp/e_stock_detail&MKTN=T&QCODE=' + df['Code'] + '?F=tmp/e_stock_detail&MKTN=T&QCODE=' + df['Code']
	dataDestinations.extend(list(df['Code']))

def transform_data(body, url=''):
	soup = BeautifulSoup(body, 'lxml')
	for link in soup.find_all('a', href=True):
		if 'QCODE' in link['href']:
			code = link['href'].split('QCODE=')[1].split('&')[0]
			break
	timeSeries = soup.find(id="histData")['value']
	timeSeries = unicode(timeSeries)
	if len(timeSeries) > 0:
		df = pd.DataFrame.from_csv(StringIO(timeSeries), sep=",", parse_dates=False, header=None, index_col=None)
		df.drop(df.columns[[-1]], axis=1, inplace=True)
		df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
		print df.tail(1)
	else:
		sys.stderr.write(str(code) + ' ' + ' has returned 0 values. check if deprecated\n')

if __name__ == "__main__":
	headers = {
		'Referer': 'http://www2.tse.or.jp/tseHpFront/JJK020010Action.do',
				}
	dataDestinations = []
	metadataDestinations = generate_metadata_destinations()
	scraper.Scraper(destinations=metadataDestinations,
					transform=transform_metadata,
					headers=headers)
	scraper.Scraper(destinations=dataDestinations,
					transform=transform_data,
					headers=headers)
