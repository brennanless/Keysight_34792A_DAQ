# -*- coding: utf-8 -*-
"""
Created on Wed Oct  7 15:05:17 2015

@author: brennanless
"""
#This script is designed to retrieve all formatted data files from the Keysight 34792A mass storage USB device,
#via FTP. All files will be transferred that are not already located on the local machine's data directory. 
#Script is designed to handle temporary network outages (<10 min), as well as power outages. 


import datetime
import visa
import os
import sys
from ftplib import FTP
import time
import re
import smtplib

def date_string_to_int(string): 
    string_split = string.split("_")
    string_merge = string_split[0] + string_split[1]
    string_list = []
    string_list.append(string_merge)
    return map(int, string_list)
    
def date_string_to_mins(string):
    string_split = string.split("_")
    string_hour = string_split[1][0:2]
    string_min = string_split[1][2:4]
    string_list_hour = []
    string_list_min = []
    string_list_hour.append(string_hour)
    string_list_min.append(string_min)
    return 60 * map(int, string_list_hour)[0] + map(int, string_list_min)[0]
    
def last_scan_string_to_int(string):
    string_split = string.split(",")
    string_merge = string_split[0] +string_split[1] +string_split[2] +string_split[3] +string_split[4] + string_split[5].split(".")[0] + string_split[5].split(".")[1]
    string_list = []
    string_list.append(string_merge)
    return map(int, string_list)
    
def datafile_string_to_int(string):
    string_split = string.split("_")
    string_merge = string_split[0] + string_split[1]
    string_list = []
    string_list.append(string_merge)
    return map(int, string_list)    
    
def parse_directory_str(string):
    return string.split(" ")[len(string.split(" ")) - 1]
    
#lists the integer values for the directories on the USB drive.  

#Find the last data file of the local file system
#Local file system must include only files with format of 34792A datafiles.
def last_data_file(local_fileList):
    datafile_int_list = []  
    for i in local_fileList:
        if i == '.DS_Store':
            continue
        else:
            datafile_int = datafile_string_to_int(i)
            datafile_int_list.append(datafile_int)
    return max(datafile_int_list)

#server = smtplib.SMTP("aspmx.l.google.com", 25)

#setting directory path for output files. Change to BBB
path = '/Users/brennanless/GoogleDrive/Attics_CEC/TestDataFiles'
#path = '/home/bdless/data' #file path for smap-src Linux machine
os.chdir(path) #sets wd to path string

#tested this loop against failed network connection (unplugged ethernet from 34792A for 2min)
#tested against last scan file already existing on local file system
 
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
            
            print "Connected to instrument"
            
            #last_scan_time = last_scan_string_to_int(my_instrument1.query("syst:time:scan?")) #returns time last scan began
            last_scan_time = my_instrument1.query("syst:time:scan?").encode('ascii', 'ignore').split(",")
            last_scan_time_minutes = 60 * int(last_scan_time[3]) + int(last_scan_time[4])
            cpu_time_minutes = 60 * datetime.datetime.now().hour + datetime.datetime.now().minute
            
            if (cpu_time_minutes - last_scan_time_minutes) > 120:
                print "It has been more than an hour since the last scan" 
                #Send email  
#                try:
#                    my_instrument1.write("abort")
#                    my_instrument1.write("init") 
#                except:
#                    break            
            
            print "Performed timing calculations."
            
            my_instrument1.write("abort")
            my_instrument1.write("init")  
            
            print "sent init and abort commands"          
            
            inst_idn = my_instrument1.query("*IDN?").split(",")[2] #Retrieves the instrument number
            mmem_path = "/DATA/" + inst_idn + "/" #Creates the file path on the USB drive
            local_fileList = os.listdir(path) #lists the files on the local directory
            
            print "got instrument id and file paths"
            
            #FTP into the 34792A  
            try:
                ftp = FTP(ip_adr)
            except:
                my_instrument1.write("DIAG:SEC FTP,ON") #After unit loses power, this commend needs 
                #to be reissued for some reason...
                ftp = FTP(ip_adr)
            ftp.login()
            
            print "successful FTP logon"
            
            ftp.cwd(mmem_path) #naviagate to the file path containing scan directories
            fileList = [] 
            ftp.retrlines("LIST", fileList.append) #list the directories on the USB in mmem_path
            fileList_ints = [] 
            for i in fileList: #turn directory dates into integers
                dir_name = parse_directory_str(i)
                dir_int = date_string_to_int(dir_name)
                fileList_ints.append(dir_int)
                
            print "created file list of integers"
                	
            try: #calculates largest value for current data files on local directory
                max_data_file = last_data_file(local_fileList) 
            except ValueError: #if no files are in directory, set max to 0
                max_data_file = [0]
                #continue
            print "max_data_file set to 0"
            
            #last_file_time = date_string_to_mins(fileList[len(fileList)-1]) #time value of the latest file on the USB, for comparison to last_scan_time 
#            if (last_scan_time[0] - fileList_ints[len(fileList_ints)-1][0]) < 10000:
#                my_instrument1.write("init")                
#            if cpu_time - last_file_time > 120:
#                Send Email
#                break
#            else:
#                continue
            data_files_to_get = []    
            for i in range(len(fileList_ints)): #Boolean values indicating if files on USB are later than the lates file on the local drive
                data_files_to_get.append(max_data_file[0] >= fileList_ints[i][0])
                
            print "got boolean values indicating which files to get"
                
            fileList_to_get = []              
            for i in range(len(fileList)): #Assembles list of directories that are not on local drive
                if data_files_to_get[i] == False:
                    fileList_to_get.append(fileList[i])
                else:
                    continue
                    
            print "created list of files to get"
                    
            for i in range(len(fileList_to_get)-1): #works thrtough the directories and downloads each file to local drive
                scan_directory_name = parse_directory_str(fileList_to_get[i])
                print scan_directory_name
                ftp.cwd(scan_directory_name)
                local_file = scan_directory_name + "_dat00001.csv"
                print local_file
                if any(local_file in s for s in local_fileList):
                    os.remove(local_file)
                local_filename = os.path.join(path, local_file) 
                print local_filename
                lf = open(local_filename, "wb")
                print "local file opened"
                ftp.retrbinary("RETR " + "dat00001.csv", lf.write)
                print "retrieved data and wrote to local file."
                lf.close()
                ftp.cwd("..")
                
            print "successfully retrieved files"    
                
            #close out ftp, instrument and resource manager connections
            ftp.quit()
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