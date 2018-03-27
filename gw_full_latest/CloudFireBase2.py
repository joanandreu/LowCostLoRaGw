----------------------------------------------------------------------------
# Copyright 2018 NOWDATA
# 


import urllib2
import socket
import time
import datetime
import ssl
import sys

# get key definition from external file to ease
# update of cloud script in the future
import key_FireBase

try:
	key_FireBase.source_list
except AttributeError:
	key_FireBase.source_list=[]

# didn't get a response from firebase server?
connection_failure = False

# function to check connection availability with the server
def test_network_available():
	connection = False
	iteration = 0
	response = None
	
	# we try 4 times to connect to the server.
	while(not connection and iteration < 4) :
		try:
	    	# 3sec timeout in case of server available but overcrowded
			response=urllib2.urlopen('https://www.firebase.com/', timeout=3)
			connection = True
		except urllib2.URLError, e: pass
		except socket.timeout: pass
		except ssl.SSLError: pass
			
		# if connection_failure == True and the connection with the server is unavailable, don't waste more time, exit directly
		if(connection_failure and response is None) :
			print('FireBase: the server is still unavailable')
			iteration = 4
		# print connection failure
		elif(response is None) :
			print('FireBase: server unavailable, retrying to connect soon...')
			# wait before retrying
			time.sleep(1)
			iteration += 1
		    		
	return connection
	
# msg is already in JSON format
def send_data(msg, path, msg_entry):
	from firebase import firebase
	global _db_firebase
	_db_firebase = firebase.FirebaseApplication(key_FireBase.firebase_database, None)
				
	try:
		result = _db_firebase.put(path, msg_entry, msg)	
		#fbase = firebase(path)
		#fbase.push(msg)
	except Exception as e:
		print("FireBase: can not send the data to the server:" + str(e))
		print("FireBase: not uploading")
		return "exception"
		
	
def firebase_uploadSingleData(msg, sensor, msg_entry, date):
	global connection_failure
	
	# test if network is available before sending to the server
	connected = test_network_available()
	
	# if we got a response from the server, send the data to it	
	if(connected) :
		print("FireBase: uploading")
		#send_to = date.date().isoformat()+'/'+sensor
		send_to = sensor
		#time.sleep(10)
		str_result = send_data(msg, send_to, msg_entry)
		
		#exception while sending data, probably a disconnection error
		if(str_result == "exception"):
			connection_failure = True
		else:
			connection_failure = False
			print "Firebase: upload success"
			
	else:
		print("FireBase: not uploading")
		connection_failure = True

# main
# -------------------

def main(ldata, pdata, rdata, tdata, gwid):


	now = datetime.datetime.utcnow()
		
	# this is common code to process packet information provided by the main gateway script (i.e. post_processing_gw.py)
	# these information are provided in case you need them	
	arr = map(int,pdata.split(','))
	dst=arr[0]
	ptype=arr[1]				
	src=arr[2]
	seq=arr[3]
	datalen=arr[4]
	SNR=arr[5]
	RSSI=arr[6]
	
	arr = map(int,rdata.split(','))
	bw=arr[0]
	cr=arr[1]
	sf=arr[2]

	#LoRaWAN packet
	if dst==256:
		src_str="%0.8X" % src
	else:
		src_str=str(src)	

	if (src_str in key_FireBase.source_list) or (len(key_FireBase.source_list)==0):
	
		#LoRaWAN packet
		if dst==256:
			#here we only take the last 8 bits
			src = src & 0x000000FF
	
		firebase_msg = {
			'time':now.isoformat(),		
			'type':ptype,
			'gateway_eui' : gwid,					
			'node_eui':src,
			'seq':seq,
			'len':datalen,
			'snr':SNR,
			'rssi':RSSI,
			'cr' : cr, 
			'datarate' : "SF"+str(sf)+"BW"+str(bw),
			'data':ldata
		}
		
		sensor_entry='sensor'+src_str
		msg_entry='nowdata%d' % 0
		
	
		#upload data to firebase
		firebase_uploadSingleData(firebase_msg, sensor_entry, msg_entry, now)
	else:
		print "Source is not is source list, not sending with CloudFireBase.py"		

if __name__ == "__main__":
	main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])	
