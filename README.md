# timestamp-extraction
Command line python tool to extract timestamps embedded on video frames and convert them to text. 

A wide range of applications, especially in industries that deal with broadcasting, videos are embedded with a timestamp at the time of archival. If the videos are stored as segments, as in the case of HLS, it becomes a cumbersome manual procedure to index these videos at a later time. 

It would be more convenient if one could feed in the coordinates and dimensions of the timestamp on the videos, and a tool could provide the timestamp at the first frame of the video. This is exactly what the timestamp-extraction tool does. 

<h2>How does it work?</h2>

<h3>The first step: Pre-processing video frames</h3>
Before the program tries to detect the characters in the timestamp, it is to be ensured that the timestamp is crealy visible and is neatly isolated from the image. Although it can be isolated using its coordinates in the frame and its dimesions, it is more challenging to isolate it from it's neighbourhood. In some frames, it may never be possible to isolate the timestamp from its background (For instance, when the neighbourhood is of the same colour as the timestamp). This can be achieved using a series of image processing techniques. Some of the techniques used are: median filtering, resizing, and geormetric transformations like opening and closing.   
At the end of this step, the a clear image of the timestamp is available for extraction to text. 

<h3>Text recognition in images using tesseract </h3>
Tesseract is an open source google tool for developers that helps recognize text embedded in images. 
When used on the isolated timestamp frame, tesseract can be used to recognize all text data in the image. 

<h3> Verifying that extracted timestamp is correct </h3>
More often than not, the text generated may vary from the timestamp on some digits.  
A regex is used to verify if the text recognized is in the form of a timestamp. Once the format has been verified, the text is verified by cheking against a timestamp value that is extracted from the same video source at a later instance of time. 
The program terminates if a timestamp that is in agreement with the timestamp detected at the first frame is recognized. 

The program lacks a good command line or graphical interface. 

Developers are welcome to contribute to this project, in terms of such improvements. 
