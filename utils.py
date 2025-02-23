import io
import logging

import numpy as np
import pandas as pd
import pulse2percept as p2p
import yaml
from PIL import Image

from tensorflow.keras.layers import Conv2D, Dense, Flatten, MaxPooling2D
from tensorflow.keras.models import load_model
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.utils import to_categorical


def load_config(yaml_file):
    with open(yaml_file) as file:
        raw_content = yaml.load(file,Loader=yaml.FullLoader) # nested dictionary
    return raw_content

percept_model_argtypes = {
    'xrange': tuple,
    'yrange': tuple,
}

def get_percept_model(cfg):
    for param, type in percept_model_argtypes.items():
        if param in cfg['percept_model_args'] and cfg['percept_model_args'][param] is not None:
            cfg['percept_model_args'][param] = type(cfg['percept_model_args'][param])

    if cfg['percept_model'] == 'scoreboard':
        return p2p.models.ScoreboardModel(**cfg['percept_model_args'])
    elif cfg['percept_model'] == 'axon':
        return p2p.models.AxonMapModel(**cfg['percept_model_args'])
    else:
        raise NotImplementedError
    
def get_implant(cfg):
    if cfg['implant'] == 'PRIMA75':
        if cfg['implant_args'] is not None:
            return p2p.implants.PRIMA75(**cfg['implant_args'])
        else:
            return p2p.implants.PRIMA75()
    else:
        raise NotImplementedError

def get_dataset(cfg):
    if cfg['dataset'] == 'MNIST':
        return get_MNIST_dataset()
    else:
        raise NotImplementedError
    
def get_MNIST_dataset():
    train_df = pd.read_parquet("datasets/MNIST/train.parquet")
    train_images = []
    train_labels = []

    for i in range(train_df.shape[0]):
        if i % 1000 == 0: logging.debug(f"creating train image {i}")
        image = Image.open(io.BytesIO(train_df["image"].iloc[i]['bytes']))
        train_labels.append(train_df["label"].iloc[i])
        img_array = np.array(image)
        train_images.append(img_array)
    logging.debug(f"total train images: {len(train_images)}")

    test_df = pd.read_parquet("datasets/MNIST/test.parquet")
    test_images = []
    test_labels = []

    for i in range(test_df.shape[0]):
        if i % 1000 == 0: logging.debug(f"creating test image {i}")
        image = Image.open(io.BytesIO(test_df["image"].iloc[i]['bytes']))
        test_labels.append(test_df["label"].iloc[i])
        img_array = np.array(image)
        test_images.append(img_array)
    logging.debug(f"total test images: {len(test_images)}")

    return train_images, train_labels, test_images, test_labels

def get_classifier(cfg):
    if cfg['classifier'] == 'basic_cnn':
        return get_basic_cnn_classifier()
    else:
        raise NotImplementedError
    
def get_basic_cnn_classifier():
    model = Sequential()
    model.add(Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_uniform', input_shape=(28, 28, 1)))
    model.add(MaxPooling2D((2, 2)))
    model.add(Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_uniform'))
    model.add(Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_uniform'))
    model.add(MaxPooling2D((2, 2)))
    model.add(Flatten())
    model.add(Dense(100, activation='relu', kernel_initializer='he_uniform'))
    model.add(Dense(10, activation='softmax'))
    # compile model
    opt = SGD(learning_rate=0.01, momentum=0.9)
    model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['accuracy'])
    return model

def get_processed_dataset():
    X = np.load('Out/traindata.npz')
    Y = np.load('Out/trainlabels.npz')
    trainX = X['data']
    trainY = Y['data']
    # reshape dataset to have a single channel
    trainX = trainX.reshape((trainX.shape[0], 28, 28, 1))
    # one hot encode target values
    trainY = to_categorical(trainY)

    X = np.load('Out/testdata.npz')
    Y = np.load('Out/testlabels.npz')
    testX = X['data']
    testY = Y['data']
    # reshape dataset to have a single channel
    testX = testX.reshape((testX.shape[0], 28, 28, 1))
    # one hot encode target values
    testY = to_categorical(testY)

    return trainX, trainY, testX, testY

def get_trained_classifer(cfg):
    if cfg['classifier'] == 'basic_cnn':
        trained_model = load_model('Out/final_model.h5')
        return trained_model
    else:
        raise NotImplementedError