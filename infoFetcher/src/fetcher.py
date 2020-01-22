# -*- coding: UTF-8
from bs4 import BeautifulSoup
import requests
import xml.etree.ElementTree as ET
import codecs
import time
import os
import datetime
import json
import re
import time

selfDir = os.path.dirname(os.path.abspath(__file__))
logToFile = 0
gLogFile = 'log.log'
gSiteUrl = 'http://www.tmsf.com'
gJsonUrlFormat = 'http://jia3.tmsf.com/tmj3/property_detail.jspx?json=true&propertyid=%s&siteid=%s'
gWebLinkScheme = 'http://www.tmsf.com/yh/2018yh/%4d_%d_preview.htm'
xmlDir = selfDir + '/../xml/'
jsonFilePath = selfDir + '/../json/estateSaleInfo.json'
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
    debugTrace('try to find link ' + link)
    headers = {
        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.53 Safari/537.36 Edg/80.0.361.33',
        'Connection' : 'keep-alive',
        'Cache-Control': 'no-cache'
    }
    time.sleep(5)
    r = requests.get(link, headers = headers)
    if r.status_code == 200:
        if json:
            return r.json()
        else:
            return BeautifulSoup(r.text, 'html5lib')
    else:
        debugTrace("Fail to get %s, status code: %d" % (link, r.status_code))
        return None

def findLocation(elem, soup):
    debugTrace(elem['name'])
    elem['location'] = {
        'latitude': '',
        'longitude': ''
    }
    divs = soup.find_all('div', attrs={'class': 'bigT'})
    for div in divs:
        font = div.find('font', attrs={'class': 'f16 bold'})
        if font == None:
            continue
        a = font.find('a')
        if a == None:
            continue
        if elem['name'] != a.string:
            continue
        pagePath = a['href']
        strs = pagePath.split('_')
        if len(strs) < 3:
            continue
        propertyId = strs[2]
        siteId = strs[1]
        linkUrl = gJsonUrlFormat % (propertyId, siteId)
        jsonData = fetchContentFromLink(linkUrl, True)
        if 'cohProperty' not in jsonData.keys():
            continue
        if ('prjx' not in jsonData['cohProperty']) or ('prjy' not in jsonData['cohProperty']):
            continue
        if (jsonData['cohProperty']['prjx'] == '' or jsonData['cohProperty']['prjy'] == ''):
            continue
        elem['location']['longitude'] = float(jsonData['cohProperty']['prjx'])
        elem['location']['latitude'] = float(jsonData['cohProperty']['prjy'])
        debugTrace('find positon %f' % (elem['location']['longitude']))
        break
    return elem

def parseTrToSaleElement(tr):
    elem = {}
    tds = tr.find_all('td')
    idxes = range(len(tds))
    for i in idxes:
        brs = tds[i].find_all('br')
        for br in brs:
            br.decompose()
        elem[attrNames[i]] = (''.join(map(lambda x: x.string, tds[i].contents)))
    return elem

def parseTableHeader(tr):
    tblHeader = {}
    ths = tr.find_all('th')
    idxes = range(len(ths))
    for i in idxes:
        brs = ths[i].find_all('br')
        for br in brs:
            br.decompose()
        tblHeader[attrNames[i]] = (''.join(map(lambda x: x.string, ths[i].contents)))
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
            findLocation(elem, soup)
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

def generateJsonFile(estateSaleInfo):
    with open(jsonFilePath, 'w') as f:
        json.dump(estateSaleInfo, f, indent = 4, encoding="utf-8")

def loadJsonFile():
    #return {}
    if not os.path.exists(jsonFilePath):
        return {}
    with open(jsonFilePath, 'r') as f:
        return json.load(f)

def generateWebLink(year, month):
    return (gWebLinkScheme % (year, month))

def getSaleInfoByYearMonth(year, month):
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
    return estateSaleInfo
    #    print(formatStr)

def getNextMonth(currentMonth):
    if currentMonth[1] == 12:
        return [currentMonth[0] + 1, 1]
    else:
        return [currentMonth[0], currentMonth[1] + 1]

def isTodayInGivenMonth(month):
    today = datetime.date.today()
    if month[0] == today.year and month[1] == today.month:
        return True
    else:
        return False

if __name__ == '__main__':
    estateSaleInfo = {}
    oldInfo = loadJsonFile()
    #oldInfo = {}
    month = [2019, 1]
    while not isTodayInGivenMonth(month):
        keyStr = '%4d%02d' % (month[0], month[1])
        if keyStr in oldInfo.keys():
            estateSaleInfo[keyStr] = oldInfo[keyStr]
        else:
            estateSaleInfo[keyStr] = getSaleInfoByYearMonth(month[0], month[1])
        month = getNextMonth(month)
    keyStr = '%4d%02d' % (month[0], month[1])
    estateSaleInfo[keyStr] = getSaleInfoByYearMonth(month[0], month[1])
    generateJsonFile(estateSaleInfo)


