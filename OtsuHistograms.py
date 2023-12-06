# -*- coding: utf-8 -*-
"""
This program takes in a folder of images and displays the image, a threshold image based on 
Otsu Binarization, and a histogram of colour values in the image 

To use: Just change image_folder to the directory where your images are stored 
"""
import cv2 as cv 
import os 
import matplotlib.pyplot as plt

image_folder = '//wp-oft-nas/HiWis/GM_Dawn_Zheng/Arvid/Magnesium Walls for Dawn/otsutest'
loi = os.listdir(image_folder)
acceptedFileTypes = ['png'] # add more as needed

for i in loi:
    if( '.' in i and i.split('.')[-1] in acceptedFileTypes):
        
        # thresh image 
        f = image_folder + '/' + i
        img = cv.imread(f)
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        ret, thresh = cv.threshold(gray, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
        
        
        # plot image and thresh image
        plt.subplot(121), plt.imshow(img)
        plt.title(i), plt.xticks([]), plt.yticks([])

        plt.subplot(122), plt.imshow(thresh)
        plt.title('Otsu Threshing'), plt.xticks([]), plt.yticks([])
        
        plt.tight_layout()
        plt.show()
        
        
        # plot histogram
        plt.hist(img.ravel(),256)
        plt.title(i + ' Histogram')
        plt.grid()
        plt.show()
        