# -*- coding: UTF-8
from bs4 import BeautifulSoup
import requests
import xml.etree.ElementTree as ET
import codecs
import time
import os
import datetime

selfDir = os.path.dirname(os.path.abspath(__file__))
logToFile = 0
gLogFile = 'log.log'
gWebLinkScheme = 'http://www.tmsf.com/yh/2018yh/%4d_%d_preview.htm'
xmlDir = selfDir + '/../xml/'
attrNames = [
    'name',             # 楼盘名
    'distArea',         # 所属城区
    'saleNumber',       # 预售证编号
    'lotteryState',     # 摇号<br />状态
    'saleAmount',       # 本次摇号房源
    'unitPrice',        # 均价<br />(元/㎡)
    'fitmentCost',       # 装修<br />(元/㎡)
    'percentForNo',     # 无房<br />比例
    'moneyCredit',      # 存款证明
    'percentHit'        # 整体<br />中签率
]

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
    elem = []
    tds = tr.find_all('td')
    for td in tds:
        brs = td.find_all('br')
        for br in brs:
            br.decompose()
        elem.append(''.join(map(lambda x: x.string, td.contents)))
    return elem

def parseTableHeader(tr):
    tblHeader = []
    ths = tr.find_all('th')
    for th in ths:
        brs = th.find_all('br')
        for br in brs:
            br.decompose()
        tblHeader.append(''.join(map(lambda x: x.string, th.contents)))
    return tblHeader

def getRealEstateSaleInfoFromPage(pageLink):
    estateSaleInfo = {
        'headers': [],
        'infos': []
    }
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
    estateSaleInfo['headers'] = parseTableHeader(trs[0])
    for tr in trs[1:]:
        elem = parseTrToSaleElement(tr)
        if len(elem) != 0:
            estateSaleInfo['infos'].append(elem)
    #print(estateSaleInfo)
    return estateSaleInfo

def generateOneEstateXml(elem):
    oe = ET.Element('oneEstate')
    idxes = range(len(elem))
    for i in idxes:
        #print(attrNames[i] + ': ' + elem[i])
        subElem = ET.SubElement(oe, attrNames[i])
        subElem.text = elem[i]
    ET.SubElement(oe, 'latitude')
    ET.SubElement(oe, 'longitude')
    return oe

def generateXmlFile(estateSaleInfo):
    infoXml = ET.Element('estateSaleInfo', attrib={'year': str(estateSaleInfo['year']), 'month': str(estateSaleInfo['month'])})
    for elem in estateSaleInfo['infos']:
        estateXml = generateOneEstateXml(elem)
        infoXml.append(estateXml)
    tree = ET.ElementTree(infoXml)
    xmlFileName = xmlDir + ('%4d%02d.xml' % (estateSaleInfo['year'], estateSaleInfo['month']))
    tree.write(xmlFileName, encoding = 'utf-8', xml_declaration=True)

def generateWebLink(year, month):
    return (gWebLinkScheme % (year, month))

def generateSaleInfoXmlByYearMonth(year, month):
    link = generateWebLink(year, month)
    estateSaleInfo = getRealEstateSaleInfoFromPage(link)
    estateSaleInfo['year'] = year
    estateSaleInfo['month'] = month
    formatStr = ''
    for x in estateSaleInfo['headers']:
        formatStr = formatStr + x + '\t'
    #print(formatStr)
    for elem in estateSaleInfo['infos']:
        formatStr = ''
        for y in elem:
            formatStr = formatStr + y + '\t'
    #    print(formatStr)
    generateXmlFile(estateSaleInfo)

if __name__ == '__main__':
    #year = 2019
    #for month in range(1, 13):
    #    estateSaleInfo = generateSaleInfoXmlByYearMonth(year, month)
    today = datetime.date.today()
    generateSaleInfoXmlByYearMonth(today.year, today.month)


