#!/usr/bin/env python

"""
Author: D. Knowles
Desc  : ROS node that publishes ultrasonic data
"""
import os
import time
import rospy
from umnitsa_msgs.msg import Ultrasonic
if (os.environ['ARCHITECTURE'] == 'raspi'):
    import RPi.GPIO as GPIO
elif (os.environ['ARCHITECTURE'] == 'nano'):
    import Jetson.GPIO as GPIO

class UltrasonicPublisher():
	def __init__(self):
		self.speedofsound = 343.0   # [m/s]
		self.minDistance = 0.0      # [m]
		self.maxDistance = 5.0      # [m]
		self.maxTime = (self.maxDistance*2.0)/self.speedofsound
		self.distanceTemp = [self.maxDistance,self.maxDistance,self.maxDistance,self.maxDistance]

		# pull the right pin numbers from the parameter file
		self.ULTRA1_TRIG = rospy.get_param('ULTRA1_TRIG')
		self.ULTRA1_ECHO = rospy.get_param('ULTRA1_ECHO')
		self.ULTRA2_TRIG = rospy.get_param('ULTRA2_TRIG')
		self.ULTRA2_ECHO = rospy.get_param('ULTRA2_ECHO')
		self.ULTRA3_TRIG = rospy.get_param('ULTRA3_TRIG')
		self.ULTRA3_ECHO = rospy.get_param('ULTRA3_ECHO')
		self.ULTRA4_TRIG = rospy.get_param('ULTRA4_TRIG')
		self.ULTRA4_ECHO = rospy.get_param('ULTRA4_ECHO')

		GPIO.setmode(GPIO.BOARD)    # use RasPi pin numbers
		GPIO.setwarnings(False)     # don't show setup warnings
		GPIO.setup(self.ULTRA1_TRIG,GPIO.OUT,initial=False)
		GPIO.setup(self.ULTRA1_ECHO,GPIO.IN)
		GPIO.setup(self.ULTRA2_TRIG,GPIO.OUT,initial=False)
		GPIO.setup(self.ULTRA2_ECHO,GPIO.IN)
		GPIO.setup(self.ULTRA3_TRIG,GPIO.OUT,initial=False)
		GPIO.setup(self.ULTRA3_ECHO,GPIO.IN)
		GPIO.setup(self.ULTRA4_TRIG,GPIO.OUT,initial=False)
		GPIO.setup(self.ULTRA4_ECHO,GPIO.IN)

		self.triggers = [self.ULTRA1_TRIG,
						 self.ULTRA2_TRIG,
						 self.ULTRA3_TRIG,
						 self.ULTRA4_TRIG]

		self.echoes = [self.ULTRA1_ECHO,
					   self.ULTRA2_ECHO,
					   self.ULTRA3_ECHO,
					   self.ULTRA4_ECHO]

		# setup publisher
		self.ultrasonic_publisher = rospy.Publisher('ultrasonic',Ultrasonic, queue_size=10)
		rospy.init_node('ultrasonic_sensors',anonymous=True)
		self.ultrasonic_distance = Ultrasonic()
		self.rate = rospy.Rate(5) # 10 Hz output rate
		# wait for sensor to settle
		time.sleep(5)

	def publish(self):
		while not rospy.is_shutdown():
			self.updateMeasurements()
			rospy.loginfo(self.ultrasonic_distance)
			self.ultrasonic_publisher.publish(self.ultrasonic_distance) # publish updated distances
			self.rate.sleep()

	def updateMeasurements(self):
		for ii in range(len(self.triggers)):
			# send 0.01ms pulse
			GPIO.output(self.triggers[ii],True)
			time.sleep(0.00001)
			GPIO.output(self.triggers[ii],False)

			# initialize both times
			start = time.time()
			stop = time.time()

			while GPIO.input(self.echoes[ii]) == 0:
				start = time.time()
				if start - stop > self.maxTime:
					break

			while GPIO.input(self.echoes[ii]) == 1:
				stop = time.time()
				if stop - start > self.maxTime:
					break

			elapsed = stop - start  # elapsed time
			distance = (elapsed * self.speedofsound) / 2.   # distance = time * velocit
			distance = self.clip(distance) # clip measurement

			self.distanceTemp[ii] = distance # update distance

		# package distances up for publishing
		self.ultrasonic_distance.ULTRA1 = self.distanceTemp[0]
		self.ultrasonic_distance.ULTRA2 = self.distanceTemp[1]
		self.ultrasonic_distance.ULTRA3 = self.distanceTemp[2]
		self.ultrasonic_distance.ULTRA4 = self.distanceTemp[3]

	def clip(self,input):
		if input < self.minDistance:
			output = self.minDistance
		elif input > self.maxDistance:
			output = self.maxDistance
		else:
			output = input
		return output



if __name__ == '__main__':
	try:
		publisher = UltrasonicPublisher()
		publisher.publish()
	except rospy.ROSInterruptException:
		GPIO.cleanup()
