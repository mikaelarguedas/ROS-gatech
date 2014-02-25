#!/usr/bin/env python
import roslib
roslib.load_manifest('blob_tracker_base')

import rospy
import cv2.cv as cv
import sensor_msgs.msg
from sensor_msgs.msg import RegionOfInterest
from cv_bridge import CvBridge
import time



def is_rect_nonzero(r):
	(_,_,w,h) = r
	return (w > 0) and (h > 0)
	



class CamShiftDemo:
    
	def __init__(self):
		#rospy.loginfo(" begin init")
		self.br = CvBridge()
		#self.capture = cv.CaptureFromCAM(0)
		rospy.Subscriber("/vrep/visionSensor", sensor_msgs.msg.Image, self.detect_and_draw)
		self.frame = cv.CreateImage( (320,200), 8, 3)
		self.backproject = cv.CreateImage( (320,200), 8, 3)
		self.header = None
		cv.NamedWindow( "CamShiftDemo", 1 )
		cv.NamedWindow( "Histogram", 1 )
		cv.SetMouseCallback( "CamShiftDemo", self.on_mouse)
		self.drag_start = None      # Set to (x,y) when mouse starts drag
		self.track_window = None    # Set to rect when the mouse drag finishes
		self.pause = False

		

		

		self.disp_hist = True
		self.backproject_mode = False
		self.hist = cv.CreateHist([180], cv.CV_HIST_ARRAY, [(0,180)], 1 )


		rospy.init_node('blob_tracker')
		self.blob_pub = rospy.Publisher("blobimage", sensor_msgs.msg.RegionOfInterest)
		
		print( "Keys:\n"
		"    ESC - quit the program\n"
			"    b - switch to/from backprojection view\n"
			"    p - pause processing\n"
			"To initialize tracking, drag across the object with the mouse\n" )
		#rospy.loginfo(" end init")
  
	def hue_histogram_as_image(self, hist):
		""" Returns a nice representation of a hue histogram """
		histimg_hsv = cv.CreateImage( (320,200), 8, 3)

		mybins = cv.CloneMatND(hist.bins)
		cv.Log(mybins, mybins)
		(_, hi, _, _) = cv.MinMaxLoc(mybins)
		cv.ConvertScale(mybins, mybins, 255. / hi)

		w,h = cv.GetSize(histimg_hsv)
		hdims = cv.GetDims(mybins)[0]
		for x in range(w):
		    xh = (180 * x) / (w - 1)  # hue sweeps from 0-180 across the image
		    val = int(mybins[int(hdims * x / w)] * h / 255)
		    cv.Rectangle( histimg_hsv, (x, 0), (x, h-val), (xh,255,64), -1)
		    cv.Rectangle( histimg_hsv, (x, h-val), (x, h), (xh,255,255), -1)

		histimg = cv.CreateImage( (320,200), 8, 3)
		cv.CvtColor(histimg_hsv, histimg, cv.CV_HSV2BGR)
		return histimg

	def on_mouse(self, event, x, y, flags, param):
		#rospy.loginfo(" begin on_mouse")
		if event == cv.CV_EVENT_LBUTTONDOWN:
			self.drag_start = (x, y)
		if event == cv.CV_EVENT_LBUTTONUP:
		    self.drag_start = None
		    self.track_window = self.selection
		if self.drag_start:
			xmin = min(x, self.drag_start[0])
			ymin = min(y, self.drag_start[1])
			xmax = max(x, self.drag_start[0])
			ymax = max(y, self.drag_start[1])
			self.selection = (xmin, ymin, xmax - xmin, ymax - ymin)
		#rospy.loginfo(" end on_mouse")

	def detect_and_draw(self,imgmsg):
		if self.pause:
			return
        #frame = cv.QueryFrame( self.capture )
	#frame = self.br.imgmsg_to_cv(frame)
	#frame = self.frame
		frame = self.br.imgmsg_to_cv(imgmsg,"bgr8")
		hsv = cv.CreateImage(cv.GetSize(frame), 8, 3)
		cv.CvtColor(frame, hsv, cv.CV_BGR2HSV)
		self.hue = cv.CreateImage(cv.GetSize(frame), 8, 1)
		cv.Split(hsv, self.hue, None, None, None)
	
		# Compute back projection
		backproject = cv.CreateImage(cv.GetSize(frame), 8, 1)
	
	
        # Run the cam-shift
		cv.CalcArrBackProject( [self.hue], backproject, self.hist )
		if self.track_window and is_rect_nonzero(self.track_window):
			crit = ( cv.CV_TERMCRIT_EPS | cv.CV_TERMCRIT_ITER, 10, 1)
			(iters, (area, value, rect), track_box) = cv.CamShift(backproject, self.track_window, crit)
			self.track_window = rect
	    #rospy.loginfo(str(type(rect)))

        # If mouse is pressed, highlight the current selected rectangle
        # and recompute the histogram

		if self.drag_start and is_rect_nonzero(self.selection):
			sub = cv.GetSubRect(frame, self.selection)
			save = cv.CloneMat(sub)
			cv.ConvertScale(frame, frame, 0.5)
			cv.Copy(save, sub)
			x,y,w,h = self.selection
			cv.Rectangle(frame, (x,y), (x+w,y+h), (255,255,255))
			#self.blob_pub.publish(self.x,self.y, self.x+self.w,self.y+self.h,True)
			sel = cv.GetSubRect(self.hue, self.selection )
			cv.CalcArrHist( [sel], self.hist, 0)
			(_, max_val, _, _)= cv.GetMinMaxHistValue(self.hist)
			if max_val != 0:
				cv.ConvertScale(self.hist.bins, self.hist.bins, 255. / max_val)
	    
  	  # rospy.loginfo(" before publish")
	    
	  #  rospy.loginfo(" after publish")
		elif self.track_window and is_rect_nonzero(self.track_window):
			cv.EllipseBox( frame, track_box, cv.CV_RGB(255,0,0), 3, cv.CV_AA, 0 )
			#rospy.loginfo(len(track_box) +str(track_box[0]) )#+str(track_box[1]) +str(track_box[2]))
			#rospy.loginfo(str(type(self.track_window)) + "first element" + str(self.track_window[0])+ "second element" + str(self.track_window[1])+ "third element" + str(self.track_window[2]))
			self.blob_pub.publish(self.track_window[0],self.track_window[1],self.track_window[2] ,self.track_window[3],True)			
			#self.blob_pub.publish(track_box[0],track_box[1],track_box[2],track_box[3],True)			

	    
		#if (self.w > 3) and (self.h > 3):   
		self.frame = frame
		self.backproject = backproject
		#cv.ShowImage("proba",self.backproject)
		#rospy.loginfo(str(type(self.proba_pub)))
		#if(type(self.proba_pub)!= NoneType)
		self.proba_pub.publish(self.br.cv_to_imgmsg(self.backproject, "mono8"))	
					
			
	#rospy.loginfo(" end detect")


	def run(self):
		self.disp_hist = True
		self.backproject_mode = False
		self.hist = cv.CreateHist([180], cv.CV_HIST_ARRAY, [(0,180)], 1 )

		rospy.init_node('blob_tracker')
		self.proba_pub = rospy.Publisher("probability", sensor_msgs.msg.Image)
		while not rospy.is_shutdown():
            # rospy.spin_once()
			if not self.pause:
				#self.detect_and_draw()
				if not self.backproject_mode:
					cv.ShowImage( "CamShiftDemo", self.frame )
				else:
					cv.ShowImage( "CamShiftDemo", self.backproject)
				if self.disp_hist:
					cv.ShowImage( "Histogram", self.hue_histogram_as_image(self.hist))
			c = cv.WaitKey(7) & 0x0FF
			if c == 27:
				rospy.signal_shutdown("OpenCV said so")
			elif c == ord("p"):
				self.pause = not self.pause
			elif c == ord("b"):
				self.backproject_mode = not self.backproject_mode

if __name__=="__main__":
    demo = CamShiftDemo()
    demo.run()
    cv.DestroyAllWindows()
