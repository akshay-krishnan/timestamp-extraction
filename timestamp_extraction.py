# program to extract a timestamp from a video
# written by Akshay Krishnan, Yashika (Interns, Amagi Media Labs)

#usage:
#timestamp_extract.py -b <Name_of_s3_bucket> -p <path_to_folder_containing_videos_in_bucket> -f(optional)
#specifying f is optional. if specified, it downloads entire video from the bucket.
#before running, ensure that a file 'videos.txt' contains the list of videos in s3 from which timestamp is to be extracted
#after execution, extracted timestamps are stored in stamp_file.txt

import cv2				#computer vision library to process images
from PIL import Image 	#Python imaging library to handle images
import pytesseract		#Google's tesseract-OCR wrapper for python
import argparse 		#library to handle command line arguments
import os 				#perform file operations, create and remove files
import re 				#perform regular expression search
import unicodedata		#convert string format between unicode and ascii
import boto3 			#downloading files 
import botocore 		#from AWS s3


#function to convert the numbers in the stamp as detected by tesseract
#into the standard hh:mm:ss:nn stamp format
def stampFromText(text):
	stamp =  text.encode('ascii','ignore')
	s = list(stamp)
	st = []
	for item in s:
		if item.isdigit() == True:
			st.append(item)
	if len(st) == 8:
		return (True, st[0]+st[1]+':'+st[2]+st[3]+':'+st[4]+st[5]+':'+st[6]+st[7])
	else:
		return 	(False, 'garbage')


#function to calculate the mismatch between stamp of first frame
#as obtained by frame number and the stamp as obtained by tesseract
def calculateMismatch(stamp, firstFrameStamp, frame_no):
	h, m, s, f = firstFrameStamp
	h1, m1, s1, f1 = stamp
	init_f = (h*3600 + m*60 + s)*25 + f+1
	now_f = (h1*3600 +m1*60+s1)*25 +f1 +1
	return frame_no - (now_f - init_f)


#function that obtains the timestamp in a given frame of the video
def GetTimestamp(video):
	cap = cv2.VideoCapture(video)
	filename = "timestamp_test_file.bmp"
	stamp_found = False
	frame_count = 0
	stamp_confirmed = False
	stamp = None
	firstFrameStamp1 = None

	reset_count = 0
	mismatch = 0
	while(cap.isOpened() and stamp_confirmed is False):
		ret, frame = cap.read()
		if ret == True:
			cv2.imwrite(filename, frame)
			text = pytesseract.image_to_string(Image.open(filename))
			if len(text) > 0:
				m = re.findall("[0-2][0-9].[0-5][0-9].[0-5][0-9].[0-9][0-9]", text)
				if len(m) > 0:
					temp_flag, stamp = stampFromText(m[0])
					if temp_flag is True:
						firstFrameStamp = getTimeFirstFrame(stamp, frame_count, 25)
						if stamp_found is False:
							stamp_found = True
							firstFrameStamp1 = firstFrameStamp
							
						else:
							x,y,w,z = firstFrameStamp1
							x1,y1,w1,z1 = firstFrameStamp
							if (x1==x and y1==y and z1==z and w1==w):
								stamp_confirmed = True
								mismatch = calculateMismatch(intStamp(stamp), firstFrameStamp, frame_count)
							else:
								firstFrameStamp1 = firstFrameStamp
								reset_count+=1
				else:
					gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
					rows, cols =  gray.shape
					gray = gray[20:40, int(float(cols/3))+18:int(float(cols)*2/3)-16]
					gray = cv2.threshold(gray, 240,255,cv2.THRESH_BINARY)[1]
					gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
					gray = cv2.dilate(gray, cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3)), iterations=1)
					cv2.imwrite(filename, gray)
					text = pytesseract.image_to_string(Image.open(filename))
					os.remove(filename)
					if len(text) > 0:
						m = re.findall("[0-2][0-9].[0-5][0-9].[0-5][0-9].[0-9][0-9]", text)
						if len(m) > 0:
							temp_flag, stamp = stampFromText(m[0])
							if temp_flag is True:
								firstFrameStamp = getTimeFirstFrame(stamp, frame_count, 25)
								if stamp_found is False:
									stamp_found = True
									firstFrameStamp1 = firstFrameStamp
										
								else:
									x,y,w,z = firstFrameStamp1
									x1,y1,w1,z1 = firstFrameStamp
									if (x1==x and y1==y and z1==z and w1==w):
										stamp_confirmed = True
										mismatch = calculateMismatch(intStamp(stamp), firstFrameStamp, frame_count)
									else:
										firstFrameStamp1 = firstFrameStamp
										reset_count+=1
			frame_count += 1		
		else:
			break
	if(os.path.isfile('timestamp_test_file.bmp')):
		os.remove('timestamp_test_file.bmp')
	cap.release()
	return stamp_confirmed, firstFrameStamp1, mismatch


#if frame number is given as input, the function returns the run time to reach that particular frame
def getTimeFromFrameNumber(frame_no, fps):
	f = frame_no % fps
	s = int(frame_no/fps)
	m = int(s/60)
	s = s%60
	h = int(m/60)
	m = m%60
	return (h, m, s, f)


#helper function to convert stamps from string to integer tuples
def intStamp(stamp):
	l = stamp.split(':')
	t = []
	for i in l:
		t.append(int(i))
	return t


#funtion to calculate the timestamp on the first frame if the stamp at 
#any other frame and the corresponding frame numbers are input
def getTimeFirstFrame(stamp, frameno, fps):
	t = intStamp(stamp)
	h,m,s,f = t
	secs = h*3600 + m*60 + s
	isecs = secs - (frameno/fps)
	h = isecs/3600
	m = (isecs%3600)/60
	s = (isecs%60)
	return (h,m,s,0)



if __name__ == '__main__':
	ap = argparse.ArgumentParser()
	ap.add_argument("-b", "--bucket", required=True, help="S3 bucket name")
	ap.add_argument("-p", "--path", required=True, help="path to folder containing videos in bucket")
	ap.add_argument("-f", "--full", default=False, help="boolean flag, if set downloads entire media file", action='store_true')

	args = vars(ap.parse_args())
	s3 = boto3.resource('s3')
	client = boto3.client('s3')
	offset = 0
	end = 5000000

	if(os.path.isfile('stamp_file.txt')):
		db_file = open("stamp_file.txt", 'r')
		text_from_file = str(db_file.read())
		db_file.close()
	else:
		text_from_file = ''
	videos_file = open("videos.txt")
	videoname = ''
	stamp_file = open("stamp_file.txt", 'a+')
	lines = videos_file.read().split('\n')
	try:
		for line in lines:
			if len(line) > 0:
				words = line.split(' ')
				videoname = words[len(words)-1]
				if videoname in text_from_file:
					print videoname, ": entry already exists for this video"
				else:
					if args["full"] is True:
						s3.Bucket(args["bucket"]).download_file(args["path"]+videoname, videoname)
					else:
						obj = client.get_object(Bucket=args["bucket"], Key=args["path"]+videoname,Range='bytes={}-{}'.format(offset, end))
						newdata = obj['Body'].read()
						f = open(videoname,'w')
						f.write(newdata)
						f.close()
					
					flagt, stamp, err = GetTimestamp(videoname)
					os.remove(videoname)
					if flagt == True:
						stamp_file.write(videoname+', '+str(stamp[0])+":"+str(stamp[1])+":"+str(stamp[2])+":"+str(stamp[3])+', '+str(err)+'\n')
						print "video ", videoname, stamp, err

					else:
						print videoname, ": error in finding stamp"
		stamp_file.close()
		videos_file.close()
	except KeyboardInterrupt:
		if(os.path.isfile('timestamp_test_file.bmp')):
			os.remove('timestamp_test_file.bmp')
		if(os.path.isfile(videoname)):
			os.remove(videoname)
		stamp_file.close()
		videos_file.close()
		print "quitting"

