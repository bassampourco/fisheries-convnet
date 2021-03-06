# -*- coding: utf-8 -*-

# Convolutional Neural Network
MODEL_PATH = './trained_models/'
IMAGE_PATH = './data/localized_images/'
# IMAGE_PATH = './data/original_images/'
IMAGE_SHAPE = (90, 160, 3)
# IMAGE_SHAPE = (720, 1280, 3)
BATCH_SIZE = 64
MAX_STEPS = 1500
ALPHA = 1e-3
BETA = 1e-2

# Object Detection
HAARCASCADE = './app/cv/fishcascade/'
BOUNDINGBOX = './app/cv/bb/'
BASE_URL = 'http://image-net.org/api/text/imagenet.synset.geturls?wnid={0}'
# CV_SAMPLE_PATH = './data/native_cv_samples/'
CV_SAMPLE_PATH = './data/cv_samples/'
SYNSET_ID_POS = {
                    'Tuna_Bluefin': 'n02627292',
                    'Tuna_Yellowfin': 'n02627532',
                    'Tuna_Albacore': 'n02627037',
                    'DOL': 'n02581957',
                    'LAG': 'n02545841',
                    'SHA': 'n01484285',
                    'OTHER': 'n02512053'
}
SYNSET_ID_NEG = {
                    'ocean': 'n09376198',
                    'people': 'n07942152',
                    'poop deck': 'n03982642',
                    'equipment': 'n03294048',
                    'sea boat': 'n04158807',
                    'waves': 'n13868944'
}
SYNSET_NUM_POS = 10
SYNSET_NUM_NEG = 1e4
HAARPARAMS = dict(
    scaleFactor=6,
    # 0 minNeighbors 0 so that there is minimum change missing fish.
    minNeighbors=2,
    minSize=(50, 50),
    maxSize=(700, 700)
)
