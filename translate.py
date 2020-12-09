# -*- coding: utf-8 -*-
"""translate.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1QiaRykKXw2U0pA-8Q4ZT1WnPXl_z_V6h
"""

import tensorflow as tf
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from sklearn.model_selection import train_test_split

import unicodedata
import re
import numpy as np
import os
import io
import time
import re

import pandas as pd
ds = pd.read_csv('/content/drive/MyDrive/Translation/eng_-french.csv')

ds.head()

ds['English words/sentences'] = ds['English words/sentences'].apply(lambda x: x.lower())

ds['French words/sentences']  =ds['French words/sentences'].apply(lambda x: x.lower())

ds['English words/sentences'] = ds['English words/sentences'].apply(lambda x: re.sub("'", '', x))
ds['French words/sentences'] = ds['French words/sentences'].apply(lambda x: re.sub("'", '', x))

import string
special_characters= set(string.punctuation)

ds['English words/sentences'] = ds['English words/sentences'].apply(lambda x: ''.join(char1 for char1 in x if char1 not in special_characters))
ds['French words/sentences'] = ds['French words/sentences'].apply(lambda x: ''.join(char1 for char1 in x if char1 not in special_characters))

num_digits= str.maketrans('','', string.digits)

ds['English words/sentences'] = ds['English words/sentences'].apply(lambda x: x.translate(num_digits))
ds['French words/sentences'] = ds['French words/sentences'].apply(lambda x: x.translate(num_digits))

ds['English words/sentences'] = ds['English words/sentences'].apply(lambda x: x.strip())
ds['French words/sentences'] = ds['French words/sentences'].apply(lambda x: x.strip())

ds['English words/sentences'] = ds['English words/sentences'].apply(lambda x: re.sub(" +", " ", x))
ds['French words/sentences'] = ds['French words/sentences'].apply(lambda x: re.sub(" +", " ", x))

ds['French words/sentences'] = ds['French words/sentences'].apply(lambda x: 'START_ '+ x + ' _END')

ds.head(20)

all_source_words=set()
for source in ds['English words/sentences']:
    for word in source.split():
        if word not in all_source_words:
            all_source_words.add(word)

all_target_words=set()
for target in ds['French words/sentences']:
    for word in target.split():
        if word not in all_target_words:
            all_target_words.add(word)

source_words= sorted(list(all_source_words))
target_words=sorted(list(all_target_words))

source_length_list=list()
for l in ds['English words/sentences']:
    source_length_list.append(len(l.split(' ')))
max_source_length= max(source_length_list)
print(" Max length of the source sentence",max_source_length)

target_length_list=[]
for l in ds['French words/sentences']:
    target_length_list.append(len(l.split(' ')))
max_target_length= max(target_length_list)
print(" Max length of the target sentence",max_target_length)

source_word2idx= dict([(word, i) for i,word in enumerate(source_words)])
target_word2idx=dict([(word, i) for i, word in enumerate(target_words)])

source_idx2word= dict([(i, word) for word, i in  source_word2idx.items()])
print(source_idx2word)
target_idx2word =dict([(i, word) for word, i in target_word2idx.items()])

x_train, x_test, y_train, y_test = train_test_split(ds['English words/sentences'], ds['French words/sentences'], test_size=0.1)

len(x_train)

num_encoder_tokens=len(source_words)

num_decoder_tokens=len(target_words)

def generate_batch(X = x_train, y = y_train, batch_size = 2):
    ''' Generate a batch of data '''
    while True:
        for j in range(0, len(X), batch_size):
            encoder_input_data = np.zeros((batch_size, max_source_length),dtype='float32')
            decoder_input_data = np.zeros((batch_size, max_target_length),dtype='float32')
            decoder_target_data = np.zeros((batch_size, max_target_length, num_decoder_tokens),dtype='float32')
            for i, (input_text, target_text) in enumerate(zip(X[j:j+batch_size], y[j:j+batch_size])):
                for t, word in enumerate(input_text.split()):
                  encoder_input_data[i, t] = source_word2idx[word] 
                for t, word in enumerate(target_text.split()):
                  if t<len(target_text.split())-1:
                      decoder_input_data[i, t] = target_word2idx[word] # decoder input seq
                  if t>0:
                        # decoder target sequence (one hot encoded)
                        # does not include the START_ token
                        # Offset by one timestep
                        #print(word)
                      decoder_target_data[i, t - 1, target_word2idx[word]] = 1.
                    
            yield([encoder_input_data, decoder_input_data], decoder_target_data)

print(next(generate_batch()))

train_samples = len(x_train)
val_samples = len(x_test)
batch_size = 128
epochs = 50
latent_dim=256

from tensorflow import keras

encoder_inputs = keras.Input(shape=(None,))
enc_emb =  keras.layers.Embedding(num_encoder_tokens, latent_dim, mask_zero = True)(encoder_inputs)
encoder_lstm = keras.layers.LSTM(latent_dim, return_state=True)
encoder_outputs, state_h, state_c = encoder_lstm(enc_emb)# We discard `encoder_outputs` and only keep the states.
encoder_states = [state_h, state_c]

decoder_inputs = keras.Input(shape=(None,))
dec_emb_layer = keras.layers.Embedding(num_decoder_tokens, latent_dim, mask_zero = True)
dec_emb = dec_emb_layer(decoder_inputs)# We set up our decoder to return full output sequences,
# and to return internal states as well. We don't use the
# return states in the training model, but we will use them in inference.
decoder_lstm = keras.layers.LSTM(latent_dim, return_sequences=True, return_state=True)
decoder_outputs, _, _ = decoder_lstm(dec_emb,
                                     initial_state=encoder_states)
decoder_dense = keras.layers.Dense(num_decoder_tokens, activation='softmax')
decoder_outputs = decoder_dense(decoder_outputs)

model = keras.models.Model([encoder_inputs, decoder_inputs], decoder_outputs)

model.compile(optimizer='rmsprop', loss='categorical_crossentropy', metrics=['acc'])

model.summary()

train_samples = len(x_train) # Total Training samples
val_samples = len(x_test)    # Total validation or test samples
batch_size = 4
epochs = 15

model.fit_generator(generator = generate_batch(x_train, y_train, batch_size = batch_size),steps_per_epoch = train_samples//batch_size,epochs=epochs,validation_data = generate_batch(x_test, y_test, batch_size = batch_size),validation_steps = val_samples//batch_size)

model.save_weights(‘nmt_weights_100epochs.h5’)

