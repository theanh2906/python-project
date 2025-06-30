import matplotlib.pyplot as plt
from IPython.display import Image
from PIL import Image, ImageFilter


def image_processing():
    img = Image.open("images/image.jpg")
    if img.mode == 'P':
        img = img.convert('RGB')
    blurred = img.filter(ImageFilter.BLUR)
    contour = img.filter(ImageFilter.CONTOUR)
    detail = img.filter(ImageFilter.DETAIL)
    edge_enhance = img.filter(ImageFilter.EDGE_ENHANCE)
    edge_enhance_more = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
    emboss = img.filter(ImageFilter.EMBOSS)
    find_edges = img.filter(ImageFilter.FIND_EDGES)
    sharpen = img.filter(ImageFilter.SHARPEN)
    smooth = img.filter(ImageFilter.SMOOTH)
    smooth_more = img.filter(ImageFilter.SMOOTH_MORE)
    gaussian_blur = img.filter(ImageFilter.GaussianBlur(radius=10))

    fig, axes = plt.subplots(4, 3, figsize=(15, 15))
    axes = axes.flatten()

    filters = [
        ("Blurred", blurred),
        ("Contour", contour),
        ("Detail", detail),
        ("Edge Enhance", edge_enhance),
        ("Edge Enhance More", edge_enhance_more),
        ("Emboss", emboss),
        ("Find Edges", find_edges),
        ("Sharpen", sharpen),
        ("Smooth", smooth),
        ("Smooth More", smooth_more),
        ("Gaussian Blur", gaussian_blur),
    ]

    for ax, (title, image) in zip(axes, filters):
        ax.imshow(image)
        ax.set_title(title)
        ax.axis("off")

    # Hide any unused subplots
    for ax in axes[len(filters):]:
        ax.axis("off")

    plt.tight_layout()
    plt.show()

if __name__ =="__main__":
    image_processing()