import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import tensorflow as tf
import cv2
import numpy as np
from PIL import Image
from utils import save_image
import imageio.v3 as iio

# Constants
KERNEL_SIZE = 3
CHANNEL_COUNT = 3
IMAGE_SCALE = 256
DEFAULT_OUTPUT_SIZE = (256, 256)

class ImageSharpener:
    @staticmethod
    def create_sharpening_kernel_cv2():
        return np.array([[0, -1, 0],
                        [-1, 5, -1],
                        [0, -1, 0]])

    @staticmethod
    def create_sharpening_kernel_tf():
        kernel = np.zeros([KERNEL_SIZE, KERNEL_SIZE, CHANNEL_COUNT, CHANNEL_COUNT])
        center_value = 9.
        edge_value = -1.
        
        for i in range(KERNEL_SIZE):
            for j in range(KERNEL_SIZE):
                if i == 1 and j == 1:
                    kernel[i, j, :, :] = center_value
                else:
                    kernel[i, j, :, :] = edge_value
        return kernel

    def sharpen_with_cv2(self, input_image_path: str, output_image_path: str) -> None:
        """Sharpen image using OpenCV implementation"""
        image = cv2.imread(input_image_path)
        if image is None:
            raise ValueError("Unable to read the input image.")
        
        sharpening_kernel = self.create_sharpening_kernel_cv2()
        sharpened_image = cv2.filter2D(image, -1, sharpening_kernel)
        save_image(output_image_path, sharpened_image)
        print(f"Sharpened image saved to {output_image_path}")

    def sharpen_with_tensorflow(self, input_image_path: str, output_image_path: str) -> None:
        """Sharpen image using TensorFlow implementation"""
        img = Image.open(input_image_path)
        np_img = np.asarray(img, dtype='float32') / IMAGE_SCALE
        reshaped_img = np_img.reshape(1, *np_img.shape)

        kernel = self.create_sharpening_kernel_tf()
        
        tf.compat.v1.disable_eager_execution()
        x = tf.compat.v1.placeholder('float32', [1, None, None, CHANNEL_COUNT])
        w = tf.Variable(tf.cast(kernel, tf.float32))
        out = tf.nn.depthwise_conv2d(x, w, strides=[1, 1, 1, 1], padding='SAME')
        
        with tf.compat.v1.Session() as sess:
            sess.run(tf.compat.v1.global_variables_initializer())
            output = sess.run(out, feed_dict={x: reshaped_img})
            normalized = self._normalize_output(output)
            iio.imwrite(output_image_path, normalized, plugin='tifffile')

    def _normalize_output(self, output):
        max_value = np.amax(output)
        normalized = output / max_value
        normalized = (normalized * 255).round().astype(np.uint8)
        return np.squeeze(normalized)

if __name__ == "__main__":
    input_path = "images/image.jpg"
    output_path = "images/sharpened.jpg"
    
    sharpener = ImageSharpener()
    # Choose either method:
    sharpener.sharpen_with_tensorflow(input_path, output_path)
    # or
    # sharpener.sharpen_with_cv2(input_path, output_path)