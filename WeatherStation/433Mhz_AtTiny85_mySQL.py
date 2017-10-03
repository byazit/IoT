#!/usr/bin/env python

"""
This module provides a 313MHz/434MHz radio interface compatible
with the Virtual Wire library used on Arduinos.

It has been tested between a Pi, and Arduino Pro Mini.
"""
# 2015-06-4
#2016-05-04
# vw.py
import time
import MySQLdb
import pigpio
import vw
import socket
import fcntl
import struct

MAX_MESSAGE_BYTES=77
MIN_BPS=50
MAX_BPS=10000
count=0
_HEADER=[0x2a, 0x2a, 0x2a, 0x2a, 0x2a, 0x2a, 0x38, 0x2c]

_CTL=3

_SYMBOL=[
   0x0d, 0x0e, 0x13, 0x15, 0x16, 0x19, 0x1a, 0x1c, 
   0x23, 0x25, 0x26, 0x29, 0x2a, 0x2c, 0x32, 0x34]


def _sym2nibble(symbol):
   for nibble in range(16):
      if symbol == _SYMBOL[nibble]:
         return nibble
   return 0

def _crc_ccitt_update(crc, data):

   data = data ^ (crc & 0xFF);

   data = (data ^ (data << 4)) & 0xFF;

   return (
             (((data << 8) & 0xFFFF) | (crc >> 8)) ^
              ((data >> 4) & 0x00FF) ^ ((data << 3) & 0xFFFF)
          )

class rx():

   def __init__(self, pi, rxgpio, bps=2000):
      """
      Instantiate a receiver with the Pi, the receive gpio, and
      the bits per second (bps).  The bps defaults to 2000.
      The bps is constrained to be within MIN_BPS to MAX_BPS.
      """
      self.pi = pi
      self.rxgpio = rxgpio

      self.messages = []
      self.bad_CRC = 0

      if bps < MIN_BPS:
         bps = MIN_BPS
      elif bps > MAX_BPS:
         bps = MAX_BPS

      slack = 0.20
      self.mics = int(1000000 / bps)
      slack_mics = int(slack * self.mics)
      self.min_mics = self.mics - slack_mics       # Shortest legal edge.
      self.max_mics = (self.mics + slack_mics) * 4 # Longest legal edge.

      self.timeout =  8 * self.mics / 1000 # 8 bits time in ms.
      if self.timeout < 8:
         self.timeout = 8

      self.last_tick = None
      self.good = 0
      self.bits = 0
      self.token = 0
      self.in_message = False
      self.message = [0]*(MAX_MESSAGE_BYTES+_CTL)
      self.message_len = 0
      self.byte = 0

      pi.set_mode(rxgpio, pigpio.INPUT)

      self.cb = pi.callback(rxgpio, pigpio.EITHER_EDGE, self._cb)

   def _calc_crc(self):

      crc = 0xFFFF
      for i in range(self.message_length):
         crc = _crc_ccitt_update(crc, self.message[i])
      return crc

   def _insert(self, bits, level):

      for i in range(bits):

         self.token >>= 1

         if level == 0:
            self.token |= 0x800

         if self.in_message:

            self.bits += 1

            if self.bits >= 12: # Complete token.

               byte = (
                  _sym2nibble(self.token & 0x3f) << 4 |
                  _sym2nibble(self.token >> 6))

               if self.byte == 0:
                  self.message_length = byte

                  if byte > (MAX_MESSAGE_BYTES+_CTL):
                     self.in_message = False # Abort message.
                     return

               self.message[self.byte] = byte

               self.byte += 1
               self.bits = 0

               if self.byte >= self.message_length:
                  self.in_message = False
                  self.pi.set_watchdog(self.rxgpio, 0)

                  crc = self._calc_crc()

                  if crc == 0xF0B8: # Valid CRC.
                     self.messages.append(
                        self.message[1:self.message_length-2])
                  else:
                     self.bad_CRC += 1

         else:
            if self.token == 0xB38: # Start message token.
               self.in_message = True
               self.pi.set_watchdog(self.rxgpio, self.timeout)
               self.bits = 0
               self.byte = 0

   def _cb(self, gpio, level, tick):

      if self.last_tick is not None:

         if level == pigpio.TIMEOUT:

            self.pi.set_watchdog(self.rxgpio, 0) # Switch watchdog off.

            if self.in_message:
               self._insert(4, not self.last_level)

            self.good = 0
            self.in_message = False

         else:

            edge = pigpio.tickDiff(self.last_tick, tick)

            if edge < self.min_mics:

               self.good = 0
               self.in_message = False

            elif edge > self.max_mics:

               if self.in_message:
                  self._insert(4, level)

               self.good = 0
               self.in_message = False

            else:

               self.good += 1

               if self.good > 8: 

                  bitlen = (100 * edge) / self.mics

                  if   bitlen < 140:
                     bits = 1
                  elif bitlen < 240:
                     bits = 2
                  elif bitlen < 340:
                     bits = 3
                  else:
                     bits = 4

                  self._insert(bits, level)

      self.last_tick = tick
      self.last_level = level

   def get(self):
      """
      Returns the next unread message, or None if none is avaiable.
      """
      if len(self.messages):
         return self.messages.pop(0)
      else:
         return None

   def ready(self):
      """
      Returns True if there is a message available to be read.
      """
      return len(self.messages)

   def cancel(self):
      """
      Cancels the wireless receiver.
      """
      if self.cb is not None:
         self.cb.cancel()
         self.pi.set_watchdog(self.rxgpio, 0)
      self.cb = None
def dataBase():
	# Open database connection
   db = MySQLdb.connect("107.180.4.79","piSaveInfo","password","piSaveInfo" )

# prepare a cursor object using cursor() method
   cursor = db.cursor()
   #daTi= time.strftime('%Y-%m-%d %H:%M:%S')
   if raz[0:3]=="pir":
      #print raz			
      sql="INSERT INTO pirSensor(ip,deviceID,dateTime)VALUES('%s','%s','%s') "%(ip,raz[5:8],daTi)
         # disconnect from server
      try:
   # Execute the SQL command
         cursor.execute(sql)
   # Commit your changes in the database
         db.commit()
      except:
   # Rollback in case there is any error
         db.rollback()
         print "error"
      db.close()
   if raz[0:2]=="ID":
      sql="INSERT INTO weatherState(ip,deviceID,temp,humd,dateTime)VALUES('%s','%s','%s','%s','%s') "%(ip,raz[3:6],raz[12:14],raz[19:22],daTi)
         # disconnect from server
      try:
   # Execute the SQL command
         cursor.execute(sql)
   # Commit your changes in the database
         db.commit()
      except:
   # Rollback in case there is any error
         db.rollback()



         print "error"

      db.close()
#dropBox upload and download
def dropBox():
   import os
   import subprocess as sub

   motionE="motion.txt"
   weatherE="weather.txt"
   download_dir = "/home/pi/upload/Dropbox-Uploader/"
   daTi= time.strftime('%Y-%m-%d %H:%M:%S')
   #daTi= time.strftime('%Y-%m-%d %H:%M:%S')
   if raz[0:3]=="pir":
      #print raz			
      f=open('motion.txt','w')
      f.write(ip+' '+raz[5:8]+' '+daTi)
      f.close()
      cmd = download_dir + "dropbox_uploader.sh upload "
      cmd += motionE + " /"
      os.system(cmd)
   if raz[0:2]=="ID":
      dataBase()
"""
      #print raz
      f=open('weather.txt','w')
      f.write('DeviceId: '+raz[3:6]+' Temp: '+raz[12:14]+' Hum: '+raz[19:22]+' '+daTi)
      f.close()
      cmd = download_dir + "dropbox_uploader.sh upload "
      cmd += weatherE + " /"
      os.system(cmd)
"""
#send an email through gmail
def sys_email():
      try:
         #server = smtplib.SMTP(SERVER) 
         server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465) #or port 465 doesn't seem to work!
         server_ssl.ehlo()
         server_ssl.login(gmail_user, gmail_pwd)
         server_ssl.sendmail(FROM, TO, message)
         #server.quit()
         server_ssl.close()
         #print 'successfully sent the mail'
      except:
         dropBox()

def send_email():
   import smtplib
   daTi= time.strftime('%Y-%m-%d %H:%M:%S')
   if raz[0:3]=="pir":
      gmail_user = "razib.rob@gmail.com"
      gmail_pwd = "#"
      FROM = ''
      TO = [''] #must be a list
      SUBJECT = "MotionDetected@"+daTi
      TEXT = "check"

      # Prepare actual message
      message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
      """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
      sys_email()

if __name__ == "__main__":

   """
	#fatch database

   sql = "SELECT * FROM weatherState"
   
   try:
   # Execute the SQL command
      cursor.execute(sql)
   # Fetch all the rows in a list of lists.
      results = cursor.fetchall()
      #print results
      for row in results:
         id = row[0]
         ip = row[1]
         temp = row[2]
         humd = row[3]
         dateTime = row[4]
      # Now print fetched result
         print row[4]
         print "id=%d,ip=%s,temo=%d,humd=%d,dateTime=%s"%(id,ip,temp,humd,dateTime )
   except:
      print "Error: unable to fecth data"
   """ 
   #get eth0 ip address
   def get_ip_address(ifname):
       s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
       return socket.inet_ntoa(fcntl.ioctl(
           s.fileno(),
           0x8915,  # SIOCGIFADDR
           struct.pack('256s', ifname[:15])
       )[20:24])
   ip= get_ip_address('eth0')
   RX=17
   BPS=2000

   pi = pigpio.pi() # Connect to local Pi.

   rx = vw.rx(pi, RX, BPS) # Specify Pi, rx gpio, and baud.

   msg = 0
   start = time.time()
   #while (time.time()-start) < 300:
   while (1):
      while rx.ready():
         count +=1
         raz="".join(chr (c) for c in rx.get())
         l=list(raz)
         #print raz
         #print raz[0:2]
         #print(count,"-".join(chr (c) for c in rx.get()))
         #for c in rx.get():
            #c=chr(c)
            #print c
            #if(c!=":"):
               #print("".join(chr (r) for r in rx.get()))
         dataBase()
         #dropBox()
         #send_email()
   send_email()
   rx.cancel()
   pi.stop()
