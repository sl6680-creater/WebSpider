# 使用selenium自动化测试工具获取成绩
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import csv

def init_browser():  # 创建、初始化browser
    # 启用无界面模式，Headless
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    browser = webdriver.Chrome(options=chrome_options)
    return browser


def login(usrAccount, usrPassword):
    browser.get('http://bkjx.wust.edu.cn/')
    usr = browser.find_element_by_id('userAccount')  # 找到学号输入栏
    psd = browser.find_element_by_id('userPassword')  # 找到密码输入栏
    btn = browser.find_element_by_css_selector('#ul1 li button.btn')    # 找到登录按钮
    usr.send_keys(usrAccount)
    psd.send_keys(usrPassword)
    btn.click()
    time.sleep(2)


def getscores():
    main_page = 'http://bkjx.wust.edu.cn/jsxsd/framework/xsMain.jsp'
    browser.get(main_page)  # 进入登陆后的主页面
    browser.switch_to.frame('Frame0')   # 跳转到子框架Frame0
    # 找到课程成绩查询对应标签
    grid = browser.find_element_by_class_name('cy_icon').find_elements_by_class_name('grid')[1]
    # 执行标签内onclick属性的javascript
    browser.execute_script(grid.get_attribute('onclick'))
    time.sleep(2)
    # 先返回父框架
    browser.switch_to.parent_frame()
    browser.switch_to.frame('Frame1')
    time.sleep(1)
    # 切换到成绩单框架
    browser.switch_to.frame('cjcx_list_frm')
    tr_list = browser.find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')
    lst = [[] for _ in range(len(tr_list))]     # 创建二维列表
    th_list = tr_list[0].find_elements_by_tag_name('th')    # th-列名
    for th in th_list:
        lst[0].append(th.text)
    index = 1   # 计数器
    while index < len(tr_list):     # 各项成绩放入lst
        for tr in tr_list[1:]:
            td_list = tr.find_elements_by_tag_name('td')
            for td in td_list:
                if td.text == '':   # 处理空白文本项
                    lst[index].append('  ')
                else:
                    lst[index].append(td.text)
            index += 1
    return lst


def save_to_file(lst):
    with open(lst[1][1]+'score.csv', 'w') as csvfile:
        csv.writer(csvfile).writerows(lst)
    print('文件保存成功')


def main():
    login(usrAccount, usrPassword)
    lst = getscores()
    save_to_file(lst)


if __name__ == '__main__':
    browser = init_browser()
    usrAccount = input('学号：')
    usrPassword = input('密码：')
    main()
