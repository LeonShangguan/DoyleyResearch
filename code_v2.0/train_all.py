# -*- coding: utf-8 -*-
"""
Created on 2019-3-11
@author: LeonShangguan
"""
import argparse
import tensorflow as tf
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau

from segmentation_models import Unet
from segmentation_models.losses import bce_jaccard_loss
from segmentation_models.metrics import iou_score

from dataset import Carotid_DataGenerator
from dataset import get_train_val_split


def train(backbone,
          load_pretrain,
          data_path,
          split_path,
          save_path,
          n_split=5,
          seed=960630,
          batch_size=4,
          fold=0):

    # split by all data
    get_train_val_split(data_path=data_path+"/images/",
                        save_path=split_path,
                        n_splits=n_split,
                        seed=seed)

    # split by folders
    # get_train_val_split(data_path=data_path+'images/',
    #                     save_path=split_path,
    #                     n_splits=n_split,
    #                     seed=seed)

    if load_pretrain is not None:
        model = tf.keras.models.load_model(load_pretrain, compile=False)
    elif backbone is not None:
        model = Unet(backbone, classes=1, encoder_weights='imagenet')
    else:
        model = Unet(classes=1, encoder_weights='imagenet')

    model.compile('Adam', loss=bce_jaccard_loss, metrics=[iou_score])
    # model.summary()

    # split by folder
    train_data = Carotid_DataGenerator(
        df_path=split_path+'split/train_fold_{}_seed_{}.csv'.format(fold, seed),
        image_path=data_path + '/images/',
        mask_path=data_path + '/masks/',
        batch_size=batch_size,
        target_shape=(512, 512),
        augmentation=True,
        shuffle=False)
    val_data = Carotid_DataGenerator(
        df_path=split_path + 'split/val_fold_{}_seed_{}.csv'.format(fold, seed),
        image_path=data_path + '/images/',
        mask_path=data_path + '/masks/',
        batch_size=batch_size,
        target_shape=(512, 512),
        augmentation=False,
        shuffle=False)

    callbacks = [EarlyStopping(monitor='val_loss',
                               patience=8,
                               verbose=1,
                               min_delta=1e-4),
                 ReduceLROnPlateau(monitor='val_loss',
                                   factor=0.1,
                                   patience=4,
                                   verbose=1,
                                   epsilon=1e-4),
                 ModelCheckpoint(monitor='val_loss',
                                 filepath=save_path+f"/{backbone}_fold{fold}.hdf5",
                                 verbose=True,
                                 save_best_only=True)]

    model.fit_generator(train_data,
                        validation_data=val_data,
                        epochs=10,
                        callbacks=callbacks,
                        verbose=1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Get input parameters.")

    parser.add_argument('--backbone', type=str, default=None)
    parser.add_argument('--load_pretrain', type=str, default=None)
    parser.add_argument('--data_path', type=str,
                        default="../Carotid-Data/Carotid-Data")
    parser.add_argument('--split_path', type=str,
                        default="dataset/")
    parser.add_argument('--save_path', type=str,
                        default='models')
    parser.add_argument('--n_split', type=int, default=5)
    parser.add_argument('--seed', type=int, default=960630)
    parser.add_argument('--batch_size', type=int, default=4)
    parser.add_argument('--fold', type=int, default=1)

    args = parser.parse_args()
    for i in range(args.n_split):
        train(
            backbone=args.backbone,
            load_pretrain=args.load_pretrain,
            data_path=args.data_path,
            split_path=args.split_path,
            save_path=args.save_path,
            n_split=args.n_split,
            seed=args.seed,
            batch_size=args.batch_size,
            fold=i
        )


