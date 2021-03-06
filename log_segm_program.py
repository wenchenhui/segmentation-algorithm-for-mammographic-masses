import pylab as plt
import numpy as np
import imageio
import os
import logging
import glob
import argparse
from PIL import Image
from scipy.signal import convolve2d
from skimage.transform import  rescale, resize
from skimage import measure
from skimage.filters import  median, threshold_yen , threshold_multiotsu, threshold_otsu
from scipy import ndimage
from draw_radial_line import draw_radial_lines
from define_border import define_border,distanza
logging.basicConfig(level=logging.INFO)
_description='metti la descrisione    yyy  ooo'


'''
This function pre-process the image.
'''
def process_img(image, smooth_factor, scale_factor):

    k = np.ones((smooth_factor,smooth_factor))/smoot,_factor**2
    im_conv = convolve2d(image, k )
    image_normalized = rescale(im_conv, 1/scale_factor)#/np.max(im_conv)
    im_log = 255*np.log10(image+1)
    im_log = im_log.astype('uint8')
    im_median = median(im_log, np.ones((5,5)))
    im_res = resize(im_median, (126,126))
    im_log_normalized = im_res#/np.max(im_res)

    return im_log_normalized, image_normalized


def find_center(x_max, y_max, y1, x1, y2, x2):
    
    '''if the point with maximum intensity is too far away from the ROI center,
    the center is chosen as the center of the rectangle. This is also the starting point of rays.'''
    
    if((np.abs(x_max-(x2-x1)/2)<(4/5)*(x1+(x2-x1)/2)) or (np.abs(y_max-(y2-y1)/2)<(4/5)*(y1+(y2-y1)/2))):
        x_center = x1+int((x2-x1)/2)
        y_center = y1+int((y2-y1)/2)
    else:
        #x_center = x_max[0]
        #y_center = y_max[0]
        x_center = x_max
        y_center = y_max
    center = [x_center, y_center]
    return center

def segmentation(file_path):
    logging.info('Reading files')
    fileID = glob.glob(file_path+'/*.png')
    for item in range(61,62):
    #for __,item in enumerate(fileID):
        f = open('center_list.txt', 'a')
        #f.write('#filename\t x_center\t y_center\t y1\t x1\t y2\t x2\n')
        image=imageio.imread(fileID[item])
        filename, file_extension = os.path.splitext(fileID[item])
        filename = os.path.basename(filename)
        path_out = 'result/'

        if (os.path.exists(path_out)==False):
            logging.info ('Creating folder for save results.\n')
            os.makedirs('result')
        mask_out = path_out + filename + '_mask' + file_extension

        logging.info('Defining parameters ')
        smooth_factor = 8
        scale_factor = 8
        size_nhood_variance = 5
        NL = 33
        R_scale = 5

        logging.info('Processing image {}'.format(filename))
        im_log_n, image_n= process_img(image, smooth_factor, scale_factor)
        plt.figure()
        plt.title('image {}'.format(filename))
        plt.imshow(image_n)
        conf=imageio.imread('/Users/luigimasturzo/Documents/esercizi_fis_med/large_sample_Im_segmented_ref/'+str(filename)+'_mass_mask.png')
        plt.imshow(conf, alpha=0.1)
        plt.colorbar()
        plt.grid()
        plt.show()
        

        logging.info('Starting the image segmentation.')
        decision  = 'si'

        while (decision != 'no'):
            logging.info('Enter ROIs coordinates that contains the mass.')
            y1=int(input('Enter y1: '))
            x1=int(input('Enter x1: '))
            y2=int(input('Enter y2: '))
            x2=int(input('Enter x2: '))
            ROI = np.zeros(np.shape(image_n))                
            ROI[y1:y2,x1:x2] = image_n[y1:y2,x1:x2]
            y_max,x_max = np.where(ROI==np.max(ROI))
    
            if (len(x_max) == 1):
                center = find_center(x_max, y_max, y1, x1, y2, x2)
            else:
                center = find_center(x_max[0], y_max[0], y1, x1, y2, x2)
                
            logging.info('Showing ROI and center.' )
            plt.figure()
            plt.title('ROI')
            plt.imshow(image_n)
            plt.imshow(ROI, alpha=0.3)
            plt.plot(center[0], center[1], 'r.')
            plt.colorbar()
            plt.show()
            print('Do you want to change your coordinates?')
            decision=input('Answer yes or no: ')

        f.write('{} \t {} \t {}\t {}\t {}\t {}\t {}\n'.format(filename, center[0], center[1], y1, x1, y2, x2))
        
        logging.info('First step: finding the border using Yen threshold.')
        image_n=image_n/np.max(ROI)
        image_yen = np.zeros(np.shape(image_n))
        print('image_n = ',np.mean(image_n))
        print('ROI =     ',np.mean(ROI/(np.max(ROI))))
        val = threshold_yen(image_n) #- threshold_otsu(image_n)
        image_yen[image_n >= val] = 1
        image_yen[image_n < val] = 0
        print('val =     ',val)

        if args.show != None:
            plt.figure()
            plt.title('first step -> Yen threshold')
            plt.imshow(image_yen*ROI)
            plt.plot(center[0], center[1], 'r.')
            plt.show()
        
        logging.info('Second step: refining border using Otsu double threshold')
        image_otsu = np.zeros((y2-y1,x2-x1))
        matrix = np.zeros(np.shape(image_n))
        image_otsu = image_yen[y1:y2,x1:x2]*(ROI[y1:y2,x1:x2]/np.max(ROI))
        val1, val2 = threshold_multiotsu(image_otsu)
        print('val1 =    ',val1)
        print('val2 =    ',val2)
        image_otsu[image_otsu>val2] = 0
        image_otsu[image_otsu<val1] = 0
        matrix[y1:y2,x1:x2] = image_otsu
        
        fill = np.zeros(np.shape(image_n))
        contours = measure.find_contours(matrix, 0)
        arr = contours[0].flatten('F').astype('int')
        y = arr[0:(int(len(arr)/2))]
        x = arr[(int(len(arr)/2)):]
        fill[y,x] = 1
        fill = ndimage.binary_fill_holes(fill).astype(int)

        if args.show != None:
            plt.figure()
            plt.title('second step -> Otsu double threshold')
            plt.imshow(fill)
            plt.plot(center[0], center[1], 'r.')
            plt.show()
        
        logging.info('Refining segmentation results.')
        R=int(distanza(x1,y1,x2,y2)/2)
        roughborder=np.zeros(np.shape(im_log_n))
        
        for _ in range(0,len(x)):
            print(len(x)-_)
            center_raff = [x[_], y[_]]
            Ray_masks_raff = draw_radial_lines(image_yen*ROI,center_raff,int(R/R_scale),NL)
            roughborder_raff= define_border(image_yen*ROI, NL, fill ,size_nhood_variance, Ray_masks_raff)
            roughborder+=roughborder_raff
        
        fill_raff=ndimage.binary_fill_holes(roughborder).astype(int)
        
        if args.show != None:
            plt.figure()
            plt.title('Final mask of segmented mass.')
            plt.imshow(fill_raff)
            plt.show()

            logging.info('Showing result')
            plt.figure()
            plt.title('Segmented mass.')
            plt.imshow(fill_raff*image_n)
            plt.colorbar()
            plt.show()

        plt.figure()
        plt.title('confronto.')
        plt.subplot(1,2,1)
        conf=imageio.imread('/Users/luigimasturzo/Documents/esercizi_fis_med/large_sample_Im_segmented_ref/'+str(filename)+'_mass_mask.png')
        plt.imshow(conf)
        plt.imshow(fill_raff, alpha=0.7)
        plt.subplot(1,2,2)
        plt.imshow(fill_raff)
        plt.show()

        fill_raff = fill_raff.astype(np.int8)
        im1 = Image.fromarray(fill_raff, mode='L')
        im1.save(mask_out)
        f.close()
    #return mask_out, fill_raff




if __name__ == '__main__':

    #logging.info('Luigi -> /Users/luigimasturzo/Documents/esercizi_fis_med/large_sample/*.png')
    #logging.info('Sara -> /Users/sarasaponaro/Desktop/exam_cmpda/large_sample/*.png')
    
    parser= argparse.ArgumentParser(description=_description)
    parser.add_argument('-i','--input', help='path to images folder')
    parser.add_argument('-s','--show', help='Do you want to show the images of process?')
    args=parser.parse_args()
    #segmentation(args.input)
    segmentation('/Users/luigimasturzo/Documents/esercizi_fis_med/large_sample')


    
    
    
