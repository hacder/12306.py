12306.py
========

一段简易的12306订票代码，部分变量需要用户手动设置，支持于2014年10月05日，运行在Ubuntu系统的python下面。<br>
流程解释：<br>
    默认预订20天后的票。订票顺序："硬卧","软卧","硬座"，其他的不予订购；车次为train中的顺序；乘客为passenger中的乘客；<br>

需要手动设置的变量说明：<br>
    TICKET=["硬卧","软卧","硬座",]  ，设置订票顺序<br>
    passenger=[["胡XX","421125XXXXXXXXXXXX","136XXXXXXXX","N"],["胡YY","421125XXXXXXXXXXXX","158XXXXXXXX","N"]]，乘车人信息，依次为“用户名，身份证，手机号，儿童票”<br>
    oldPassengerStr="胡XX,1,421125XXXXXXXXXXXX,1_胡YY,1,421125XXXXXXXXXXXX,1_"，乘车人信息，是否为老乘客，依次为“用户名，1，身份证，1_”<br>
    train=["1203","K133"]， 车次，按顺序购买<br>
    start="XZN"  起始站，从https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.809查询<br>
	  end="OSQ"    终点站，从https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.809查询<br>
    
    queryInterval=5  查询间隔<br>
    proxies = {}  代理，指HTTP代理<br>


