import sys,os
from click.formatting import join_options
import requests
from PIL import Image, ImageDraw, ImageFont
import mimetypes
import click
import json
from os import path
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from easydict import EasyDict


class Uploader:
    def __init__(self, filename, file_host_url):
        self.filename = filename
        self.file_host_url = file_host_url

    @staticmethod
    def _progress_bar(monitor):
        progress = int(monitor.bytes_read/monitor.len*20)
        sys.stdout.write("\r[{}/{}] bytes |".format(monitor.bytes_read, monitor.len))
        sys.stdout.write("{}>".format("=" * progress))
        sys.stdout.write("{}|".format(" " * (20-progress)))
        sys.stdout.flush()

    def _multipart_post(self, data):
        encoder = MultipartEncoder(fields=data)
        monitor = MultipartEncoderMonitor(encoder, callback=self._progress_bar)
        r = requests.post(self.file_host_url,
                          data=monitor,
                          headers={'Content-Type': monitor.content_type})
        return r

    def _mimetype(self):
        _, extension = path.splitext(self.filename)
        if extension == '':
            extension = '.txt'
        mimetypes.init()
        try:
            return mimetypes.types_map[extension]
        except KeyError:
            return 'plain/text'

    def execute(self):
        raise NotImplementedError()


class CatboxUploader(Uploader):
    def __init__(self, filename):
        self.filename = filename
        self.file_host_url = "https://catbox.moe/user/api.php"

    def execute(self):
        file = open(self.filename, 'rb')
        try:
            data = {
                'reqtype': 'fileupload',
				'short':'pd412w',
                'fileToUpload':(file.name, file, self._mimetype())
            }
            response = self._multipart_post(data)
        finally:
            file.close()

        return response.text

uploader_classes = {
    "catbox": CatboxUploader,
}


def upload(host, name):
    uploader_class = uploader_classes[host]
    uploader_instance = uploader_class(name)
    result = uploader_instance.execute()
    return result

# Code above is from https://github.com/yukinotenshi/pyupload

RELEASE_DIR = 'D:\\photo\\release'
THUMBNAIL_DIR = 'D:\\Code\\yslib.github.io\\static\\thumbnails\\'
DB_JSON_FILE = 'D:\\Code\\yslib.github.io\\static\\image_data.json'
THUMBNAIL_SIZE = (400,300)
WATERMARK_TEXT='Lucida'


def encode_thumbnail_name(filename):
	return filename+'_thum.jpg'

def thumbnail(filename, watermark=False):
	img = Image.open(filename).convert("RGBA")
	(path,fullname) = os.path.split(filename)
	(fname, ext) = os.path.splitext(fullname)

	thumbsize = (int(img.size[0] * 0.08),int(img.size[1] * 0.08))
	thumbImg = img.resize(thumbsize,Image.BILINEAR)
	thumbname = encode_thumbnail_name(fname)
	thumbImg.convert("RGB").save(os.path.join(THUMBNAIL_DIR, thumbname))

	return thumbname

def add_img(filename, watermark=False):
	info = {
	'url': upload('catbox', filename),
	'thumbnailUrl':thumbnail(filename, watermark),
	'filename':filename,
	'name':'',
	'date':'',
	'location':'',
	'note':'',
	'device':''
	}
	return info

def open_imgs(input_dir, ext=None):
    for root, dirs, files in os.walk(input_dir, topdown=True):
        files = list(map(lambda x:os.path.join(input_dir,x),files))
        return files

def main(argv):

	# ret_url = upload('catbox',)
	with open(DB_JSON_FILE, 'r+',encoding='utf-8') as db:
		img_data = json.load(db)

	img_data = EasyDict(img_data)
	img_files = open_imgs(RELEASE_DIR)
	print(img_files)
	for each in img_files:
		info = add_img(each)
		obj = EasyDict(info)
		print(obj)
		img_data.images.append(obj)

	for i in img_data.images:
		print(i['url'])

	text = json.dumps(img_data)
	print(text)
	with open('output.json', 'w', encoding='utf-8') as out:
		out.write(text)



if __name__ == '__main__':
	main(sys.argv)