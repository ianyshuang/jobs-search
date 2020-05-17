from selenium import webdriver
from bs4 import BeautifulSoup
from os import path, getcwd
from pymongo import MongoClient
import time
import requests


def get_job_links(base_url, query):
  '''
  Get all job links given query conditions

  :param str base_url: The base url of the website that we want to scrape
  :param dictionary query: The query string object that we use when sending GET request to the server
  '''

  full_url = requests.get(base_url, query).url

  driver.get(full_url)

  # find out the number of pages of data
  # store it in 'pages' so that we can go through all the pages later
  pages_select_element = driver.find_elements_by_class_name('gtm-paging-top')
  pages = len(pages_select_element[0].find_elements_by_tag_name('option'))
  iterations = pages // 15 + 1

  job_links = []  # use to store all job links(website url)

  # go through all pages
  for i in range(iterations):
    # 因 104 的網站在 15 頁內的「下一頁」，並不會直接跳轉頁面，而是往下滑至底部後會動態生成 (發送 AJAX 然後 browser 再 re-render)
    # 因此使用 window.scrollTo 滑至底部繼續載入下一頁
    # 動態生成做最多到 15 個頁面，第 16 頁後必須手動點選「下一頁」才可繼續
    print('Loading pages {} ~ {}'.format(i*15 + 1, i*15 + 15))
    if i != 0:
      query['page'] = i * 15 + 1
      full_url = requests.get(base_url, query).url
      driver.get(full_url)  # send a GET request to query jobs

    try:
      if i != iterations - 1:
        while True:
          driver.execute_script(
              'window.scrollTo(0, document.body.scrollHeight);')
          time.sleep(0.5)

          next_page_elements = driver.find_elements_by_class_name(
              'js-more-page')

          if (len(next_page_elements)) != 0:
            break
      else:
        for i in range(20):
          driver.execute_script(
              'window.scrollTo(0, document.body.scrollHeight);')
          time.sleep(0.5)

      soup = BeautifulSoup(driver.page_source, 'html.parser')

      for a in soup.find_all('a', 'js-job-link'):
          job_links.append(a['href'])
    except Exception as e:
      print(e)
      driver.quit()

  return job_links

def get_job_details (job_links):
  '''
  Iterate the job links and get jobs detail information from those links

  param: list job_links: Website URL of that job
  '''

  jobs_detail = [] # list to store all job detail information

  for i in range(len(job_links)):
    try:
      job_url = 'https:{}'.format(job_links[i])
      job_response = driver.get(job_url)
      time.sleep(1) # wait for the driver to load the website
      soup = BeautifulSoup(driver.page_source, 'html.parser')

      # initiate data structure for job
      data = {
        'job_title': None,
        'company_name': None,
        'job_description': None,
        'job_types': [],
        'job_salary': None,
        'job_experience': None,
        'education': [],
        'major': [],
        'language': None,
        'tools': [],
        'skills': [],
        'other_requirements': None
      }

      # 取得工作職稱
      job_title = soup.find('div', {'class': 'job-header__title'}).find('h1').contents[0]
      data['job_title'] = job_title

      # 取得公司名稱
      company_name = soup.find('div', {'class': 'job-header__title'}).find('div').find('a').text
      data['company_name'] = company_name

      # 取得工作內容
      job_description = soup.find('p', {'class': 'job-description__content'}).text
      data['job_description'] = job_description

      # 取得工作細節的 tag elements 並從其中取出多種資訊
      job_table_elements = soup.find('div', {'class': 'job-description-table'}).find_all('div', {'class': 'row'})
      # 取得職務類別
      job_types_elements = job_table_elements[0].find('div', {'class': 'job-description-table__data'}).find_all('u')
      job_types = [e.text for e in job_types_elements]
      data['job_types'] = job_types

      # 取得薪資範圍
      job_salary = job_table_elements[1].find('div', {'class': 'job-description-table__data'}).find('p').text
      data['job_salary'] = job_salary

      # 取得條件要求
      requirements_table_one = soup.select('div.job-requirement-table.row')[0].select('div.job-requirement-table__data')

      job_experience = requirements_table_one[1].find('p').text # 取得工作經驗
      data['job_experience'] = job_experience

      education = requirements_table_one[2].find('p').text.split('、')  # 取得學歷要求
      data['education'] = education

      major = requirements_table_one[3].find('p').text.split('、')  # 取得科系要求
      data['major'] = major

      language = requirements_table_one[4].find('p').text # 取得語言能力
      data['language'] = language

      tools_elements = requirements_table_one[5].find_all('u')  # 取得擅長工具
      tools = [e.text for e in tools_elements]
      data['tools'] = tools

      skills_elements = requirements_table_one[6].find_all('u') # 取得工作技能
      skills = [e.text for e in skills_elements]
      data['skills'] = skills

      other_requirements = soup.select('div.job-requirement.col')[0].select('p')[0].text  # 取得其他條件
      data['other_requirements'] = other_requirements

      # append job information to job_details list
      jobs_detail.append(data)
      
    except Exception as e:
      print(e)
      continue

  
  return jobs_detail

def save_data_to_local_mongo(keyword, data):
  '''
  Save the data into local MongoDB

  :param str keyword: Job keyword
  :param list data: Job data to be inserted
  '''

  try:
    client = MongoClient('localhost', 27017)

    db_name = 'job-{}-information'.format(keyword)
    db = client[db_name]
    collection = db['jobs']

    collection.insert_many(data)
  except Exception as e:
    print(e)

  print('Finish Saving Data to Local MongoDB!')
  return None


# create selenimu webdriver
driver_path = path.join(getcwd(), 'bin/chromedriver')  # if using Windows, change the second argument to bin/chomedriver.exe
driver = webdriver.Chrome(driver_path)

# initiate url and query string
base_url = 'https://www.104.com.tw/jobs/search/'
keyword = input("輸入你想要搜尋的關鍵字來找到相關工作: ")
query = {
    'ro': '1',  # 工作性質：全部/全職/兼職/高階/其他，1 為全職
    'keyword': keyword,  # 欲搜尋的關鍵字
    'isNew': '30',  # 30 天內更新過的
    'mode': 'l',  # 呈現方式為條列式 (list)
    'page': '1'
}

job_links = get_job_links(base_url, query)  # get all job links

jobs_detail = get_job_details(job_links)  # get those jobs' detail information

driver.quit()

save_data_to_local_mongo(keyword, jobs_detail)  # save data to local MongoDB
