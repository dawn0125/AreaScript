# -*- coding: utf-8 -*-
"""
This script takes in a folder of images which should contain one sample on top of a "substrate?"
For each image, it processes the area of the body as well as the area of the pores.
After processing the entire folder of images, it wil export an excel file. (didn't write that yet')

How to Use:
    1. Change image directory to the path with the folder of images 
    2. set show_thresh, save_thresh, and show_contours to True/False accordinly
    3. change thresh directory 
    4. set scale if it is different from the current input 
    
Procedure: 
    1. Iterates through a folder of images
    2. From each image, remove the background using REMBG remove
    3. Find the contours of the image using cv.findContours
    4. Separate the contour with the largest area (it will be the sample)
    4. Return the area of the remaining contours (pores)
    5. Save information and export file 
    
ALternative procedure: 
    1. find the "substrate?", create a mask of the sample above the substrate
    2. Previous procedure from step 3-5 
    
Notes: 
    - did not add scale yet 
"""
import os
import cv2 as cv
import numpy as np
import pandas as pd 
from rembg import remove 
import matplotlib.pyplot as plt

#=============================FUNCTIONS========================================
    
def threshManual(img, lower, upper):
    '''
    thresh according to bins added manually 
    '''
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    ret, thresh = cv.threshold(gray, lower, upper, cv.THRESH_BINARY)
    return thresh
    

def threshOtsu(img):
    '''
    img: image array 
    thresh: black and white image array 

    '''
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    ret, thresh = cv.threshold(gray, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
    return thresh

def threshold(img, manual):
    if manual == True: 
        print('Enter Lower Bin:')
        lower = int(input())
        print('Enter Upper Bin:')
        upper = int(input())
        
        return threshManual(img, lower, upper)
    
    else: 
        return threshOtsu(img)

def findContours(img):
    '''
    img: image array 
    contours: image array of just the contours of img 

    '''
    if np.ndim(img) != 2:
        img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    contours, hierarchy = cv.findContours(img, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    return contours

def findAreas(contours):
    '''
    contours: image array with contours found 
    area: array with area of each contour 

    '''
    area = []
    for cnt in contours:
        area.append(cv.contourArea(cnt))
    return np.asarray(area)
    
def heavilyBlur(img):
    '''
    blurs image so much that a lot of detail is lost (only for getting a mask)
    accepts: image array 
    returns: blurred image array 
    '''
    kernel = cv.getStructuringElement(cv.MORPH_RECT,(6,6))
    closed = cv.morphologyEx(img, cv.MORPH_CLOSE, kernel, iterations = 5)
    bilateral = cv.bilateralFilter(closed, 9, 75, 75)
    
    return bilateral

def findTransition(col):
    '''
    finds the point where there are 10 consecutive white pixels  
    '''
    white_px = np.where(col == 255)[0]
    return white_px[0]

def drawLine(x1, y1, x2, y2):
    '''
    draws a line between two points: y = mx + b
    '''
    m = (y2 - y1) / (x2 - x1)
    b = y2 - m * x2
    
    return m, b

def findSurfaceLine(thresh):
    '''
    accepts a thresh 
    '''
    xmax = np.shape(thresh)[1]
    firstcol = thresh[:,0]
    lastcol = thresh[:,-1]
    
    y1 = findTransition(firstcol)
    y2 = findTransition(lastcol)

    m, b = drawLine(0, y1, xmax, y2)

    return m, b

def createSurfaceMask(thresh):

    m, b = findSurfaceLine(thresh)
    
    surface_mask = np.full(thresh.shape[0:2], fill_value = 0, dtype="uint8") 
    
    # iterate through each column 
    for x in np.arange(np.shape(surface_mask)[1]): 
        
        # get index where the transition is 
        y = int(m * x + b)
        
        # change anything under the transition to 1 
        surface_mask[:,x][:y] = 1
        
    return surface_mask

def getSampleMask(img):
    '''
    accepts and image array, returns a binary array where 0 depicts the background
    and 1 depicts the portion of the sample above the flat surface

    '''
    # heavily filter the image to remove details 
    blurred = heavilyBlur(img)
    
    # make the image black and white 
    thresh_img = threshOtsu(blurred)
    
    # segment the surface 
    surface_mask = createSurfaceMask(thresh_img)
    
    # only keep parts of the image that are above the surface + are the sample
    mask = cv.bitwise_and(thresh_img, surface_mask)
    
    # fill the pores of the sample 
    p1 = np.full((img.shape[0]+2, img.shape[1]+2), fill_value=0, dtype="uint8")
    cv.floodFill(mask, p1, (0,0), 255)
    
    # invert the mask 
    mask = cv.bitwise_not(mask)
    
    return mask 

#=============================MAIN========================================
# directories
img_directory = '//wp-oft-nas/HiWis/GM_Dawn_Zheng/Vurgun/Area Images - Copy'
thresh_directory = '//wp-oft-nas/HiWis/GM_Dawn_Zheng/Vurgun/Thresh Images'
excel_directory = '//wp-oft-nas/HiWis/GM_Dawn_Zheng/Vurgun/Area Images/Areas.xlsx'

#  parameters 
loi = os.listdir(img_directory)
acceptedFileTypes = ['tif']
show_thresh = True
save_thresh = True
show_contours = True
scale = 1

# threshing 
manual_threshing = False
lower_thresh = 127
upper_thresh = 255

# for troubleshooting
issues = 0
problem_pics = []

# excel data 
data = []

if not os.path.exists(thresh_directory) and save_thresh == True:
    os.makedirs(thresh_directory)
    
# if saveThresh = True and threshDir does not exist, make directory 
# loop through images in image directory 
for i in loi:
    if( '.' in i and i.split('.')[-1] in acceptedFileTypes):
        try: 
            f = img_directory + '/' + i
            img = cv.imread(f)
            
            print('filtering ' + i)
            
            # create a mask which detects where the sample is 
            mask = getSampleMask(img)

            # plt.subplot(121), plt.imshow(img)
            # plt.title(i)
            # plt.subplot(122), plt.imshow(mask)
            # plt.show()
            
        except: 
            print('\nIssue filtering ' + i + '\n')
            issues += 1
            problem_pics.append(i)


        # begin threshing 
        if manual_threshing == True:
            thresh_img = threshManual(img, lower_thresh, upper_thresh)
            
        elif manual_threshing == False:
            thresh_img = threshOtsu(img)
        
        sample_only = cv.bitwise_and(thresh_img, mask) 
        
        # output comparison images only if you want to verify the thresh is good 
        if show_thresh == True:
            plt.subplot(311), plt.imshow(img)
            plt.title(i)
            plt.subplot(312), plt.imshow(thresh_img)
            plt.title('Thresh')
            plt.subplot(313), plt.imshow(sample_only)
            plt.title('BGRemoved')
            plt.tight_layout()
            plt.show()
        
        # save thresh into thresh directory 
        if save_thresh == True:
            cv.imwrite(thresh_directory  + '/' + i, sample_only)
        
        
        # find contours of thresh and the areas of each contour: 
        cnts = findContours(sample_only)
        areas = findAreas(cnts)
        max_area_index = np.argsort(areas)[-1]
        
        # output contours, white is the body and blue is the pores/scratches
        if show_contours == True: 
            im = np.zeros_like(img)
            for cnt in cnts:
                cv.drawContours(im, cnt, -1, (0, 255, 255), 5)
            cv.drawContours(im, cnts[max_area_index], -1, (255, 255, 255), 10)
            plt.imshow(im)
            plt.show()
    
        # write all this information into a csv + info Vurgun wants 
        whole_area = np.sort(areas)[-1] * scale
        pore_area = np.sum(areas) - np.sort(areas)[-1] * scale
        body_area = whole_area - pore_area
        ratio_area = pore_area/ body_area * 100 
        
        # save to csv  
        data.append([body_area, ratio_area])
        
        # print iformation
        print('\narea of body = {}'.format(body_area))
        print('area of pores = {}'.format(pore_area))
        print('ratio = {}'.format(ratio_area))
        print('\n')
        
df = pd.DataFrame(data=list(data), columns=['body area', 'ratio'])
df.to_excel(excel_directory)


if issues > 0:
    print('number of issues: ' + str(issues))
    print('issues with: ') 
    print(problem_pics)
    
print('Done Processing!')
