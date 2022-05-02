# -*- coding: UTF-8 -*-
"""
__Author__ = "MakiNaruto"
__Version__ = "2.1.0"
__Description__ = ""
__Created__ = 2022/5/02 14:16
"""

import re
import os
import json
import execjs
import pickle
import platform
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def save_cookies(login_cookies):
    """ 保存cookies """
    with open('cookies.pkl', 'wb') as fw:
        pickle.dump(login_cookies, fw)


def load_cookies():
    """ 读取保存的cookies """
    try:
        with open('cookies.pkl', 'rb') as fr:
            cookies = pickle.load(fr)
        return cookies
    except Exception as e:
        print('-' * 10, '加载cookies失败', '-' * 10)
        print(e)


def check_login_status(login_cookies):
    """ 检测是否登录成功 """
    personal_title = '我的大麦-个人信息'

    headers = {
        'authority': 'passport.damai.cn',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.83 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'referer': 'https://passport.damai.cn/login?ru=https://passport.damai.cn/accountinfo/myinfo',
        'accept-language': 'zh,en;q=0.9,en-US;q=0.8,zh-CN;q=0.7',
    }

    response = requests.get('https://passport.damai.cn/accountinfo/myinfo',
                            headers=headers,
                            cookies=login_cookies)
    personal_info = BeautifulSoup(response.text, 'html.parser')
    if personal_info.title.text == personal_title:
        return True
    else:
        return False


def account_login(login_type: str, login_id=None, login_password=None):
    """
    登录大麦网

    :param login_id:
    :param login_password:
    :param login_type:  选择哪种方式进行登录
    :return:
    """
    damai_title = '大麦网-全球演出赛事官方购票平台-100%正品、先付先抢、在线选座！'

    login_url = 'https://passport.damai.cn/login'
    option = webdriver.ChromeOptions()  # 默认Chrome浏览器
    # 关闭开发者模式, window.navigator.webdriver 控件检测到你是selenium进入，若关闭会导致出现滑块并无法进入。
    option.add_experimental_option('excludeSwitches', ['enable-automation'])
    option.add_argument('--disable-blink-features=AutomationControlled')
    # option.add_argument('headless')               # Chrome以后台模式进行，注释以进行调试
    # option.add_argument('window-size=1920x1080')  # 指定分辨率
    # option.add_argument('no-sandbox')             # 取消沙盒模式
    # option.add_argument('--disable-gpu')          # 禁用GPU加速
    # option.add_argument('disable-dev-shm-usage')  # 大量渲染时候写入/tmp而非/dev/shm
    if platform.system().lower() == 'linux':
        chromedriver = os.path.join(os.getcwd(), 'chromedriver_linux')
    elif platform.system().lower() == 'windows':
        chromedriver = os.path.join(os.getcwd(), 'chromedriver_windows')
    else:
        chromedriver = os.path.join(os.getcwd(), 'chromedriver_mac')

    driver = webdriver.Chrome(chromedriver, options=option)
    driver.set_page_load_timeout(60)
    driver.get(login_url)
    if login_type == 'account':
        driver.switch_to.frame('alibaba-login-box')  # 切换内置frame，否则会找不到元素位置
        driver.find_element_by_name('fm-login-id').send_keys(login_id)
        driver.find_element_by_name('fm-login-password').send_keys(login_password)
        driver.find_element_by_class_name('password-login').send_keys(Keys.ENTER)
    WebDriverWait(driver, 180, 0.5).until(EC.title_contains(damai_title))

    login_cookies = {}
    if driver.title != damai_title:
        print('登录异常，请检查页面登录提示信息')
    for cookie in driver.get_cookies():
        login_cookies[cookie['name']] = cookie['value']
    if check_login_status(login_cookies):
        return login_cookies


def get_api_param():
    """ 获取请求大麦API所必须的一些参数, 可能大麦网js代码更新后需要修改此函数内的代码以重新获得参数信息 """

    def format_param(context):
        param = []
        for line in context.split(','):
            k, v = line.split(':')
            param.append('"{}":{}'.format(k, v))
        param = json.loads('{' + ','.join(param) + '}')
        return param

    js_code_define = requests.get(
        "https://g.alicdn.com/damai/??/vue-pc/0.0.70/vendor.js,vue-pc/0.0.70/perform/perform.js").text
    # 获取商品SKU的API参数
    commodity_param = re.search('getSkuData:function.*?\|\|""}}', js_code_define).group()
    commodity_param = re.search('data:{.*?\|\|""}}', commodity_param).group()
    commodity_param = commodity_param.replace('data:{', ''). \
        replace('this.vmSkuData.privilegeId||""}}', '""'). \
        replace('itemId:e', 'itemId:""')
    commodity_param = format_param(commodity_param)
    # 获取订单购买用户的API参数
    ex_params = re.search(',i=Z}else{.*?;e&&', js_code_define).group()
    ex_params = re.search('{.*}', ex_params).group()
    ex_params = ex_params.replace('{var u=', '')[1:-1]
    ex_params = format_param(ex_params)
    return commodity_param, ex_params


def get_sign_code(h5_token: str, time_stamp, api_param) -> str:
    """
    返回请求选座信息接口必备的sign信息

    :return:
    """
    node = execjs.get()
    with open('signcode.js', 'r', encoding='utf-8') as f:
        js_file = f.read()
    js_exec = node.compile(js_file)
    param1 = '{}&{}&12574478&'.format(h5_token, time_stamp)

    context = param1 + api_param
    sign_code = js_exec.call('calcaulate', context)
    return sign_code


def get_select_seat_params(item_id, data_id=None):
    """ 获取座位信息的必备参数 """
    headers = {
        'authority': 'detail.damai.cn',
        'accept': '*/*',
        'accept-language': 'zh,en;q=0.9,en-US;q=0.8,zh-CN;q=0.7',
        'referer': 'https://detail.damai.cn/item.htm?spm=a2oeg.home.card_1.ditem_1.591b23e1qozgyw&id=671100996170',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'script',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
    }

    params = {"itemId": item_id,
              "dataId": data_id,
              "dataType": 4,
              "apiVersion": 2.0,
              "dmChannel": "damai_pc",
              "bizCode": "ali.china.damai",
              "scenario": "itemsku"
              }

    response = requests.get('https://detail.damai.cn/subpage', headers=headers, params=params)
    if response.status_code == 200:
        result = json.loads(response.text[5:-1])
        item_basic_info = result.get('itemBasicInfo')
        city_id = item_basic_info.get('nationalStandardCityId')
        project_id = item_basic_info.get('projectId')
        item_id = item_basic_info.get('itemId')
        perform_id = result.get('perform').get('performId')
        return city_id, project_id, item_id, perform_id


def get_seat_dynamic_info(cookies, project_id, item_id, perform_id):
    """ 获取 standId, 用于获取所有座位信息 """
    headers = {
        'authority': 'mtop.damai.cn',
        'accept': 'application/json',
        'accept-language': 'zh,en;q=0.9,en-US;q=0.8,zh-CN;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        # Requests sorts cookies= alphabetically
        # 'cookie': 'cna=QAvhGhruGS4CAXx+ibfGKnY/; t=1ff77fc3f03114d784e6055f2e58128e; damai.cn_email=23964951@qq.com; damai.cn_nickName=MakiNaruto; munb=4031179480; xlly_s=1; cookie2=109b25aa6388dfbc71b8d6cb05dbb154; _tb_token_=3e87e37a17bde; _samesite_flag_=true; _hvn_login=18; csg=21db6663; damai.cn_user=SHm/AXRMF7mxpN8uip9sNS+4EH/qiS5ef3Q/K/+slykinDgISXh0XsCSZVMGSCKgGxb2+Rjuqig=; damai.cn_user_new=SHm%2FAXRMF7mxpN8uip9sNS%2B4EH%2FqiS5ef3Q%2FK%2F%2BslykinDgISXh0XsCSZVMGSCKgGxb2%2BRjuqig%3D; h5token=3936e2bf88964af2a37c20b092c61c75_1_1; damai_cn_user=SHm%2FAXRMF7mxpN8uip9sNS%2B4EH%2FqiS5ef3Q%2FK%2F%2BslykinDgISXh0XsCSZVMGSCKgGxb2%2BRjuqig%3D; loginkey=3936e2bf88964af2a37c20b092c61c75_1_1; user_id=108050604; _m_h5_tk=2ef39e419fe42af48f9fb3adc7e043df_1651324694423; _m_h5_tk_enc=a442fe5379084c1830b4418f456f7fb3; tfstk=c4McBWjbVz_B4DFoOKwXCmEadKORZ9Wa-AkSUn0_9Hotq0MPi_CPTJd2qrYBu11..; l=eBgKXWFnLg3Eg5F3BOfwourza77OSIRAguPzaNbMiOCPOTfp5_f1W6qQzd89C3GNh6zeR3J8Iu2zBeYBcSvEdvNX0cWf96Hmn; isg=BEhIJmYUvgYlEtLl2khALh8EGbBa8az7J9rUOgL5lEO23ehHqgF8i95bVb2tbWTT',
        'origin': 'https://seatsvc.damai.cn',
        'referer': 'https://seatsvc.damai.cn/',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
    }
    h5_token = cookies.get('_m_h5_tk').split('_')[0]
    time_stamp = int(datetime.now().timestamp() * 1000)
    api_param = json.dumps({'projectId': project_id,
                            'performanceId': perform_id,
                            'itemId': item_id,
                            'hasPromotion': 'true',
                            'dmChannel': 'pc@damai_pc'}).replace(' ', '')
    sign_code = get_sign_code(h5_token, time_stamp, api_param)

    params = {
        'jsv': '2.6.0',
        'appKey': '12574478',
        't': time_stamp,
        'sign': sign_code,
        'type': 'originaljson',
        'dataType': 'json',
        'v': '1.0',
        'H5Request': 'true',
        'AntiCreep': 'true',
        'AntiFlood': 'true',
        'api': 'mtop.damai.wireless.seat.dynamicinfo',
        'data': api_param,
    }

    response = requests.get('https://mtop.damai.cn/h5/mtop.damai.wireless.seat.dynamicinfo/1.0/', params=params,
                            cookies=cookies, headers=headers)
    if response.status_code == 200:
        result = json.loads(response.text).get('data')
        stand_id = result.get('standColorList')[0].get('standId')
        seat_price_list = result.get('priceList')
        return stand_id, seat_price_list


def get_select_seat_api(cookies, perform_id, city_id):
    """ 得到请求所有座位信息的api地址 """
    h5_token = cookies.get('_m_h5_tk').split('_')[0]
    time_stamp = int(datetime.now().timestamp() * 1000)
    api_param = json.dumps({"cityId": city_id,
                            "pfId": 2147483647 ^ int(perform_id),
                            "excludestatus": True,
                            "svgEncVer": "1.0",
                            "dmChannel": "pc@damai_pc"}).replace(' ', '')
    sign_code = get_sign_code(h5_token, time_stamp, api_param)
    headers = {
        'authority': 'mtop.damai.cn',
        'accept': 'application/json',
        'accept-language': 'zh,en;q=0.9,en-US;q=0.8,zh-CN;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://seatsvc.damai.cn',
        'referer': 'https://seatsvc.damai.cn/',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
    }

    params = {
        'jsv': '2.6.0',
        'appKey': '12574478',
        't': time_stamp,
        'sign': sign_code,
        'type': 'originaljson',
        'dataType': 'json',
        'v': '1.3',
        'H5Request': 'true',
        'AntiCreep': 'true',
        'AntiFlood': 'true',
        'api': 'mtop.damai.wireless.project.getB2B2CAreaInfo',
        'data': api_param,
    }
    response = requests.get('https://mtop.damai.cn/h5/mtop.damai.wireless.project.getb2b2careainfo/1.3/',
                            headers=headers, params=params, cookies=cookies)
    if response.status_code == 200:
        api_text = json.loads(response.text).get('data').get('result')
        api_info = json.loads(api_text).get('seatQuYu')
        api_address = api_info.get('resourcesPath')
        seat_price_list = api_info.get('seatPriceList')
        return api_address


def get_valuable_seat_id(cookies, project_id, perform_id, city_id, stand_id):
    """ 获取可用的座位信息 """
    h5_token = cookies.get('_m_h5_tk').split('_')[0]
    time_stamp = int(datetime.now().timestamp() * 1000)
    api_param = json.dumps({"cityId": city_id,
                            "pfId": 2147483647 ^ int(perform_id),
                            "standIds": stand_id,
                            "channel": 100100010001,
                            "projectId": project_id,
                            "lessFirst": True,
                            "dmChannel": "pc@damai_pc"}).replace(' ', '')
    sign_code = get_sign_code(h5_token, time_stamp, api_param)

    headers = {
        'authority': 'mtop.damai.cn',
        'accept': 'application/json',
        'accept-language': 'zh,en;q=0.9,en-US;q=0.8,zh-CN;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://seatsvc.damai.cn',
        'referer': 'https://seatsvc.damai.cn/',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
    }

    params = {
        'jsv': '2.6.0',
        'appKey': '12574478',
        't': time_stamp,
        'sign': sign_code,
        'type': 'originaljson',
        'dataType': 'json',
        'v': '1.0',
        'H5Request': 'true',
        'AntiCreep': 'true',
        'AntiFlood': 'true',
        'api': 'mtop.damai.wireless.seat.queryseatstatus',
        'data': api_param
    }

    response = requests.get('https://mtop.damai.cn/h5/mtop.damai.wireless.seat.queryseatstatus/1.0/', params=params,
                            cookies=cookies, headers=headers)
    if response.status_code == 200:
        seat_data = json.loads(response.text)
        seat_data = seat_data.get('data')
        return seat_data


def create_seat_dict(detail, save_dict):
    """ 构建座位层级信息 """
    floor = detail.get('fn')
    row = detail.get('x')
    col = detail.get('y')
    sid = detail.get('sid')
    if floor not in save_dict:
        save_dict.update({floor: {}})
    if row not in save_dict.get(floor):
        save_dict[floor].update({row: {}})
    if col not in save_dict.get(floor).get(row):
        save_dict[floor][row].update({col: sid})


def format_valuable_seatid(all_seats_info, valuable_seats_info, price_id):
    """ 格式化 seatid 相关信息 """
    sid2coordinate = {}
    coordinate2sid = {}

    for detail in all_seats_info.get('seats'):
        create_seat_dict(detail, coordinate2sid)
        sid2coordinate.update({
            detail.get('sid'): {
                'sid': detail.get('sid'),
                'plid': detail.get('plid'),
                'fn': detail.get('fn'),
                'x': detail.get('x'),
                'y': detail.get('y')
            }})

    if 'noseat' in valuable_seats_info:
        # 去除不可用的座位信息
        noseat_data = valuable_seats_info.get('noseat')
        for line in noseat_data:
            sid = line.get('sid')
            floor = sid2coordinate.get(sid).get('floor')
            row = sid2coordinate.get(sid).get('row')
            col = sid2coordinate.get(sid).get('col')
            coordinate2sid[floor][row].pop(col)
        for line in coordinate2sid:
            if line.get('plid') != price_id:
                floor = line.get('fn')
                row = line.get('row')
                col = line.get('col')
                coordinate2sid[floor][row].pop(col)
        return coordinate2sid
    else:
        valuable_sid = {}
        seat_data = valuable_seats_info.get('seat')
        for line in seat_data:
            sid = line.get('sid')
            detail = sid2coordinate.get(sid)
            if detail.get('plid') == price_id:
                create_seat_dict(detail, valuable_sid)
        return valuable_sid


def pick_seat(valuable_seat, stand_id, buy_nums):
    """ 简单实现选取座位信息 """
    selected_seats = []
    for floor, floor_info in valuable_seat.items():
        for row, row_info in floor_info.items():
            for col, sid in row_info.items():
                selected_seats.append({'seatId': sid, 'standId': stand_id})
                if len(selected_seats) == buy_nums:
                    return selected_seats
