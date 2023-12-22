# Code Explained #

This document was created for Nima and Vurgun for off-boarding purposes. It explains the AreaScript.py in detail. The procedure is as follows: 

1. Find surface 
2. Extract the part of the sample **above** the surface 
3. Find area of pores and area of sample
4. Calculate **porosity** and save data to CSV/Excel file

The contents of this document follow the order of the procedure. 

## Finding Surface ##

The "surface" is a straight line that the sample **intersects**. 

To find the surface, we heavily blur the thresh image to get rid of the noise. Then, for the first and last columns, we find the first white pixels and assume they are the surface. After, we connect the pixels with a straight line: 

$$ y = mx + b $$

The functions defined in lines 90 - 119 do the procedure above: 


```python
# lines 90 - 119
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
```

## Creating Mask ##

The mask of the sample in question is a combination of a mask of the surface, named **surface_mask**, and a binary thresh of the image: line 224


```python
# line 244: combining thresh and surface mask
sample_only = cv.bitwise_and(thresh_img, mask) 
```

### Surface Mask ###

After finding the surface line above, we must create a **binary mask** of the surface. 

Since we only need to consider the part of the sample that is **above** the surface, we will first make an array of 0s that is the same shape as our image. Then, for each column, we will find the **y pixel** of the surface line by solving $y = mx + b$. Then, we set all the pixels above our y pixel to be 1. This procedure is implemented in the function createSurfaceMask. 


```python
# lines 121 - 136
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
```

### Threshold ###

The threshold can be done either **manually** or **automatically**. The functions that define manual and automatic threshing are in lines 37 - 54.


```python
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
```

In both functions, the image is turned to grayscale, then threshed using cv.threshold from opencv's library. The difference is that in threshOtsu, the automatic threshing, the parameter cv.THRESH_OTSU is used alongside cv.THRESH_BINARY. 

Otsu thresholding picks the thresh based on a histogram of the colours. For more on this, checkout the otsuHistogram.py file in the repository. 

The choice between threshing methods is defined in line 180, The **manual** threshing parameters are defined in lines 181 and 182: 


```python
# lines 180 - 182
manual_threshing = True
lower_thresh = 127
upper_thresh = 255
```

The threshing is then implemented in lines 218 - 222:


```python
# lines 218 - 222: 
if manual_threshing == True:
    thresh_img = threshManual(blurred, lower_thresh, upper_thresh)

elif manual_threshing == False:
    thresh_img = threshOtsu(blurred)
```

## Finding and Filtering Contours ##
In our code, we find the contours, hierarchies, and area after threshing in lines 237 - 241, using functions from lines 56 - 77:


```python
# function from lines 56 - 65
def findContours(img):
    '''
    img: image array 
    contours: image array of just the contours of img 

    '''
    if np.ndim(img) != 2:
        img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    contours, hierarchy = cv.findContours(img, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
    return contours, hierarchy
```

findContours is just turns an image to grayscale if it is not already, and then finds the contours using opencv's findContours function (nothing revolutionary) 


```python
# function from line 67 - 77
def findAreas(contours):
    '''
    contours: image array with contours found 
    area: array with area of each contour 

    '''
    area = []
    for cnt in contours:
        area.append(cv.contourArea(cnt))
    return np.asarray(area)
```

findAreas loops over each contour that is returned by the findContours function and finds the area of that contour. **cv.contourArea only takes in 1 contour**, not a list of contours.


```python
# code from lines 237 - 241: 
cnts, hier = findContours(sample_only)
parent = hier[:,:,3][0]
areas = findAreas(cnts)
max_area_index = np.argsort(areas)[-1]
```

In the code above, "cnts" and "hier" are the contours and hierarchies that are extracted from the findContours function. The parent of each contour is then extracted into a separate array for easy indexing later on. The areas is then extracted. Finally, the **indices** of the areas are sorted, smallest to largest, and the largest one [-1] is extracted as our "max_area_index". This index corresponds to the contour, area, and parent of our sample. 


The remaining contours are then filtered based on their **parent**. If their parent is our sample contour, as denoted by the max_area_index, then they are considered a **pore**. This filtering happens in lines 247 - 251: 


```python
# lines 247 - 251
for j in np.arange(len(cnts)):
    if parent[j] == max_area_index: #and areas[j] >= 100:
        pore_area += areas[j]
        cv.drawContours(cnt_img, cnts, j, (0, 255, 255), 5)   
cv.drawContours(cnt_img, cnts, max_area_index, (255, 255, 255), 10)
```

In the lines above, we use "j" to denote the index of the contour that we examine. We loop over all the contours returned previously by findContours. 

If the parent of the contour is our sample, meaning that the contour is **inside** the sample, then it is a pore. We add the area of the pore into our total sum of pore areas, then draw the pore using yellow on our summary image. This way, we can check to make sure our pore areas counts only the pores that we are interested in. 

Finally, we draw the outline of our sample contour, this is also for checking, to ensure 2 things: 
1. the sample contour is actually the sample we want
2. the sample is cut off at the surface 

## Porosity Calculations & Excel Data ##

The objective of this program is to calculate for porosity, the formula for porosity is: 

$$ porosity = \frac{area_{pores}}{area_{sample}} $$ 

- The area of all the pores was calculated in the for loop explained above. 
- The area of the sample is just the area of the max_area_index solved above. 

Thus, the porosity has already been found. Lines 261 - 265 show the calculations of porosity. The number should always be less than 1. *Make sure to **scale** your areas with (scale ** 2).* 


```python
# lines 261 - 265
pore_area = pore_area * (scale ** 2)
whole_area = areas[max_area_index] * (scale ** 2)
body_area = whole_area - pore_area
porosity = pore_area / whole_area
```

Save the data that Vurgun wants into an excel file using pandas: 


```python
# line 268
data.append([body_area, porosity])

# lines 276 - 277
df = pd.DataFrame(data=list(data), columns=['body area', 'porosity'])
df.to_excel(excel_directory)
```
