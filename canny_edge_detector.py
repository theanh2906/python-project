import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import convolve, gaussian_filter
import imageio.v3 as iio # use imageio for image reading and display

def canny_edge_detector(im, blur = 1, high_threshold = 91, low_threshold = 31):
    im = np.array(im, dtype=float) #Convert to float to prevent clipping values

    #Gaussian blur to reduce noise
    im2 = gaussian_filter(im, blur)

    #Use sobel filters to get horizontal and vertical gradients
    im3h = convolve(im2,[[-1,0,1],[-2,0,2],[-1,0,1]])
    im3v = convolve(im2,[[1,2,1],[0,0,0],[-1,-2,-1]])

    #Get gradient and direction
    grad = np.power(np.power(im3h, 2.0) + np.power(im3v, 2.0), 0.5)
    theta = np.arctan2(im3v, im3h)
    theta_q = (np.round(theta * (5.0 / np.pi)) + 5) % 5 #Quantize direction

    #Non-maximum suppression
    grad_sup = grad.copy()
    for r in range(im.shape[0]):
        for c in range(im.shape[1]):
            #Suppress pixels at the image edge
            if r == 0 or r == im.shape[0]-1 or c == 0 or c == im.shape[1] - 1:
                grad_sup[r, c] = 0
                continue
            tq = theta_q[r, c] % 4

            if tq == 0: #0 is E-W (horizontal)
                if grad[r, c] <= grad[r, c-1] or grad[r, c] <= grad[r, c+1]:
                    grad_sup[r, c] = 0
            if tq == 1: #1 is NE-SW
                if grad[r, c] <= grad[r-1, c+1] or grad[r, c] <= grad[r+1, c-1]:
                    grad_sup[r, c] = 0
            if tq == 2: #2 is N-S (vertical)
                if grad[r, c] <= grad[r-1, c] or grad[r, c] <= grad[r+1, c]:
                    grad_sup[r, c] = 0
            if tq == 3: #3 is NW-SE
                if grad[r, c] <= grad[r-1, c-1] or grad[r, c] <= grad[r+1, c+1]:
                    grad_sup[r, c] = 0

    #Double threshold
    strong_edge = (grad_sup > high_threshold)

    #Strong has value 2, weak has value 1
    thresholded_edges = np.array(strong_edge, dtype=np.uint8) + (grad_sup > low_threshold)

    #Tracing edges with hysteresis
    #Find weak edge pixels near strong edge pixels
    final_edges = strong_edge.copy()
    current_pixels = []
    for r in range(1, im.shape[0]-1):
        for c in range(1, im.shape[1]-1):
            if thresholded_edges[r, c] != 1:
                continue #Not a weak pixel

            #Get 3x3 patch
            local_patch = thresholded_edges[r-1:r+2,c-1:c+2]
            patch_max = local_patch.max()
            if patch_max == 2:
                current_pixels.append((r, c))
                final_edges[r, c] = 1

    #Extend strong edges based on current pixels
    while len(current_pixels) > 0:
        new_pix = []
        for r, c in current_pixels:
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    if dr == 0 and dc == 0: continue
                    r2 = r+dr
                    c2 = c+dc
                    if thresholded_edges[r2, c2] == 1 and final_edges[r2, c2] == 0:
                        #Copy this weak pixel to final result
                        new_pix.append((r2, c2))
                        final_edges[r2, c2] = 1
        current_pixels = new_pix

    return final_edges

if __name__=="__main__":
    im = iio.imread("images/background_landscape.png", mode="L") #Open image, convert to greyscale
    final_edges = canny_edge_detector(im)
    plt.title('Original')
    plt.imshow(final_edges)
    plt.axis('off')
    plt.show()