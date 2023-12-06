import os
import hashlib

from pathlib import Path
from datetime import datetime

from PIL import Image

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings

from .models import Picture


EXIF_DATE = 36867


def is_member(user):
    return user.groups.filter(name='member').exists()


@login_required
@user_passes_test(is_member, login_url='/forbidden', redirect_field_name=None)
def index(req):
    pics = Picture.objects.order_by('-date')
    days = {}
    for pic in pics:
        day = pic.date.strftime('%Y-%m-%d')
        if day not in days.keys():
            days[day] = []
        days[day].append(pic)

    return render(req, "app/index.html", {"days": days})


def forbidden(req):
    return render(req, "app/forbidden.html", status=403)


def login(req):
    return render(req, "app/login.html")


@login_required
@user_passes_test(is_member, login_url='/forbidden', redirect_field_name=None)
def catalog(req):
    # do stuff
    for photo_dir in settings.PHOTO_DIRS:
        for (root, dirs, files) in os.walk(photo_dir):
            for filename in files:
                path = root / Path(filename)
                if path.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'):
                    continue  # not a picture file name

                assert_or_save(path, photo_dir)

    # redirect to index
    return redirect('index')


def assert_or_save(path, photo_dir):
    # get md5
    h = get_md5_for_filename(path)
    try:
        Picture.objects.get(checksum=h)
        return  # because we already cataloged it
    except Picture.DoesNotExist:
        pass  # it's new, we'll process outside the try/except

    im = Image.open(path)
    width, height = im.size

    # date
    date = datetime.strptime(
        im._getexif()[EXIF_DATE], '%Y:%m:%d %H:%M:%S').astimezone()

    # thumbnail
    size = 256
    thumb = Path(f'{h}-{size}{path.suffix}')
    im.thumbnail((size, size))
    im.save(settings.THUMB_DIR / thumb)

    # save
    Picture.objects.create(checksum=h, path=path.relative_to(
        photo_dir), small_path=thumb, date=date, width=width, height=height)


def get_md5_for_filename(filename):
    return hashlib.md5(open(filename, 'rb').read()).hexdigest()
