##########################################
#   Author: Daisuke Otagiri
#   Course: EECS 113
#   Final Project - CIMIS.py file
#   Created: 8, June 2021
##########################################

from __future__ import print_function
import time
import urllib
import json
from urllib.request import urlopen
from datetime import datetime, timedelta

appKey = '370c79a6-a8bb-4c7b-8aea-9ba0cd1c7447'
target = 75 #station number for Irvine

class cimis_data:
    def __init__(self, date, hour, humidity):
        self.date = date 
        self.hour = hour
        self.humidity = humidity
    def get_date(self):
        return self.date
    def get_hour(self):
        return self.hour
    def get_humidity(self):
        return self.humidity

def get_cimis_data_for (current_hour):
    if current_hour == 0 or current_hour > time.localtime(time.time()).tm_hour:
        date = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')
    else:
        date = datetime.now().strftime('%Y-%m-%d')

    data = run_cimis(appKey, target, date, date)

    if data is None:
        return None
    d = cimis_data( data[current_hour-1]['Date'],     
                    data[current_hour-1]['Hour'], 
                    data[current_hour-1]['HlyRelHum']['Value']
                   )
    return d
    
def retrieve_cimis_data(url, target):
    try:
        content = urlopen(url).read().decode('utf-8')        
        assert(content is not None)
        return json.loads(content)
    except urllib.error.HTTPError as e:
        print("Could not resolve the http request at this time")
        error_msg = e.read()
        print(error_msg)
        return None
    except urllib.error.URLError:
        print('Could not access the CIMIS database.Verify that you have an active internet connection and try again.')
        return None
    except: #json.decoder.JSONDecodeError:  #ConnectionResetError:
        print("CMIS request was rejected")
        return None
 
def run_cimis(appKey, target, start, end):
    ItemList = ['hly-rel-hum']

    dataItems = ','.join(ItemList)
    
    url = ('http://et.water.ca.gov/api/data?appKey=' + appKey + '&targets='
            + str(target) + '&startDate=' + start + '&endDate=' + end +
            '&dataItems=' + dataItems)
            
    data = retrieve_cimis_data(url, target)
    if(data is None):
        return None    
    else:
        return data['Data']['Providers'][0]['Records']
