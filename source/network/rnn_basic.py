import numpy as np

import tensorflow as tf

rnn = tf.contrib.rnn

num_rnn_layer = 2
rnn_size = [256, 256]

def net(x, feed_dict_seq, seq_length,
        batch_size, vocab_size, embd, starter, mode="train"):

  with tf.variable_scope(name_or_scope='RNN',
                         values=[x],
                         reuse=tf.AUTO_REUSE):

    if mode == "train" or mode == "eval":
      inputs = x
      c0 = tf.zeros([batch_size, rnn_size[0]], tf.float32)
      h0 = tf.zeros([batch_size, rnn_size[0]], tf.float32)
      c1 = tf.zeros([batch_size, rnn_size[1]], tf.float32)
      h1 = tf.zeros([batch_size, rnn_size[1]], tf.float32)
    elif mode == "export":
      inputs = x
      c0 = tf.placeholder(
        tf.float32,
        shape=(batch_size, rnn_size[0]), name="c0")
      h0 = tf.placeholder(
        tf.float32,
        shape=(batch_size, rnn_size[0]), name="h0")
      c1 = tf.placeholder(
        tf.float32,
        shape=(batch_size, rnn_size[1]), name="c1")
      h1 = tf.placeholder(
        tf.float32,
        shape=(batch_size, rnn_size[1]), name="h1")        
    else:
      # Use placeholder in inference mode for both input and states
      # This allows taking the previous batch (step)'s output
      # as the input for the next batch.
      inputs = tf.placeholder(
        tf.int32,
        shape=(batch_size, seq_length),
        name="inputs")
      initial_value = np.array(starter, dtype=np.int32)
      feed_dict_seq[inputs] = initial_value

      c0 = tf.placeholder(
        tf.float32,
        shape=(batch_size, rnn_size[0]), name="c0")
      h0 = tf.placeholder(
        tf.float32,
        shape=(batch_size, rnn_size[0]), name="h0")
      c1 = tf.placeholder(
        tf.float32,
        shape=(batch_size, rnn_size[1]), name="c1")
      h1 = tf.placeholder(
        tf.float32,
        shape=(batch_size, rnn_size[1]), name="h1")

      feed_dict_seq[c0] = np.zeros(
        (batch_size, rnn_size[0]), dtype=float)
      feed_dict_seq[h0] = np.zeros(
        (batch_size, rnn_size[0]), dtype=float)
      feed_dict_seq[c1] = np.zeros(
        (batch_size, rnn_size[1]), dtype=float)
      feed_dict_seq[h1] = np.zeros(
        (batch_size, rnn_size[1]), dtype=float)

    initial_state = (rnn.LSTMStateTuple(c0, h0),
                     rnn.LSTMStateTuple(c1, h1))

    cell = rnn.MultiRNNCell([rnn.LSTMBlockCell(num_units=rnn_size[i])
                            for i in range(num_rnn_layer)])

    if len(embd) > 0:
      embeddingW = tf.get_variable(
        'embedding',
        initializer=tf.constant(embd),
        trainable=True)      
    else:
      embeddingW = tf.get_variable('embedding', [vocab_size, rnn_size[0]])

    input_feature = tf.nn.embedding_lookup(embeddingW, inputs)

    input_list = tf.unstack(input_feature, axis=1)

    outputs, last_state = tf.nn.static_rnn(
      cell, input_list, initial_state)

    output = tf.reshape(tf.concat(outputs, 1), [-1, rnn_size[1]])

    logits = tf.layers.dense(
      inputs=tf.layers.flatten(output),
      units=vocab_size,
      activation=tf.identity,
      use_bias=True,
      kernel_initializer=tf.contrib.layers.variance_scaling_initializer(2.0),
      bias_initializer=tf.zeros_initializer())

    return logits, last_state, inputs