import sys
from os import path, mkdir
from PIL import Image, ImageOps, ImageDraw

class Config():

    LEFT    =   0x0
    CENTER  =   0x1
    RIGHT   =   0x2

    def __init__(self, crop_type, size=(450, 450)):
        self.type = crop_type
        self.size = size
        self.path = Rect(*self.getMap())

    def getMap(self):
        if self.type == self.LEFT:
            return (328, 3, 778, 454)
        if self.type == self.CENTER:
            return (556, 3, 1005, 454)
        if self.type == self.RIGHT:
            return (782, 3, 1232, 454)


class Rect():

    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    def check_dimensions(self, rect):
        if rect.left < self.left or rect.left > rect.right - 1:
            return False, 'Invalid left value: %d (Min: %d, Max: %d).' % (rect.left, self.left, rect.right - 1)
        if rect.right < rect.left + 1 or rect.right > self.right:
            return False, 'Invalid right value: %d (Min: %d, Max: %d).' % (rect.right, rect.left + 1, self.right)
        if rect.top < self.top or rect.top > rect.bottom - 1:
            return False, 'Invalid top value: %d (Min: %d, Max: %d).' % (rect.top, self.top, rect.bottom - 1)
        if rect.bottom < rect.top + 1 or rect.bottom > self.bottom:
            return False, 'Invalid bottom value: %d (Min: %d, Max: %d).' % (rect.bottom, rect.top + 1, self.bottom)
        return True, None


class Cropper():

    def __init__(self, file):
        if not path.exists(file):
            raise FileExistsError('Unable to find image file at: %s' % path)
        self.exports_count = 0
        self.basedir = path.dirname(file)
        self.filename, self.extension = path.splitext(path.basename(file))
        self.image = Image.open(file)
        self.width, self.height = self.image.size
        self.rect = Rect(0, 0, self.width, self.height)
        print('[%s] Loaded: [W: %d, H: %d]' % (self.filename, self.width, self.height))

    def crop(self, rect):
        success, error = self.rect.check_dimensions(rect)
        if not success:
            raise ValueError(error)
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        self.cropped = self.image.crop((rect.left, rect.top, rect.right, rect.bottom))
        print("[%s] Cropped: [W: %d, H: %d]" % (self.filename, width, height))

    def crop_ellipse(self, mask_size):
        tmp_size = tuple(map(lambda x: x * 2, mask_size))
        mask = Image.new('L', tmp_size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0) + tmp_size, fill=255)
        mask = mask.resize(mask_size, Image.ANTIALIAS)
        self.ellipse = ImageOps.fit(self.cropped, mask_size, method=Image.LANCZOS, centering=(0.5, 0.5))
        self.ellipse.putalpha(mask)
        print("[%s] Ellipse: [W: %d, H: %d]" % ((self.filename,) + mask_size))

    def crop_all(self):
        configs = (
            Config(Config.LEFT),
            Config(Config.CENTER),
            Config(Config.RIGHT)
        )
        for config in configs:
            self.crop(config.path)
            self.resize(config.size)
            self.crop_ellipse(config.size)
            self.export()
            self.cropped.close()
            self.ellipse.close()
        print("[%s] Done." % self.filename)

    def resize(self, resize):
        self.cropped = self.cropped.resize(resize, Image.LANCZOS)
        print("[%s] Resized: [W: %d, H: %d]" % ((self.filename,) + resize))

    def export(self, png=True, jpeg=True):
        if not png and not jpeg:
            raise ValueError('Either PNG or JPEG must be true.')
        self.exports_count += 1
        output_dir = path.join(self.basedir, self.filename)
        if not path.isdir(output_dir):
            mkdir(output_dir)
        if png:
            filename_png = '%s-%d.png' % (self.filename, self.exports_count)
            output = path.join(output_dir, filename_png)
            self.cropped.save(output, quality=100)
        if jpeg:
            filename_jpeg = '%s-%d.jpg' % (self.filename, self.exports_count)
            output = path.join(output_dir, filename_jpeg)
            self.cropped.save(output, quality=100)
        if not self.ellipse is None:
            ellipse_filename = '%s-%d_ellipse.png' % (self.filename, self.exports_count)
            output = path.join(output_dir, ellipse_filename)
            self.ellipse.save(output, quality=100)

    def show(self, image=None):
        (image if not image is None else self.cropped).show()

    def close(self):
        self.image.close()
        print("[%s] Released." % self.filename)


if __name__ == "__main__":
    for file in sys.argv[1:]:
        image = Cropper(file)
        image.crop_all()
        image.close()