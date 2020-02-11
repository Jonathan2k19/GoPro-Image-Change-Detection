"""
Using unofficial GoPro API to detect changes between to images.
Comparison time is around one minute
"""

from PIL import Image
import requests
import sys
import time


def setup_cam():
    global all_adjusted
    try:
        json_stat = requests.get('http://10.5.5.9/gp/gpControl/status').json()
    except requests.exceptions.ConnectionError:
        print('Connection error')
        sys.exit()
    # adjust settings
    if json_stat['status']['43'] != 1:   # photo mode
        requests.get('http://10.5.5.9/gp/gpControl/command/mode?p=1')
        print('changed to photo mode')
    else:
        print('photo mode already set')
    if json_stat['settings']['17'] != 3:  # megapixels (5mp wide == 3)
        requests.get('http://10.5.5.9/gp/gpControl/setting/17/3')
        print('set resolution to 5MP wide')
    else:
        print('5mp already set')
    if json_stat['settings']['20'] != 0:  # spot meter (off == 0)
        requests.get('http://10.5.5.9/gp/gpControl/setting/20/0')
        print('turned spot meter off')
    else:
        print('spot meter already set')
    if json_stat['settings']['21'] != 0:  # protune (off == 0)
        requests.get('http://10.5.5.9/gp/gpControl/setting/21/0')
        print('turned protune off')
    else:
        print('protune already set')
    all_adjusted = True


def take_photo():
    while not all_adjusted:
        time.sleep(0.1)
    requests.get('http://10.5.5.9/gp/gpControl/command/shutter?p=1')
    global took_pic
    took_pic = True
    print('Took photo.')


def get_latest_img():
    global latest_jpg, d_name, root, num, format, total_vids
    json_stat = requests.get('http://10.5.5.9/gp/gpControl/status').json()
    total_batch_pics = json_stat['status']['36']
    total_vids = json_stat['status']['37']
    json_media = requests.get('http://10.5.5.9/gp/gpMediaList').json()
    time.sleep(0.5)
    d_name = json_media['media'][0]['d']
    file_names = []
    jpgs = []
    for pic in range(total_vids + total_batch_pics):
        file_names.append(json_media['media'][0]['fs'][pic]['n'])
    if not file_names:
        print('No files available.')
        sys.exit()
    for file in file_names:
        # get jpg only
        if file[-1] == chr(71):
            jpgs.append(file)
        else:
            pass
    latest_jpg = jpgs[-1]   # second latest because latest isn´t yet loaded in media
    latest_jpg = list(latest_jpg)  # strings are immutable so I can´t change characters in place -> string as list
    root = latest_jpg[0: 4]
    num = latest_jpg[4: 8]
    format = latest_jpg[8: 12]
    num_int = int(num[0] + num[1] + num[2] + num[3])  # length without leading zeros
    num_str = str(num_int)
    length = len(num_str)
    miss_zero = 4 - length  # how many leading zeros to append
    latest_jpg = ''.join(root) + str(miss_zero * str(0)) + num_str + ''.join(format)
    compare_jpg = ''.join(root) + str(miss_zero * str(0)) + str(num_int-1) + ''.join(format)
    lat = requests.get('http://10.5.5.9/videos/DCIM/' + str(d_name) + '/' + latest_jpg, allow_redirects=True)
    open('latest.JPG', 'wb').write(lat.content)
    comp = requests.get('http://10.5.5.9/videos/DCIM/' + str(d_name) + '/' + compare_jpg, allow_redirects=True)
    open('compare.JPG', 'wb').write(comp.content)
    print('Latest image and compare image downloaded')


def prep_img():
    global img1, img2, w1, w2, h1, h2
    raw1 = Image.open('latest.JPG')
    raw2 = Image.open('compare.JPG')
    w1 = raw1.width
    h1 = raw1.height
    img1 = raw1.resize((100, 100))

    w2 = raw2.width
    h2 = raw2.height
    img2 = raw2.resize((100, 100))
    print('Images prepared')


def compare_img():
    data1 = list(img1.getdata())
    data2 = list(img2.getdata())
    print('Data1: ' + str(data1))
    print('Data2: ' + str(data2))
    r = []
    g = []
    b = []
    for rgb1, rgb2 in zip(data1, data2):
        # all differences val1, val2 separated by color
        diff_r = abs(rgb1[0] - rgb2[0])
        diff_g = abs(rgb1[1] - rgb2[1])
        diff_b = abs(rgb1[2] - rgb2[2])
        r.append(diff_r)
        g.append(diff_g)
        b.append(diff_b)
        # total r, g, b differences
        c_r = 0
        c_g = 0
        c_b = 0
        for j, k, l in zip(r, g, b):
            c_r += j
            c_g += k
            c_b += l
            total_r = c_r / len(r)
            total_g = c_g / len(g)
            total_b = c_b / len(b)
    # test value nine is relatively exact
    if (total_r < 9) and (total_g < 9) and (total_b < 9):
        print('NO CHANGE')
    else:
        print('CHANGE')


def img_change_detection():
    setup_cam()
    for i in range(3):
        if not all_adjusted:
            setup_cam()
        else:
            pass
        take_photo()
        start_time = time.time()
        get_latest_img()
        prep_img()
        compare_img()
        runtime = time.time() - start_time
        print('It took ' + str(runtime) + 's')
        print('Done with comparison: ' + str(i))


img_change_detection()
