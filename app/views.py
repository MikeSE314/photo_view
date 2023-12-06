import time
import os
import hashlib
from pathlib import Path
from datetime import datetime

from PIL import Image

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings

from .models import Picture


@login_required
def index(req):
    pics = Picture.objects.order_by('-date')
    return render(req, "app/index.html", {"pictures": pics})


def login(req):
    return render(req, "app/login.html")


@login_required
def catalog(req):
    # do stuff
    for photo_dir in settings.PHOTO_DIRS:
        for (root, dirs, files) in os.walk(photo_dir):
            for filename in files:
                path = root / Path(filename)
                if path.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'):
                    continue  # not a picture file name

                assert_or_save(path)

    # redirect to index
    return redirect('index')


def assert_or_save(path):
    # get md5
    h = get_md5_for_filename(path)
    try:
        Picture.objects.get(checksum=h)
        return  # because we already cataloged it
    except Picture.DoesNotExist:
        pass  # it's new, we'll process outside the try/except
    
    im = Image.open(path)

    # date
    date = datetime.strptime(im._getexif()[36867], '%Y:%m:%d %H:%M:%S')

    # thumbnail
    size = 256
    thumb = Path(f'{h}-{size}{path.suffix}')
    im.thumbnail((size, size))
    im.save(settings.THUMB_DIR / thumb)

    # save
    Picture.objects.create(checksum=h, path=path.name, small_path=thumb, date=date)


def get_md5_for_filename(filename):
    return hashlib.md5(open(filename, 'rb').read()).hexdigest()


