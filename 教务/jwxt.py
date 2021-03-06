"""使用requests连接教务网站获取成绩"""
import requests
import base64
from pyquery import PyQuery as pd
import csv
import pymongo

class JWXT(object):
    def __init__(self):
        self.base_url = 'http://bkjx.wust.edu.cn/jsxsd/xk/LoginToXk'    # 发生重定向的url
        # self.score_url = 'http://bkjx.wust.edu.cn/jsxsd/kscj/cjcx_list?kksj=2020-2021-1'    # 成绩文档url
        self.score_url = 'http://bkjx.wust.edu.cn/jsxsd/kscj/'    # 成绩文档url
        self.headers = {    # 自定义请求头
            'Host': 'bkjx.wust.edu.cn',
            'Origin': 'http://bkjx.wust.edu.cn',
            'Referer': 'http://bkjx.wust.edu.cn/jsxsd/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/88.0.4324.96'
            }
        self.kksj = ['cjcx_list', 'cjcx_list?kksj=2019-2020-1', 'cjcx_list?kksj=2019-2020-2',
                     'cjcx_list?kksj=2020-2021-1', 'cjcx_list?kksj=2020-2021-2',
                     'cjcx_list?kksj=2021-2022-1', 'cjcx_list?kksj=2021-2022-2',
                     'cjcx_list?kksj=2022-2023-1', 'cjcx_list?kksj=2022-2023-2']
        self.session = requests.Session()   # 用Session维持会话，同时不必对cookies进行处理

    def login(self, usr, psd):  # 登录教务系统
        """post请求提交学号和密码"""
        # 学号和密码进行base64加密
        usrid = base64.b64encode(bytes(usr, encoding='utf-8')).decode('ascii')
        usrpsd = base64.b64encode(bytes(psd, encoding='utf-8')).decode('ascii')
        # 构造encoded参数，注意学号与密码中间还要加'%%%'
        encoded = usrid + '%%%' + usrpsd
        form = {    # 需要提交的表单
            'userAccount': usr,
            'userPassword': '',
            'encoded': encoded
        }
        self.session.post(self.base_url, data=form, headers=self.headers)

    def getHTML(self, n):  # 获得成绩页面的HTML
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/88.0.4324.96'}
            response = self.session.get(self.score_url + self.kksj[n], headers=headers)
            response.raise_for_status()
            return response.text
        except:
            return None

    def save_to_file(self):
        """分析html源码，对信息进行提取并保存到csv文件中"""
        doc = pd(self.getHTML(n)) if self.getHTML(n) is not None else ''
        tr_items = doc('tr').items()
        lst = []
        for ls in tr_items:  # 处理'\n'并将以' '分隔的列表放入lt
            lst.append(ls.text().split('\n'))
        # 忽略无用项
        lst[0].remove('成绩标识')
        lst[0].remove('补重学期')
        lst[0].remove('通选课类别')
        credit, GPA = 0, 0  # 计算学分和GPA
        for ls in lst[1:]:  # 对'分组'一项进行处理
            if ls[4].isdigit() is True or ls[4].isalpha() is True:
                ls.insert(4, ' ')
            credit += eval(ls[6])
            GPA += eval(ls[6]) * eval(ls[8])
        GPA = GPA / credit  # 计算GPA
        lst.append('GPA={:.2f}'.format(GPA))
        lst[-1].split(' ')
        filename = 'all_score.csv' if n == 0 else lst[1][1]+'score.csv'
        with open(filename, 'w', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(lst)
            print('保存文件成功')

    def save_to_mongo(self):
        """对html源码进行分析并提取有效信息，保存到mongodb中"""
        term = ['全部成绩', '2019-2020-1', '2019-2020-2', '2020-2021-1', '2020-2021-2',
                '2021-2022-1', '2021-2022-2', '2022-2023-1', '2022-2023-2']
        doc = pd(self.getHTML(n)) if self.getHTML(n) is not None else ''
        tr_items = doc('tr').items()
        lst, flag = [], -1
        for tr in tr_items:
            flag += 1
            if flag > 0:
                dic = {
                    '序号': tr('td:nth-child(1)').text(),
                    '开课学期': tr('td:nth-child(2)').text(),
                    '课程编号': tr('td:nth-child(3)').text(),
                    '课程名称': tr('td:nth-child(4)').text(),
                    '分组名': tr('td:nth-child(5)').text(),
                    '成绩': tr('td:nth-child(6)').text(),
                    '学分': tr('td:nth-child(8)').text(),
                    '总学时': tr('td:nth-child(9)').text(),
                    '绩点': tr('td:nth-child(10)').text(),
                    '考核方式': tr('td:nth-child(12)').text(),
                    '考试性质': tr('td:nth-child(13)').text(),
                    '课程性质': tr('td:nth-child(14)').text()
                }
                lst.append(dic)
        MONGO_COLLECTION = term[n]
        client = pymongo.MongoClient('localhost')
        db = client['jwxt']
        try:
            if db[MONGO_COLLECTION].insert_many(lst):
                print('保存到MongoDB成功')
        except:
            print('保存到MongoDB失败')


if __name__ == '__main__':
    jwxt = JWXT()
    usrAccount = input('学号：')
    usrPassword = input('密码：')
    # 默认n=0为获取全部成绩,1-8代表获取相应学期成绩
    n = int(input('查询学期(0代表全部成绩)：'))
    jwxt.login(usrAccount, usrPassword)
    jwxt.save_to_file()
