大麦网演唱会抢票程序---参考自github 作者：Oliver0047  地址：https://github.com/Oliver0047 
对该源码做了稍许修改,去掉了多余的依赖文件,直接修改代码里的购买页地址、关键人信息即可进行抢票。

## 准备工具
* Python3.6
* Selenium
* 本人用的chrome浏览器(可以改用火狐、IE等)，需要下载ChromeDriver包及配置  http://chromedriver.storage.googleapis.com/index.html 
* 自行寻找使用方法，这里不就不细述了。


最后成功测试运行时间：2019-05-08,方法太过于依赖页面源码的元素ID、xpath、class,导致大麦网页面更新后定位不到，会出现问题。若出现点击无效则自行替换相应的元素定位。
