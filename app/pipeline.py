# -*- coding: utf-8 -*-
"""
pipeline

data pipeline from image root folder to processed tensors of train test batches
for images and labels
"""


import os
import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn import model_selection


def folder_traverse(root_dir, ext=('.jpg')):
    """map all image-only files in a folder"""
    if not os.path.exists(root_dir):
        raise RuntimeError('{0} doesn\'t exist.'.format(root_dir))
    file_structure = dict()
    # using os.walk instead of new os.scandir for backward compatibility
    for root, _, files in os.walk(root_dir):
        image_list = [i for i in files if i.endswith(ext)]
        if image_list:
            file_structure[root] = image_list
    return file_structure


def generate_data_skeleton(root_dir, valid_size=None):
    """turn file structure into human-readable pandas dataframe"""
    file_structure = folder_traverse(root_dir)
    reversed_fs = {k + '/' + f: k.split('/')[-1]
                   for k, v in file_structure.items() for f in v}
    df = pd.DataFrame.from_dict(data=reversed_fs, orient='index').reset_index()
    df.rename(columns={'index': 'filename', 0: 'species'}, inplace=True)
    df.sort_values(by=['species', 'filename'], inplace=True)
    df.reset_index(inplace=True, drop=True)
    df['labels'] = df['species'].astype('category').cat.codes

    X, y = np.array(df['filename']), np.array(df['labels'])

    if valid_size:
        X_train, X_valid, y_train, y_valid = model_selection.train_test_split(
            X, y, test_size=valid_size, stratify=y)
        print('training: {0} samples; validation: {1} samples.'.format(
            X_train.shape[0], X_valid.shape[0]))
        return X_train, y_train, X_valid, y_valid
    else:
        print('test: {0} samples.'.format(X.shape[0]))
        return X, y


def deserialize_json(rootdir, ext=('json')):
    """concatenate and deserialize bounding boxes in json format"""

    import json
    bbox_file_structure = folder_traverse(rootdir, ext=ext)
    annotations = list()
    for folder, filelist in bbox_file_structure.items():
        for filename in filelist:
            with open(folder+filename) as f:
                label = json.load(f)
                annotations.append(label)
    # individual json object from nested lists
    annotations_dict = {json_object['filename']: json_object for nested_list
                        in annotations for json_object in nested_list}
    return annotations_dict


def make_queue(paths_to_image, labels, num_epochs=None, shuffle=True):
    """returns an Ops Tensor with queued image and label pair"""
    images = tf.convert_to_tensor(paths_to_image, dtype=tf.string)
    labels = tf.convert_to_tensor(labels, dtype=tf.uint8)
    input_queue = tf.train.slice_input_producer(
        tensor_list=[images, labels],
        num_epochs=num_epochs,
        shuffle=shuffle)
    return input_queue


def decode_transform(input_queue, shape=None, standardize=True):
    """a single decode and transform function that applies standardization with
    mean centralisation.
    """
    # input_queue allows slicing with 0: path_to_image, 1: encoded label
    label_queue = input_queue[1]
    one_hot_label_queue = tf.one_hot(
                                indices=label_queue,
                                depth=8,
                                on_value=1,
                                off_value=0)

    image_queue = tf.read_file(input_queue[0])
    original_image = tf.image.decode_jpeg(image_queue, channels=shape[2])

    # apply bounding box here


    # crop larger images (e.g. 1280*974) to 1280*720, this func doesn't resize.
    cropped_image_content = tf.image.resize_image_with_crop_or_pad(
                                image=original_image,
                                target_height=720,
                                target_width=1280)

    # resize cropped images to desired shape
    resize_image_content = tf.image.resize_images(
                                images=cropped_image_content,
                                size=[shape[0], shape[1]])

    resize_image_content.set_shape(shape)

    # apply standardization
    if standardize:
        std_image_content = tf.image.per_image_standardization(
                                resize_image_content)
        processed_image = std_image_content
    elif not standardize:
        processed_image = resize_image_content

    return processed_image, one_hot_label_queue


def batch_generator(image, label, batch_size=None, shuffle=True):
    """turn data queue into batches"""
    if shuffle:
        return tf.train.shuffle_batch(
                            tensors=[image, label],
                            batch_size=batch_size,
                            num_threads=4,
                            capacity=1e3,
                            min_after_dequeue=200,
                            allow_smaller_final_batch=True)
    elif not shuffle:
        return tf.train.batch(
                            tensors=[image, label],
                            batch_size=batch_size,
                            num_threads=1,
                            # thread number must be one to keep it unshuffled.
                            capacity=1e3,
                            allow_smaller_final_batch=True)


def data_pipe(paths_to_image,
              labels,
              num_epochs=None,
              batch_size=None,
              shape=None,
              shuffle=True):
    """so one-in-all from data directory to iterated data feed in batches"""
    resized_image_queue, label_queue = decode_transform(make_queue(
                                            paths_to_image,
                                            labels,
                                            num_epochs=num_epochs,
                                            shuffle=shuffle),
                                            shape=shape)
    image_batch, label_batch = batch_generator(
                                            resized_image_queue,
                                            label_queue,
                                            batch_size=batch_size,
                                            shuffle=shuffle)
    return image_batch, label_batch


def multi_threading(func):
    """decorator using tensorflow threading ability."""
    def wrapper(*args, **kwargs):
        coord = tf.train.Coordinator()
        threads = tf.train.start_queue_runners(coord=coord)
        func_output = func(*args, **kwargs)
        try:
            coord.request_stop()
            coord.join(threads, stop_grace_period_secs=5)
        except (tf.errors.CancelledError, RuntimeError) as e:
            pass
        return func_output
    return wrapper
