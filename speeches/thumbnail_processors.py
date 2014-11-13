# easy_thumbnails face cropping processor
# Much of the below taken from http://stackoverflow.com/a/13243712/669631

try:
    import cv
    faceCascade = cv.Load('/usr/share/opencv/haarcascades/haarcascade_frontalface_alt.xml')
except:
    faceCascade = False

# Select one of the haarcascade files:
#   haarcascade_frontalface_alt.xml  <-- Best one?
#   haarcascade_frontalface_alt2.xml
#   haarcascade_frontalface_alt_tree.xml
#   haarcascade_frontalface_default.xml
#   haarcascade_profileface.xml


def detectFaces(im):
    # This function takes a PIL image and finds the patterns defined in the
    # haarcascade function modified from: http://www.lucaamore.com/?p=638

    # Convert a PIL image to a greyscale cv image
    # from: http://pythonpath.wordpress.com/2012/05/08/pil-to-opencv-image/
    im = im.convert('L')
    cv_im = cv.CreateImageHeader(im.size, cv.IPL_DEPTH_8U, 1)
    cv.SetData(cv_im, im.tostring(), im.size[0])

    # variables
    min_size = (20, 20)
    haar_scale = 1.1
    min_neighbors = 3
    haar_flags = 0

    # Equalize the histogram
    cv.EqualizeHist(cv_im, cv_im)

    # Detect the faces
    faces = cv.HaarDetectObjects(
        cv_im, faceCascade, cv.CreateMemStorage(0),
        haar_scale, min_neighbors, haar_flags, min_size
        )

    return faces


def face_crop(im, size, face=False, **kwargs):
    if not face or not faceCascade:
        return im

    source_x, source_y = [int(v) for v in im.size]

    faces = detectFaces(im)
    if faces:
        cropBox = [0, 0, 0, 0]
        for face, n in faces:
            if face[2] > cropBox[2] or face[3] > cropBox[3]:
                cropBox = face

        xDelta = int(max(cropBox[2] * 0.25, 0))
        yDelta = int(max(cropBox[3] * 0.25, 0))

        # Convert cv box to PIL box [left, upper, right, lower]
        box = [
            max(cropBox[0] - xDelta, 0),
            max(cropBox[1] - yDelta, 0),
            min(cropBox[0] + cropBox[2] + xDelta, source_x - 1),
            min(cropBox[1] + cropBox[3] + yDelta, source_y - 1)
            ]
        im = im.crop(box)

    return im
