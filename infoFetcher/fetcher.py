# -*- coding: UTF-8
from bs4 import BeautifulSoup
import requests
import xml.etree.ElementTree as ET
import codecs
import time

logToFile = 0
gLogFile = 'log.log'

def debugTrace(str):
    if logToFile == 1:
        writeToFile(gLogFile, time.ctime() + '   ' + str)
    else:
        print(str)

def writeToFile(filePath, str):
    targetFile = codecs.open(filePath, 'a+', 'utf-8')
    targetFile.write(str + '\n')
    targetFile.close()

def fetchContentFromLink(link, json = False):
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0',
            'Connection' : 'keep-alive', 'Cache-Control': 'no-cache'}
    r = requests.get(link, headers = headers)
    if r.status_code == 200:
        if json:
            return r.json()
        else:
            return BeautifulSoup(r.text, 'html5lib')
    else:
        debugTrace("Fail to get %s, status code: %d" % (link, r.status_code))

def parseTrToSaleElement(tr):


def getRealEstateSaleInfoFromPage(pageLink):
    estateSaleInfo = []
    soup = fetchContentFromLink(pageLink)
    if soup == None:
        debugTrace("Fail to fetch content from " + pageLink)
        return estateSaleInfo
    table = soup.find('table')
    if table == None:
        debugTrace("No table element in " + pageLink)
        return estateSaleInfo
    trs = table.find_all('tr')
    if len(trs) <= 1:
        debugTrace("No tr in the table " + pageLink)
        return estateSaleInfo
    for tr in trs:
        elem = parseTrToSaleElement(tr)
        if elem != None:


if __name__ == '__main__':
    main()