import hashlib
import os

from datetime import datetime, date, timedelta
from pathlib import Path
from threading import Thread

from PIL import Image

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect

from .models import Picture


EXIF_DATE = 36867
EXIF_ORIENTATION = 274

running = False


def is_member(user):
    return user.groups.filter(name='member').exists()


@login_required
@user_passes_test(is_member, login_url='/forbidden', redirect_field_name=None)
def index(req):
    get_date = req.GET.get('date', None)
    if get_date is None:
        first_pic = Picture.objects.order_by('-date').first()
        if first_pic is None:
            return render(req, "app/index.html", {
                            "pictures": (),
                            "day": "No pictures in database",
                         })
        requested_date = first_pic.date.date()
    else:
        requested_date = date.fromisoformat(get_date)
    pics = Picture.objects.filter(
            date__year=requested_date.year,
            date__month=requested_date.month,
            date__day=requested_date.day).order_by('date')

    days = sorted(set(datetime.astimezone().date() for datetime in Picture.objects.values_list('date', flat=True).distinct().order_by('-date')))[::-1]

    return render(req, "app/index.html", {
        "pictures": pics,
        "requested_date": requested_date,
        "days": days,
        # "next_day": next_day,
        # "prev_day": prev_day
        })
    # return render(req, "app/index.html", {"days": days})


def forbidden(req):
    return render(req, "app/forbidden.html", status=403)


def login(req):
    return render(req, "app/login.html")


@login_required
@user_passes_test(is_member, login_url='/forbidden', redirect_field_name=None)
def catalog(req):
    global running
    if not running:
        running = True
        t = Thread(target=do_catalog_work)
        t.start()
    return redirect('index')

def do_catalog_work():
    global running
    # do stuff
    for photo_dir in settings.PHOTO_DIRS:
        for (root, dirs, files) in os.walk(photo_dir):
            for filename in files:
                path = root / Path(filename)
                if path.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'):
                    continue  # not a picture file name

                assert_or_save(path, photo_dir)
    running = False


def assert_or_save(path, photo_dir):
    # get md5
    name = path.relative_to(photo_dir)
    try:
        Picture.objects.get(path=path.relative_to(photo_dir))
        return
    except Picture.DoesNotExist:
        pass
    h = get_md5_for_filename(path)
    try:
        Picture.objects.get(checksum=h)
        return  # because we already cataloged it
    except Picture.DoesNotExist:
        pass  # it's new, we'll process outside the try/except

    im = Image.open(path)
    exif = im._getexif()

    #rotation

    if exif[EXIF_ORIENTATION] == 3:
        im=im.rotate(180, expand=True)
    elif exif[EXIF_ORIENTATION] == 6:
        im=im.rotate(270, expand=True)
    elif exif[EXIF_ORIENTATION] == 8:
        im=im.rotate(90, expand=True)
    
    width, height = im.size

    # date
    date = datetime.strptime(
        exif[EXIF_DATE], '%Y:%m:%d %H:%M:%S').astimezone()


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
