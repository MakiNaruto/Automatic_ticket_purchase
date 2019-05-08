# -*- coding: utf-8 -*-

import os
import re
import time
import pickle
from tkinter import *
from time import sleep
from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


#大麦网主页
damai_url="https://www.damai.cn/"
#登录页
login_url="https://passport.damai.cn/login?ru=https%3A%2F%2Fwww.damai.cn%2F"
#抢票目标页
target_url="https://detail.damai.cn/item.htm?spm=a2oeg.search_category.0.0.71254d153q9EDX&id=590449968855&clicktitle=%E7%9B%B4%E5%88%B0%E4%B8%96%E7%95%8C%E5%B0%BD%E5%A4%B4-8090%E7%BB%8F%E5%85%B8%E5%8A%A8%E6%BC%AB%E6%BC%94%E5%94%B1%E4%BC%9A%E4%B8%8A%E6%B5%B7%E7%AB%99"

name = "your_name"
phone = "your_PhoneNumber"

class Concert(object):
    def __init__(self):

        self.status = 0         #状态,表示如今进行到何种程度
        self.login_method = 1   #{0:模拟登录,1:Cookie登录}自行选择登录方式
        
    def set_cookie(self):
       self.driver.get(damai_url)
       print("###请点击登录###")
       while self.driver.title.find('大麦网-全球演出赛事官方购票平台')!=-1:
           sleep(1)
       print("###请扫码登录###")
       while self.driver.title=='中文登录':
           sleep(1)
       print("###扫码成功###")
       pickle.dump(self.driver.get_cookies(), open("cookies.pkl", "wb")) 
       print("###Cookie保存成功###")
       self.driver.get(target_url) 

    def get_cookie(self):
        try:
            cookies = pickle.load(open("cookies.pkl", "rb"))#载入cookie
            for cookie in cookies:
                cookie_dict = {
                    'domain':'.damai.cn',#必须有，不然就是假登录
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    "expires": "",
                    'path': '/',
                    'httpOnly': False,
                    'HostOnly': False,
                    'Secure': False}
                self.driver.add_cookie(cookie_dict)
            print('###载入Cookie###')
        except Exception as e:
            print(e)
            
    def login(self):
        if self.login_method==0:
            self.driver.get(login_url)                                #载入登录界面
            print('###开始登录###')

        elif self.login_method==1:            
            if not os.path.exists('cookies.pkl'):                     #如果不存在cookie.pkl,就获取一下
                self.set_cookie()
            else:
                self.driver.get(target_url)
                self.get_cookie()
    
     
    def enter_concert(self):
        print('###打开浏览器，进入大麦网###') 
        self.driver = webdriver.Chrome()        #默认Chrome浏览器
        # self.driver.maximize_window()           #最大化窗口
        self.login()                            #先登录再说
        self.driver.refresh()                   #刷新页面
        self.status = 2                         #登录成功标识
        print("###登录成功###")

    def choose_ticket(self):
        if self.status == 2:                  #登录成功入口
            self.num = 1                      #第一次尝试

            print("="*30)
            print("###开始进行日期及票价选择###")
            while self.driver.title.find('确认订单') == -1:           #如果跳转到了订单结算界面就算这步成功了，否则继续执行此步
                
                # self.driver.find_elements_by_xpath('//html//body//div[@class = "perform__order__price"]//div[2]//div//div//a[2]')[0].click()   #购票数+1(若需要)

                cart = self.driver.find_element_by_class_name('perform')   #获得选票界面的表单值

                # try:各种按钮的点击,
                buybutton = self.driver.find_element_by_class_name('buybtn').text
                try:
                    buybutton = self.driver.find_element_by_class_name('buybtn').text

                    if buybutton == "立即预定":
                        self.driver.find_element_by_class_name('buybtn').click()
                        self.status = 3
                        self.num = 1
                    elif buybutton == "立即购买":
                        self.driver.find_element_by_class_name('buybtn').click()
                        self.status = 4
                    elif buybutton == "选座购买":
                        self.driver.find_element_by_class_name('buybtn').click()
                        self.status = 5

                    elif buybutton == "提交缺货登记":
                        print('###抢票失败，请手动提交缺货登记###')  
                        break

                    print("###跳转到订单结算界面###")

                except:
                    print('###未跳转到订单结算界面###')
                
                title = self.driver.title
                if title !="确认订单" :                                     #如果前一次失败了，那就刷新界面重新开始
                    self.status=2
                    self.driver.get(damai_url)
                    
            self.check_order()


    def check_order(self):
        if self.status in [3,4,5]:
            print('###开始确认订单###')
            print('###默认购票人信息###')
            try:
                #姓名和电话的填写，这是绝对路径，由于大麦网目标页会更新，出现问题修改xpath即可
                self.driver.find_elements_by_xpath('//div[@class = "w1200"]//div[@class = "delivery-form"]//div[1]//div[2]//span//input')[0].send_keys(name)
                self.driver.find_elements_by_xpath('//div[@class = "w1200"]//div[@class = "delivery-form"]//div[2]//div[2]//span[2]//input')[0].send_keys(phone)
            except Exception as e:
                print("###填写确认订单信息时，联系人手机号填写失败###")
                print(e)
            try:
                #默认选第一个购票人信息
                self.driver.find_elements_by_xpath('//div[@class = "w1200"]//div[@class = "ticket-buyer-select"]//div//div[1]//span//input')[0].click()  #观影人1
                #选第二个购票人信息(若购买多张票时需要开启此选项，增加购票人信息)
                # self.driver.find_elements_by_xpath('//div[@class = "w1200"]//div[@class = "ticket-buyer-select"]//div//div[2]//span//input')[0].click()  #观影人2
           
            except Exception as e:
                print("###购票人信息选中失败，自行查看元素位置###")
                print(e)

            print('###不选择订单优惠###')
            print('###请在付款完成后下载大麦APP进入订单详情页申请开具###')

            # 最后一步提交订单

            time.sleep(1)       # 太快会影响加载，导致按钮点击无效
            self.driver.find_elements_by_xpath('//div[@class = "w1200"]//div[2]//div//div[9]//button[1]')[0].click()

            try:
                element = WebDriverWait(self.driver, 5).until(EC.title_contains('支付宝 - 网上支付 安全快速！'))
                self.status=6
                print('###成功提交订单,请手动支付###')
            except:
                print('###提交订单失败,请查看问题###')

if __name__ == '__main__':
    try:
        con = Concert()             #具体如果填写请查看类中的初始化函数
        con.enter_concert()
        con.choose_ticket()

    except Exception as e:
        print(e)
        # con.finish()
