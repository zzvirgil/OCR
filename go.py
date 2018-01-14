# -*- coding: utf-8 -*-

###########################
# author: zz.virgil
# date: 2018/01/14 17:34
###########################

import requests
from bs4 import BeautifulSoup as bs
from retrying import retry
from PIL import Image
from aip import AipOcr
import os

##############
# 百度OCR接入
##############
APP_ID = '10690295'
API_KEY = 'WKpFluI1IDiBZAXORdqy1ua5'
SECRET_KEY = 'nAd9jIniaAuC2IbEnLPb1KopjbuZHrbk'
client = AipOcr(APP_ID, API_KEY, SECRET_KEY)

################################
# 百度搜索方法(requests, bs4爬取)
# main: search()
# question <str> 题目
# options <list> 待统计答案项
################################
def no_result(results):
  return not len(results)

@retry(retry_on_result=no_result, stop_max_attempt_number=5)
def getSoup(question):
  headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
  url = 'http://www.baidu.com/s'
  payload = {'wd': question}
  req = requests.get(url, params=payload, headers=headers, timeout=5)
  # print(req.status_code)
  soup = bs(req.content, 'html.parser', from_encoding='utf8')
  results = soup.find_all('div', class_='c-abstract')
  # print(len(results))
  return results
  
def search(question, options):
  results = getSoup(question)
  resStr = ''
  for res in results:
    resStr += str(res)

  # 统计词频  
  rate = []
  for option in options:
    obj = {}
    obj['name'] = option
    obj['num'] = resStr.count(option)
    rate.append(obj)
  return rate

##############################
# 二值化处理 (用于图像降噪)
# img <PIL object> 图片文件对象
# threshold <number> 临界值
##############################
def binaryzation(img, threshold):
  table = []
  for i in range(256):
    if i < threshold:
     table.append(0)
    else:
      table.append(1)
  return img.convert('L').point(table, '1')

##################################################
# PIL裁剪图像
# 提取 问题 与 答案 (注掉部分：将答案合并为一张图片保存)
# name <str> 图片文件名
##################################################
def cropImg(name):
  imgry = Image.open(os.path.join('imgs', name))
  if not os.path.isdir('export/{}'.format(name)):
    os.makedirs('export/{}'.format(name))

  questionRegion = (50, 310, 700, 450)
  questionImg = imgry.crop(questionRegion)
  questionImg.save('export/{}/question.png'.format(name))

  # 不合并：
  for i in range(3):
    optionRegion = (105, 535+i*112, 645, 620+i*112)
    optionImg = imgry.crop(optionRegion)
    optionImg.save('export/{}/option{}.png'.format(name, i+1))

  ## 合并：
  # optList = []
  # for i in range(3):
  #   optionRegion = (105, 535+i*112, 645, 620+i*112)
  #   optionImg = imgry.crop(optionRegion)
  #   optList.append(optionImg)
  # newImg = Image.new('RGB', (540, 255))
  # for i, opt in enumerate(optList):
  #   newImg.paste(opt, (0, 0+i*85, 540, 85+i*85))
  # newImg.save('export/{}/option.png'.format(name))

###############################
# 读取本地图片文件
# return <bytes>
###############################
def getFile(filePath):
  with open(filePath, 'rb') as file:
    content = file.read()
    file.close()
    return content

#######################
# 主方法
# name <str> 图片文件名
#######################
def go(name):
  cropImg(name)
  # 调用百度OCR识别
  image = getFile('export/{}/question.png'.format(name))
  res = client.basicGeneral(image)
  # print(res)
  # 若未识别到任何内容，则提高识别精度
  if res.__contains__('words_result_num') and not res['words_result_num']:
    res = client.basicAccurate(image)
    # print(res)
  elif res.__contains__('error_code'):
    res = client.basicAccurate(image)
    # print(res)

  resWords = res['words_result']
  # 拼接返回内容
  question = ''
  for word in resWords:
    question += word['words']
  # 去除题目索引
  tmp = question[1:2]
  question = question[2:] if str.isdigit(tmp) or tmp == '.' else question[1:]
  print('''Question:
    {}
  Options:'''.format(question))

  options = []
  for i in range(3):
    # 调用百度OCR识别
    image = getFile('export/{}/option{}.png'.format(name, i+1))
    res = client.basicGeneral(image)
    # print(res)
    # 若未识别到任何内容，则提高识别精度
    if res.__contains__('words_result_num') and not res['words_result_num']:
      res = client.basicAccurate(image)
      # print(res)
    elif res.__contains__('error_code'):
      res = client.basicAccurate(image)
      # print(res)

    resWords = res['words_result']
    # 拼接返回内容
    option = ''
    for word in resWords:
      option += word['words']
    options.append(option)
  
  ## 测试用:
  # question = '逆时针弯道跑时,身体应向哪个方向倾斜?'
  # options = ['前', '右', '左']
  rate = search(question, options)
  for item in rate:
    print('{}{}: {}'.format(' '*6, item['name'], item['num']))

if __name__ == '__main__':
  # whichImg = input('input a imgName:')
  # go(whichImg)
  go('test3.png')



