import pylab as plt
import numpy as np
import math
import imageio
from scipy.signal import convolve2d
from skimage.transform import resize
from scipy.ndimage.filters import generic_filter
from skimage.filters import threshold_otsu
"leggo il file"
fileID='0016p1_2_1.png'
#fileID='0025p1_4_1.pgm'
#fileID='0036p1_1_1.pgm'
image=imageio.imread(fileID)
'''
plt.figure()
plt.imshow(image)
plt.show()
'''

#%% parametri
smooth_factor= 8
scale_factor= 8
size_nhood_variance=5
NL=33

#%%processo l'img
k = np.ones((smooth_factor,smooth_factor))/smooth_factor**2
im_conv=convolve2d(image, k )
im_resized = resize(im_conv, (126,126), preserve_range=True)
im_norm = im_resized/np.max(im_resized)

plt.figure()
plt.imshow(im_norm)
plt.show()

#%%SEGMENTATION
"per il momento seleziono una roi a mano dell'immagine"
y1=47
y2=82
x1=43
x2=80

ROI=np.zeros(np.shape(im_norm))
ROI[y1:y2,x1:x2]=im_norm[y1:y2,x1:x2]
x_max, y_max=np.where(ROI==np.max(ROI))

#%%radial lines
R=math.ceil(np.sqrt((x2-x1)**2+(y2-y1)**2)/2)
center=[np.min(x_max),np.min(y_max)]
nhood=np.ones((size_nhood_variance,size_nhood_variance))

'definisco le funzioni che mi permettono il passaggio da coordinate cartesiane a polari'
def cart2pol(x, y):
    rho = np.sqrt(x**2 + y**2)
    phi = np.arctan2(y, x)
    return(rho, phi)

def pol2cart(rho, theta):
    x = rho * np.cos(theta)
    y = rho * np.sin(theta)
    return(x, y)

'creo i miei angoli come suddivisione in NL parti dello angolo giro'
theta=np.linspace(0,2*np.pi,NL)

'creo una matrice vuota'
Ray_masks=[]        

'creo un vettore contenente il valore dei miei raggi per un dato theta'
rho=np.arange(R)

for _ in range(0,NL):
    iir=[]
    jjr=[]
    for __ in range (0, R): 
        'passo dalle coordinate polari a quelle cartesiane'
        x,y = pol2cart(rho[__],theta[_])
        'centro la origine delle linee nel centro della lesione che ho dato in imput (center_x, center_y)'
        iir.append(center[0]+round(x))
        jjr.append(center[1]+round(y))

    'creo una tabella cioè vettori messi in verticale'
    line1=np.column_stack((iir,jjr))

    'ho creato una matrice (futura maschera) di zeri'
    Ray_mask=np.zeros(np.shape(ROI))

    for ___ in range(0,len(line1)):
        i=int(line1[___][0])
        j=int(line1[___][1])
        Ray_mask[i,j]=1 
    Ray_masks.append(Ray_mask)
plt.figure()
plt.imshow(Ray_masks[2])
plt.show()

#%% max variance points
'''funsione che binarizza img'''
def imbinarize(img):
    thresh = 0.01 #threshold_otsu(img)
    img[img >= thresh] = 1
    img[img < thresh] = 0
    return img

J = generic_filter(im_norm, np.std, size=size_nhood_variance)
'''
plt. figure()
plt.imshow(J, cmap='gray')
ptl.show()
'''

B_points=[]
roughborder=np.zeros(np.shape(im_norm))
p_x=[]
p_y=[]
for _ in range (0, 1):
    Jmasked=J*Ray_masks[_]     #J*raggi=maschera dell'img
    Jmasked=Jmasked*imbinarize(ROI)
    w = np.where(Jmasked==np.max(Jmasked))
    p_x.append(w[0])
    p_y.append(w[1])
    roughborder[w[0], w[1]]=im_norm[w[0], w[1]]
    plt.imshow(roughborder)
    

