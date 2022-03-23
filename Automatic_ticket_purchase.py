# -*- coding: UTF-8 -*-
"""
__Author__ = "MakiNaruto"
__Version__ = "2.0.0"
__Description__ = ""
__Created__ = 2022/2/14 10:37 下午
"""

import re
import os
import json
import pickle
import platform
import argparse
from bs4 import BeautifulSoup
from requests import session
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class DaMaiTicket:
    def __init__(self):
        self.login_cookies = {}
        self.session = session()
        self.login_id = 'phone_number'
        self.login_password = 'password'
        self.item_id = 610820299671
        self.viewer = ['your_name']
        self.buy_nums = 1
        self.ticket_price = 180
        self.personal_title = '我的大麦-个人信息'
        self.damai_title = '大麦网-全球演出赛事官方购票平台-100%正品、先付先抢、在线选座！'

    def save_cookies(self):
        """ 保存cookies """
        with open('cookies.pkl', 'wb') as fw:
            pickle.dump(self.login_cookies, fw)

    def get_cookies(self):
        """ 读取保存的cookies """
        try:
            with open('cookies.pkl', 'rb') as fr:
                cookies = pickle.load(fr)
            self.login_cookies.update(cookies)
        except Exception as e:
            print('-' * 10, '加载cookies失败', '-' * 10)
            print(e)

    def check_login_status(self):
        """ 检测是否成功登录 """

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

        response = self.session.get('https://passport.damai.cn/accountinfo/myinfo',
                                    headers=headers,
                                    cookies=self.login_cookies)
        personal_info = BeautifulSoup(response.text, 'html.parser')
        if personal_info.title.text == self.personal_title:
            return True
        else:
            return False

    def account_login(self, login_type):
        """
        登录大麦网

        :param login_type:  选择哪种方式进行登录
        :return:
        """

        login_url = 'https://passport.damai.cn/login'
        option = webdriver.ChromeOptions()  # 默认Chrome浏览器
        # 关闭开发者模式, window.navigator.webdriver 控件检测到你是selenium进入，若关闭会导致出现滑块并无法进入。
        option.add_experimental_option('excludeSwitches', ['enable-automation'])
        option.add_argument('--disable-blink-features=AutomationControlled')
        option.add_argument('headless')               # Chrome以后台模式进行，注释以进行调试
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
            driver.find_element_by_name('fm-login-id').send_keys(self.login_id)
            driver.find_element_by_name('fm-login-password').send_keys(self.login_password)
            driver.find_element_by_class_name('password-login').send_keys(Keys.ENTER)
        else:
            WebDriverWait(driver, 180, 0.5).until(EC.title_contains(self.damai_title))

        for cookie in driver.get_cookies():
            self.login_cookies[cookie['name']] = cookie['value']

        return self.check_login_status()

    def get_api_param(self):
        """ 获取请求大麦API所必须的一些参数, 可能大麦网js代码更新后需要修改此函数内的代码以重新获得参数信息 """

        def format_param(context):
            param = []
            for line in context.split(','):
                k, v = line.split(':')
                param.append('"{}":{}'.format(k, v))
            param = json.loads('{' + ','.join(param) + '}')
            return param

        js_code_define = self.session.get(
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

    def step1_get_order_info(self, item_id, commodity_param, ticket_price=None):
        """
        获取点击购买所必须的参数信息

        :param item_id:             商品id
        :param commodity_param:     获取商品购买信息必须的参数
        :param ticket_price:        购买指定价位的票
        :return:
        """
        if not ticket_price:
            print('-' * 10, '票价未填写, 请选择票价', '-' * 10)
            return False

        commodity_param.update({'itemId': item_id})
        headers = {
            'authority': 'detail.damai.cn',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="98", "Google Chrome";v="98"',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
            'sec-ch-ua-platform': '"macOS"',
            'accept': '*/*',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-dest': 'script',
            'referer': 'https://detail.damai.cn/item.htm',
            'accept-language': 'zh,en;q=0.9,en-US;q=0.8,zh-CN;q=0.7',
        }

        response = self.session.get('https://detail.damai.cn/subpage', headers=headers, params=commodity_param)
        ticket_info = json.loads(response.text.replace('null(', '').replace('__jp0(', '')[:-1])
        all_ticket_sku = ticket_info['perform']['skuList']
        sku_id_sequence = 0
        sku_id = ''
        if ticket_price:
            for index, sku in enumerate(all_ticket_sku):
                if sku.get('price') and float(sku.get('price')) == float(ticket_price):
                    sku_id_sequence = index
                    sku_id = sku.get('skuId')
                    break
        return ticket_info, sku_id_sequence, sku_id

    def step2_click_buy_now(self, ex_params, sku_info):
        """
        点击立即购买

        :param ex_params:   点击立即购买按钮所发送请求的必须参数
        :param sku_info:    购买指定商品信息及数量信息
        :return:
        """

        headers = {
            'authority': 'buy.damai.cn',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'same-site',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'referer': 'https://detail.damai.cn/',
            'accept-language': 'zh,en;q=0.9,en-US;q=0.8,zh-CN;q=0.7'
        }
        params = {
            'exParams': json.dumps(ex_params),
            'buyParam': sku_info,
            'buyNow': 'true',
            'spm': 'a2oeg.project.projectinfo.dbuy'
        }

        response = self.session.get('https://buy.damai.cn/orderConfirm', headers=headers,
                                    params=params, cookies=self.login_cookies)
        result = re.search('window.__INIT_DATA__[\s\S]*?};', response.text)
        self.login_cookies.update(self.session.cookies)
        try:
            submit_order_info = json.loads(result.group().replace('window.__INIT_DATA__ = ', '')[:-1])
            submit_order_info.update({'output': json.loads(submit_order_info.get('output'))})
        except Exception as e:
            print('-' * 10, '获取购买必备参数异常，请重新解析response返回的参数', '-' * 10)
            print(result.group())
            return False
        return submit_order_info

    def step3_submit_order(self, submit_order_info, viewer):
        """
        提交订单所需参数信息

        :param submit_order_info:   最终确认订单所需的所有信息。
        :param viewer:  指定观演人进行购票
        :return:
        """
        headers = {
            'authority': 'buy.damai.cn',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="98", "Google Chrome";v="98"',
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json;charset=UTF-8',
            'x-requested-with': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.109 Safari/537.36',
            'sec-ch-ua-platform': '"macOS"',
            'origin': 'https://buy.damai.cn',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://buy.damai.cn/orderConfirm?',
            'accept-language': 'zh,en;q=0.9,en-US;q=0.8,zh-CN;q=0.7',
        }

        params = (
            ('feature', '{"returnUrl":"https://orders.damai.cn/orderDetail","serviceVersion":"1.8.5"}'),
            ('submitref', 'undefined'),
        )
        dm_viewer_pc = str([k for k, v in submit_order_info.get('data').items()])
        dm_viewer_pc_id = re.search('dmViewerPC_[0-9]*', dm_viewer_pc).group()
        if dm_viewer_pc_id:
            user_list = submit_order_info['data'][dm_viewer_pc_id]['fields']['dmViewerList']
            all_available_user = [name.get('viewerName') for name in user_list]
            if len(set(viewer).intersection(set(all_available_user))) != len(viewer):
                print('-' * 10, '请检查输入的观演人信息与大麦网观演人信息是否一致', '-' * 10)
                return False
            for user in user_list:
                if user.get('viewerName') in viewer:
                    user['isUsed'] = True

        submit_order_info = json.dumps(submit_order_info)
        response = self.session.post('https://buy.damai.cn/multi/trans/createOrder',
                                     headers=headers,
                                     params=params,
                                     data=submit_order_info,
                                     cookies=self.login_cookies)
        buy_status = json.loads(response.text)
        if buy_status.get('success') is True and buy_status.get('module').get('alipayOrderId'):
            print('-' * 10, '抢票成功, 请前往 大麦网->我的大麦->交易中心->订单管理 确认订单', '-' * 10)
            print('alipayOrderId: ', buy_status.get('module').get('alipayOrderId'))
            print('支付宝支付链接: ', buy_status.get('module').get('alipayWapCashierUrl'))

    def run(self):
        if len(self.viewer) != self.buy_nums:
            print('购买数量与实际观演人数量不符')
            return
        if os.path.exists('cookies.pkl'):
            self.get_cookies()
            login_status = self.check_login_status()
        else:
            if 'account' == args.mode.lower():
                login_status = self.account_login('account')
            else:
                login_status = self.account_login('qr')

        if login_status:
            self.save_cookies()
        else:
            print('-' * 10, '登录失败, 请检查登录账号信息', '-' * 10)
            return

        commodity_param, ex_params = self.get_api_param()

        buy_serial_number = ''
        while True:
            ticket_info, sku_id_sequence, sku_id = self.step1_get_order_info(self.item_id, commodity_param,
                                                                             ticket_price=self.ticket_price)
            ticket_sku_status = ticket_info['skuPagePcBuyBtn']['skuBtnList'][sku_id_sequence]['btnText']
            if ticket_sku_status == '即将开抢':
                continue
            elif ticket_sku_status == '缺货登记':
                print('-' * 10, '手慢了，该票价已经售空: ', ticket_sku_status, '-' * 10)
                return False
            elif ticket_sku_status == '立即购买':
                buy_serial_number = '{}_{}_{}'.format(self.item_id, self.buy_nums, sku_id)
                break

        if not buy_serial_number:
            print('-' * 10, '获取购票所需信息失败', '-' * 10)
            return
        submit_order_info = self.step2_click_buy_now(ex_params, buy_serial_number)
        self.step3_submit_order(submit_order_info, self.viewer)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='manual to this script')
    parser.add_argument('--mode', type=str, default='account', required=False,
                        help='account: account login， QR: Scan QR code login')
    args = parser.parse_args()
    a = DaMaiTicket()
    a.run()

