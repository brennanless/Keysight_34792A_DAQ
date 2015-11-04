# -*- coding: utf-8 -*-
"""
Created on Wed Oct 14 13:19:01 2015

@author: brennanless
"""

#This script is designed to run once every 24-hours. It logs onto the 34792A unit, queries it for
#any errors that have occurred, and then writes the errors to file with format
#"YYYY-MM-DD_ErrorMessagest.txt"
#It is designed to try to execute once per mintue for ten minutes. Then it will quit, send an 
#error email to me, and try again the next day. 

import datetime
import visa
import os
import sys
import time

#path = '/Users/brennanless/GoogleDrive/Attics_CEC/ErrorLogFiles/'
path = '/home/bdless/ErrorLogFiles/' #file path for smap-src Linux machine
os.chdir(path)

#Constructs the visa address outside of the loop, given an IP address. 
str1 = 'TCPIP0::'
ip_adr = '128.3.22.197' #IP address of the 34792A
str2 = '::inst0::INSTR'
visa_path = str1 + ip_adr + str2

index = 0

for attempt in range(10):
    
    if index == 0:
        
        try:
        
            #Connect to the 34792A by creating resource manager and LAN connection via IP
            rm = visa.ResourceManager() #creates VISA resource manager
            
            #Set of Keysight instruments connected via ethernet to BeagleBone. Use other VISA formats for other connectino types. 
            #my_instrument1 = rm.open_resource('TCPIP0::128.3.22.14::inst0::INSTR') #Connects to the instrument
            my_instrument1 = rm.open_resource(visa_path) #Connects to the instrument
            #my_instrument2 = rm.open_resource('TCPIP0::aaa.b.cc.ddd::inst0::INSTR') #Connects to the instrument 2
            #my_instrument3 = rm.open_resource('TCPIP0::aaa.b.cc.ddd::inst0::INSTR') #Connects to the instrument 3
            
            inst_idn = my_instrument1.query("*IDN?").split(",")[2] #Retrieves the instrument number

            cpu_time = datetime.date.today().isoformat() #string containing iso date from today
            local_file = cpu_time + "_ErrorMessages.txt" #creates error log file name
            local_filename = os.path.join(path, local_file) #sets file path
            lf = open(local_filename, "wb") #open file
            
            while True:
                string = my_instrument1.query("system:error?").encode('ascii', 'ignore')
                #this queries the instrument, until it returns the message that no more errors
                #have been logged (+0,"No error"\n). 
                if string[1] == "0": #checks for the 0 value, indicating no more errors.
                #if str[0][1] == "0":
                    break
                else:
                    lf.write(string) #writes error code to file   
                    #err_message.append(string)
                    
            lf.close()
            my_instrument1.close() #close the instrument
            rm.close() #close the resource manager
            index = 1
        except: #if any exception is thrown in the above lines, code will wait and re-execute in 60 secs, 10 times total
            print "An error occurred, will try again in 60 seconds."
            time.sleep(60)
            index = 0
            continue
    else:
        break   
    