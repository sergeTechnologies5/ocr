import pyqrcode

url = pyqrcode.create('tesing')
url.svg('uca-url.svg', scale=8)
url.eps('uca-url.eps', scale=2)