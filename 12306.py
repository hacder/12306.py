# -*- coding: utf-8 -*- 
import re
import mechanize
import Image
import sys
from getpass import getpass
import time
import datetime
import json
import urllib
import traceback

def spark_input(msg, isPassword=False):
	while True:
		try:
			if isPassword:
				return getpass(msg)
			else:
				return raw_input(msg)
		except KeyboardInterrupt:
			msg=msg.replace("==>", "   ")
			print

def spark_get_passcode(msg, isLogin=True):
	login_passcode_url="https://kyfw.12306.cn/otn/passcodeNew/getPassCodeNew?module=login&rand=sjrand"
	passenger_passcode_url="https://kyfw.12306.cn/otn/passcodeNew/getPassCodeNew?module=passenger&rand=randp"
	if isLogin:
		url_passcode=login_passcode_url
	else:
		url_passcode=passenger_passcode_url
	while True:
		try:
			f = br.retrieve( url_passcode )[0]
			image = Image.open(f)
			image.show()
			return raw_input(msg)
		except KeyboardInterrupt:
			msg=msg.replace("==>", "   ")
			print
		except IOError:
			msg=msg.replace("==>", "   ")

def GetValualeByName(name,data,mode='notnull'):
	regstr="'"+name+"':'{0,1}([^'^,]+)'{0,1}"
	f=re.findall(regstr,data)
	j=''
	i=''
	for i in f:
		if mode=='notnull' and i != 'null':
			return i
		if mode == 'max' and i != 'null':
			if len(i)>len(j):
				j=i
		
	if len(j)>0:
		return j
	return i

def spark_log(msg):
	print "log:\033[31m%s\033[0m" % msg

def login():
	passcode=None
	url_check_logincode='https://kyfw.12306.cn/otn/passcodeNew/checkRandCodeAnsyn'
	url_login="https://kyfw.12306.cn/otn/login/loginAysnSuggest"
	url_login2="https://kyfw.12306.cn/otn/login/userLogin"
	### Login
	
	while True:
		### Check Login Code
		tParam={}
		while True:
			passcode=spark_get_passcode("==>验证码：")
			tParam["rand"]="sjrand"
			tParam["randCode"]=passcode
			params = urllib.urlencode( tParam )
			resp = br.open(url_check_logincode, params).read()
			jResp=json.loads(resp)
			if jResp['data'] == 'Y':
				print '验证码正确'
				break
			else:
				print '验证码错误'
		tParam={}
		username=spark_input("==>登录名：")
		password=spark_input("==>密码：", True)
		tParam["loginUserDTO.user_name"]=username
		tParam["userDTO.password"]=password
		tParam["randCode"]=passcode
		params = urllib.urlencode( tParam )
		f = br.open(url_login, params)
		resp=f.read()
		jResp=json.loads(resp)
		if  jResp.has_key('data') and len(jResp['data']) > 0:
			print "登录成功!!"
			break
		else:
			print jResp["messages"][0]
	tParam={}
	tParam["_json_att"]=""
	params = urllib.urlencode( tParam )
	f = br.open(url_login2, params)
	resp=f.read()

#============================================================================================================

gFlag=[]
gData=[]
FLAG_YW=1
FLAG_RW=1<<1
FLAG_YZ=1<<2
FLAG_RZ=1<<3
FLAG_ZE=1<<4
FLAG_ZY=1<<5

def checkState(t,s):
	if t[s] == u"有":
		return True
	if t[s] == "--":
		return False
	if t[s] == "*":
		return False
	if t[s] == u"无":
		return False
	if t[s].isnumeric():
		return True
	return False

def haveNeededTicket(t):
	TicketRule=0
	if checkState(t,"yw_num"):
		TicketRule|=FLAG_YW
	if checkState(t,"ze_num"):
		TicketRule|=FLAG_ZE
	if checkState(t,"rw_num"):
		TicketRule|=FLAG_RW
	if checkState(t,"yz_num"):
		TicketRule|=FLAG_YZ
	if TicketRule !=0:
		gFlag.append(TicketRule)
		return True
	return False

def queryLeftTicket():
	del gData[:]
	url_query="https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date=%s&leftTicketDTO.from_station=%s&leftTicketDTO.to_station=%s&purpose_codes=ADULT"
	queryUrl=url_query % (date, start, end)
	queryFlag=True
	while queryFlag:
		try:
			result = br.open(queryUrl).read()
			temp = json.loads(result)
		except:
			time.sleep(queryInterval)
			continue
		####
		print "\033[32m% 4s   % 3s   % 3s   % 4s   % 3s   % 3s   % 3s   % 3s   % 3s   % 3s   % 3s   % 3s   % 3s   % 3s   % 3s\033[0m" % \
			(u"车次",u"出发站",u"到达站",u"历时",u"商务座",u"特等座",u"一等座",u"二等座",u"软卧",u"硬卧",u"软座",u"硬座",u"无座",u"其他",u"备注")
		if not temp.has_key("data"):
			try:
				print temp["messages"][0]
			except KeyError:
				pass
			time.sleep(queryInterval)
			continue
		###
		for d in temp["data"]:
			t=d["queryLeftNewDTO"]
			print "% 6s   % 3s   % 3s   % 6s   % 6s   % 6s   % 6s   % 6s   % 4s   % 4s   % 4s   % 4s   % 4s   % 4s   % 4s" % \
				(t["station_train_code"], 
					t["from_station_name"],
					t["to_station_name"],
					t["lishi"],
					t["swz_num"],t["tz_num"],
					t["zy_num"],t["ze_num"],
					t["rw_num"],t["yw_num"],
					t["rz_num"],t["yz_num"],
					t["wz_num"],t["qt_num"],
					d["buttonTextInfo"])
			###
			if t["canWebBuy"] != 'Y':
				time.sleep(queryInterval)
				continue
			if not haveNeededTicket(t):
				time.sleep(queryInterval)
				continue
			queryFlag=False
			gData.append(d)

#============================================================================================================
orderFlag=0
orderSeatFlag=0
def doPreOrder():
	url_checkUser="https://kyfw.12306.cn:443/otn/login/checkUser"
	url_submitOrderRequest="https://kyfw.12306.cn:443/otn/leftTicket/submitOrderRequest"
	###
	tParam={}
	tParam["_json_att"]=""
	params = urllib.urlencode( tParam )
	f = br.open(url_checkUser, params)
	resp=f.read()
	spark_log(resp)
	###
	print "orderFlag = ", orderFlag
	tParam={}
	tParam["secretStr"]=gData[orderFlag]["secretStr"].replace('%2B','+')
	tParam["train_date"]=date
	tParam["back_train_date"]=today
	tParam["tour_flag"]="dc"
	tParam["purpose_codes"]="ADULT"
	tParam["query_from_station_name"]=gData[orderFlag]["queryLeftNewDTO"]["from_station_name"]
	tParam["query_to_station_name"]=gData[orderFlag]["queryLeftNewDTO"]["to_station_name"]
	tParam["undefined"]=""
	params = urllib.urlencode( tParam )
	while True:
		try:
			f = br.open(url_submitOrderRequest, params)
			resp=f.read()
			spark_log(resp)
			jResp=json.loads(resp)
			if  jResp.has_key('status') and jResp['status'] == False:
				print resp
				return False
			break
		except:
			print "submitOrderRequest Exception"
			time.sleep(5)
			continue
	return True

def doOrder():
	url_initDc="https://kyfw.12306.cn/otn/confirmPassenger/initDc"
	url_checkRandCodeAnsyn="https://kyfw.12306.cn:443/otn/passcodeNew/checkRandCodeAnsyn"
	url_checkOrderInfo="https://kyfw.12306.cn:443/otn/confirmPassenger/checkOrderInfo"
	url_getQueueCount="https://kyfw.12306.cn/otn/confirmPassenger/getQueueCount"
	url_confirmSingleForQueue="https://kyfw.12306.cn:443/otn/confirmPassenger/confirmSingleForQueue"
	###
	tParam={}
	tParam["_json_att"]=""
	params = urllib.urlencode( tParam )
	f = br.open(url_initDc, params)
	resp=f.read()
	repeatsubmitToken=re.findall("var globalRepeatSubmitToken = '([a-z0-9]+)';",resp)
	leftTicketStr=GetValualeByName('leftTicketStr',resp)
	key_check_isChange=GetValualeByName('key_check_isChange',resp)
	train_location=GetValualeByName('train_location',resp)
	###
	orderSeatFlag = 0
	tParam={}
	tParam["cancel_flag"]="2"
	tParam["bed_level_order_num"]="000000000000000000000000000000"
	tParam["oldPassengerStr"]=oldPassengerStr
	tParam["tour_flag"]="dc"
	tParam["_json_att"]=""
	tParam["REPEAT_SUBMIT_TOKEN"]=repeatsubmitToken[0]
	orderSeatFlag=-1
	while True:
		if orderSeatFlag == len(passengerTicketStr):
			break
		else:
			orderSeatFlag+=1;
			orderSeatFlag%=len(passengerTicketStr)
			time.sleep(2)
		print "------>尝试订购 %s %s票" % (gData[orderFlag]["queryLeftNewDTO"]["station_train_code"],TICKET[orderSeatFlag])
		#passcode=spark_get_passcode("==>验证码：",False)
		while True:
			passcode=spark_get_passcode("==>验证码：",False)
			tParam["REPEAT_SUBMIT_TOKEN"]=repeatsubmitToken[0]
			tParam["_json_att"]=""
			tParam["rand"]="randp"
			tParam["randCode"]=passcode
			params = urllib.urlencode( tParam )
			resp = br.open(url_checkRandCodeAnsyn, params).read()
			jResp=json.loads(resp)
			if jResp['data'] == 'Y':
				print '验证码正确'
				break
			else:
				print '验证码错误'
		tParam["randCode"]=passcode
		###
		tParam["passengerTicketStr"]=passengerTicketStr[orderSeatFlag]
		params = urllib.urlencode( tParam )
		f = br.open(url_checkOrderInfo, params)
		resp=f.read()
		jResp=json.loads(resp)
		if jResp.has_key('data') and jResp['data'].has_key('submitStatus') and len(jResp['messages'])==0:
			print '准备提交订单'
		else:
			print jResp['messages'][0]
			continue
		### TODO
		t2=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
		t3={1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
		tParam={}
		tParam["train_date"]="%s %s %d %d 00:00:00 GMT+0800 (HKT)" % (t2[odate.weekday()], t3[odate.month], odate.day, odate.year)
		tParam["train_no"]=gData[orderFlag]["queryLeftNewDTO"]["train_no"]
		tParam["stationTrainCode"]=gData[orderFlag]["queryLeftNewDTO"]["station_train_code"]
		tParam["seatType"]=passengerTicketStr[orderSeatFlag][0:1]
		tParam["fromStationTelecode"]=gData[orderFlag]["queryLeftNewDTO"]["from_station_telecode"]
		tParam["toStationTelecode"]=gData[orderFlag]["queryLeftNewDTO"]["to_station_telecode"]
		tParam["leftTicket"]=leftTicketStr[0]
		tParam["purpose_codes"]="00"
		tParam["_json_att"]=""
		tParam["REPEAT_SUBMIT_TOKEN"]=repeatsubmitToken[0]
		params = urllib.urlencode( tParam )
		f = br.open(url_getQueueCount, params)
		resp=f.read()
		jResp=json.loads(resp)
		if 	jResp.has_key('data') and jResp['data'].has_key('op_1') and jResp.has_key('messages') and len(jResp['messages'])==0:
			leftTicketStr=jResp['data']['ticket']
		else:
			print resp
			continue
		###
		tParam={}
		tParam["passengerTicketStr"]=passengerTicketStr[orderSeatFlag]
		tParam["oldPassengerStr"]=oldPassengerStr
		tParam["randCode"]=passcode
		tParam["purpose_codes"]="00"
		tParam["key_check_isChange"]=key_check_isChange
		tParam["leftTicketStr"]=leftTicketStr
		tParam["train_location"]=train_location
		tParam["_json_att"]=""
		tParam["REPEAT_SUBMIT_TOKEN"]=repeatsubmitToken[0]
		params = urllib.urlencode( tParam )
		f = br.open(url_confirmSingleForQueue, params)
		resp=f.read()
		jResp=json.loads(resp)
		if jResp['status'] == False:
			print "Validate Message Failed!!!"
			continue
		elif jResp.has_key('data') and jResp['data'].has_key('errMsg') and len(jResp['data']['errMsg'] )>0 :
			print jResp['data']['errMsg']
			continue
		else:
			ret = GetOrderID(repeatsubmitToken[0])
			if ret == 1:
				print 'Error'
				return 1
			GetOrderID(repeatsubmitToken[0])
			break

def GetOrderID(tokenstr):
	i=0
	while True:
		timenow=time.time()*1000
		timestr='%f'%timenow
		randstr=timestr.split('.')[0]
		url='https://kyfw.12306.cn/otn/confirmPassenger/queryOrderWaitTime?random='+randstr+'&tourFlag=dc&_json_att=&REPEAT_SUBMIT_TOKEN='+tokenstr
		f = br.open(url)
		resp=f.read()
		jResp=json.loads(resp)
		#print j
		if jResp.has_key('data') and jResp['data'].has_key('orderId') and jResp['data']['orderId']:
			print 'OrderTicket OK.. orderId = :', jResp['data']['orderId']
			return 0
		else:
			print 'Wait for ORderid :'
			print resp
			#print jResp['data']['msg']
			time.sleep(5)
			i=i+1
			if  i>2:
				return 1
			
	return 1

def sortTrain():
	tmp = list(gData)
	del gData[:]
	for t in train:
		for k in tmp:
			if t==k["queryLeftNewDTO"]["station_train_code"]:
				gData.append(k)
	pass

if __name__ == "__main__":
	reload(sys)
	sys.setdefaultencoding('utf8')
	#ua='Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'
	ua="Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36"
	br = mechanize.Browser()
	br.addheaders = [('User-agent', ua)]
	print "==============================================="
	print "按提示输入，按Ctrl+C重新输入，按Ctrl+D退出输入"
	print "==============================================="
	print "------------------- init ----------------------"
	station_js="https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.809"
	queryInterval=5
	proxies = {}
	###  user infomation : User, ID, PhoneNumber, isChild
	passenger=[["胡XX","421125XXXXXXXXXXXX","136XXXXXXXX","N"],["胡YY","421125XXXXXXXXXXXX","158XXXXXXXX","N"]]
	oldPassengerStr="胡XX,1,421125XXXXXXXXXXXX,1_胡YY,1,421125XXXXXXXXXXXX,1_"
	TICKET=["硬卧","软卧","硬座",]
	passengerTicketStr=[]
	JS_FLAG_YW=3
	JS_FLAG_YZ=1
	JS_FLAG_RW=4
	for flag in (JS_FLAG_YW,JS_FLAG_RW,JS_FLAG_YZ):
		temp = ""
		for p in passenger:
			temp += "%d,0,1,%s,1,%s,%s,%s_" % (flag, p[0],p[1],p[2],p[3])
		temp = temp[:-1]
		passengerTicketStr.append(temp)
	#train=["K585","K835"]
	train=["1203","K133"]
	start="XZN"  #浠水
	end="OSQ"    #深圳西
	today= time.strftime('%Y-%m-%d',time.localtime(time.time()))
	odate = datetime.datetime.now() + datetime.timedelta(days=19) 
	#odate = datetime.datetime.now() + datetime.timedelta(days=18) 
	date = odate.strftime('%Y-%m-%d')
	# temp = br.open(station_js)
	# st=temp.read()
	# st=st[20:-2]
	whileFlag=True
	while whileFlag:
		try:
			print "------------------- login ----------------------"
			login()
			print "------------- query Left Ticket ----------------"
			while whileFlag:
				try:
					queryLeftTicket()
					sortTrain()
					print "------------- Pre Order Ticket ----------------"
					if doPreOrder():
						print "--------------- Order Ticket ------------------"
						doOrder()
					whileFlag = False
				except KeyboardInterrupt, e:
					continue
		except KeyboardInterrupt, e:
			continue
