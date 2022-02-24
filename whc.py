#!pythonw
# A Script to run in the background subscribed to mqtt Topics, and runs a counter clock
# with start/stop/pause/reset functions
# -*- coding: utf-8 -*-
# Import package
# pip3 install paho-mqtt
import ssl
import time
import datetime
import signal
import sys
import logging
import threading
import math
import paho.mqtt.client as mqtt

logging.basicConfig(
    filename='C:\Logs\ScoreboardClock.log',
    filemode='w',
    level=logging.DEBUG,
#   level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')


# Define Variables
#MQTT_HOST = "192.168.86.71"
MQTT_HOST = "192.168.86.71"
MQTT_PORT = 9001
MQTT_KEEPALIVE_INTERVAL = 45
TIMER_OP = 'Game/Timer_OP'
TIMER_SET = 'Game/Timer'
MQTT_USER = "whcadmin"
MQTT_PASSWORD = "S3cr3t321"
MQTT_INSTANCE = ""      # Empty Instance creates unique random name
QOS = 0
#
DEFAULT_TIME = 2100
minutes = 35
seconds = 0
countdown = DEFAULT_TIME
running = 0
TRUE = 1
FALSE = 0
STOP_COUNTING = 120
msg_sent = FALSE
msg_timestamp = FALSE

# First Logged message
logging.info("ScoreBoard Clock starting")

# Define on connect event function
def on_connect(self, mosq, obj, rc):
  """What to do when we connect to the broker"""
  if rc == 0:
    logging.debug("connected OK Returned code=%s", rc)
  elif rc == 1:
    logging.error("Connection refused, incorrect protocol version, Code =%s", rc
)
  elif rc == 2:
    logging.error("Connection refused, invalid client identifier, Code =%s", rc)
  elif rc == 3:
    logging.error("Connection refused, server unavailable, Code =%s", rc)
  elif rc == 4:
    logging.error("Connection refused, bad username or password, Code =%s", rc)
  elif rc == 5:
    logging.error("Connection refused, not authorised, Code = %s", rc)
  else:
    logging.error("Bad connection Returned code=%s", rc)
  if rc != 0:
    cleanup()

def on_disconnect(result_code):
  """Handle disconnections from the broker"""
  if result_code == 0:
    logging.debug("Clean disconnection")
  else:
    logging.error("Unexpected disconnection! Reconnecting in 5 seconds")
    logging.error("Result code: %s", result_code)
    time.sleep(5)
    connect()
    main_loop()

# Define on_message event function.
# This function will be invoked every time,
# a new message arrives for the subscribed topic
def on_message(mosq, obj, msg):
  """What to do when we receive a message on the Topics we are subscibed to"""
  global running, countdown
  logging.info('Received Message : Topic: %s, Payload: %s', msg.topic, msg.payload.decode("utf-8"))
  if msg.topic == TIMER_OP:
    if msg.payload.decode("utf-8") == "START":
      running = 1
      logging.info('Starting Clock')
    elif msg.payload.decode("utf-8") == "STOP":
      running = 0
      logging.info('Stopping Clock')
    elif msg.payload.decode("utf-8") == "PAUSE":
      running = 0
      logging.info('Pausing Clock')
    elif msg.payload.decode("utf-8") == "RESUME":
      running = 1
      logging.info('Resuming Clock')
    elif msg.payload.decode("utf-8") == "RESET":
      running = 0
      logging.info('Resetting Clock')
  elif msg.topic == TIMER_SET:
    countdown = timetocount(msg.payload.decode("utf-8"))
    logging.info('Setting Clock to : %s', counttotime(countdown))
  else:
    logging.error("Unknown Message on topic:%s Payload :%s", msg.topic, msg.payload.decode("utf-8"))

def on_subscribe(mosq, obj, mid, granted_qos):
  """What to do when we receive subscibed confirmation"""
  logging.debug("Subscribe Success :%s:%s:%s:%s", mosq, obj, mid, granted_qos)

# Initiate MQTT Client
logging.debug("Creating Instance")
mqttc = mqtt.Client(MQTT_INSTANCE, transport='websockets')

# Connect with MQTT Broker
#mqttc.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS, ciphers=None)
mqttc.username_pw_set(MQTT_USER, password=MQTT_PASSWORD)

def connect():
  """What to do when we connect to the broker"""
  result = mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)
  if result != 0:
    logging.error("Connection failed with error code %s. Retrying", result)
    time.sleep(10)
    connect()
  # Assign event callbacks
  mqttc.on_message = on_message
  mqttc.on_connect = on_connect
  mqttc.on_subscribe = on_subscribe

#  mqttc.subscribe(TIMER_OP)
#  mqttc.subscribe(TIMER_SET)
  mqttc.subscribe('Game/#')

def cleanup(signum, frame):
  """What to do when we receive a signal"""
#     Signal handler to ensure we disconnect cleanly
#     in the event of a SIGTERM or SIGINT.
  logging.info("Disconnecting from broker")
  mqttc.publish(TIMER_OP, "Offline", qos=QOS, retain=False)
  mqttc.disconnect()
  logging.info("Exiting on signal %d", signum)
  sys.exit(signum)

def counttotime(count):
  mins = math.floor(count/60)
  secs = count - mins * 60
  return ('{:02d}:{:02d}'.format(int(mins), int(secs)))

def timetocount(time):
  mins = int(time[0:2])
  secs = int(time[3:])
  return (mins * 60 + secs)

def tiktok():
  global countdown, running
  logging.debug("TikTok : Countdown : %s Running : %s", counttotime(countdown), running )
  if running:
    next_call = int(time.time())
    time.sleep(.5)
    if next_call != int(time.time()):
      if countdown <= STOP_COUNTING:
        countdown = STOP_COUNTING
        running = 0
      else :
        countdown -= (int(time.time()) - next_call)
      mqttc.publish(TIMER_SET, counttotime(countdown), qos=QOS, retain=True)


def main_loop():
  """The main loop in which we stay connected to the broker"""
  global msg_sent, msg_timestamp, countdown, running
  while mqttc.loop() == 0:
    tiktok()
 

# Use the signal module to handle signals
signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

#connect to broker
connect()
try:
  main_loop()
except IOError as err:
  logging.error("I/O error: {0}:%s", err)
except ValueError:
  logging.error("coulr not convert data to an integer.")
except KeyboardInterrupt:
  logging.error("Interrupted by User/Keyboard")
except SystemExit:
  logging.info("Stopped by Sysctl:")
except:
  logging.error("Exiting due to Exeption:", exc_info=True)
finally:
  logging.info("Disconnecting from broker")
  mqttc.publish(TIMER_OP, "Offline", qos=QOS, retain=False)
  mqttc.disconnect()
