# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

# Modified by Thomas Werkmeister (thomas@twerkmeister.com)
# The original file can be found at:
# https://github.com/tensorflow/tensorflow/blob/1c57936/tensorflow/models/image/experiment/experiment_train.py

"""Train using a single GPU

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime
import os.path
import time
import sys

import tensorflow.python.platform
from tensorflow.python.platform import gfile

import numpy as np
from six.moves import xrange  # pylint: disable=redefined-builtin
import tensorflow as tf

import deepaudio as experiment



FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_string('train_dir', '/home/pva1/DeepAudio/experiments/melfilter_youtube_en_de_levels',
                           """Directory where to write event logs """
                           """and checkpoint.""")
tf.app.flags.DEFINE_integer('max_steps', 30000,
                            """Number of batches to run.""")
tf.app.flags.DEFINE_boolean('log_device_placement', False,
                            """Whether to log device placement.""")


def train():
  """Train network for a number of steps."""
  with tf.Graph().as_default():
    global_step = tf.Variable(0, trainable=False)

    # Get images and labels for CIFAR-10.
    images, labels, keys = experiment.distorted_inputs()

    # Build a Graph that computes the logits predictions from the
    # inference model.
    logits = experiment.inference(images)

    # squashed_logits = tf.reduce_mean(logits, 1)

    # good_indices = tf.reduce_max(tf.where(tf.logical_not(tf.is_nan(squashed_logits))), 1)
    # bad_indices = tf.reduce_max(tf.where(tf.is_nan(squashed_logits)), 1)

    # bad_keys = tf.gather(keys, bad_indices)
    # print_bad_keys = tf.Print(bad_keys, [bad_keys], "Bad Pics: ", summarize = 32)

    # logits = tf.gather(logits, good_indices)
    # labels = tf.gather(labels, good_indices)
    # keys = tf.gather(keys, good_indices)

    #pred = tf.nn.softmax(logits)

    dense_labels = experiment.labels_to_dense(labels)

    # Calculate accuracy
    accuracy, english_accuracy, german_accuracy, german_predictions_count, sum_english_samples, sum_german_samples = experiment.accuracy(logits, dense_labels)

    # Calculate loss.
    loss, cross_entropy = experiment.loss(logits, dense_labels)
    print_cross_entropy = tf.Print(cross_entropy, [cross_entropy], "Cross-entropy: ", summarize=33)
    print_logits = tf.Print(logits, [logits], "Logits: ", summarize=4*32)
    print_keys = tf.Print(keys, [keys], "Keys:", summarize=32)
    # Build a Graph that trains the model with one batch of examples and
    # updates the model parameters.
    train_op = experiment.train(loss, global_step)

    # Create a saver.
    saver = tf.train.Saver(tf.all_variables())

    # Build the summary operation based on the TF collection of Summaries.
    summary_op = tf.merge_all_summaries()

    # Build an initialization operation to run below.
    init = tf.initialize_all_variables()

    # Start running operations on the Graph.
    sess = tf.Session(config=tf.ConfigProto(
        log_device_placement=FLAGS.log_device_placement))
    sess.run(init)

    # Start the queue runners.
    tf.train.start_queue_runners(sess=sess)

    summary_writer = tf.train.SummaryWriter(FLAGS.train_dir,
                                            graph_def=sess.graph_def)
    for step in xrange(FLAGS.max_steps):

      # if step > 0:
      #   with sess.as_default():
      #     for layer in ["conv1", "conv2", "conv3", "local4", "local5", "softmax_linear"]:
      #       with tf.variable_scope(layer, reuse=True):
      #         weights = tf.get_variable('weights')
      #         biases = tf.get_variable('biases')

      #         print('%s: step %d, %s: max weight: %g, max bias: %g' % (datetime.now(),
      #                                                                  step,
      #                                                                  layer,
      #                                                                  tf.reduce_max(tf.abs(weights)).eval(),
      #                                                                  tf.reduce_max(tf.abs(biases)).eval()))

      start_time = time.time()
      #_, pred_value, loss_value, accuracy_value, english_accuracy_value, german_accuracy_value, german_predictions_count_value, sum_english, sum_german, dense_labels_value = sess.run([train_op, pred, loss, accuracy, english_accuracy, german_accuracy, german_predictions_count, sum_english_samples, sum_german_samples, dense_labels])
      # try:
      _, loss_value, accuracy_value, dense_labels_value = sess.run([train_op, loss, accuracy, dense_labels])
      # except tensorflow.python.framework.errors.InvalidArgumentError as e:
      #   problematic_pic = tf.gather(keys, tf.where(tf.is_nan(cross_entropy)))
      #   debug_output = tf.Print(problematic_pic, [problematic_pic], "ERROR, problematic pic: ", summarize = 32)
      #   _ = sess.run([print_cross_entropy, debug_output])
      #   print("skipping to the next step")
      #   continue
      #_, pred_value, loss_value, accuracy_value, dense_labels_value = sess.run([train_op, pred, loss, accuracy, dense_labels])
      duration = time.time() - start_time

      assert not np.isnan(loss_value), 'Model diverged with loss = NaN'

      if step % 10 == 0:
        num_examples_per_step = FLAGS.batch_size
        examples_per_sec = num_examples_per_step / duration
        sec_per_batch = float(duration)

        #format_str = ('%s: step %d, loss = %.2f, accuracy = %.2f, english_accuracy = %.2f, seen_english = %d, german_accuracy = %.2f, seen_german = %d, german_predictions_count = %d '
        #              '(%.1f examples/sec; %.3f sec/batch)')
        #print (format_str % (datetime.now(), step, loss_value, accuracy_value, english_accuracy_value, sum_english, german_accuracy_value, sum_german, german_predictions_count_value,
        #                 examples_per_sec, sec_per_batch))
        format_str = ('%s: step %d, loss = %.2f, accuracy = %.2f '
                     '(%.1f examples/sec; %.3f sec/batch)')
        print (format_str % (datetime.now(), step, loss_value, accuracy_value,
                             examples_per_sec, sec_per_batch))
        #print (pred_value)
        #print (dense_labels_value)


      if step % 100 == 0:
        summary_str = sess.run(summary_op)
        summary_writer.add_summary(summary_str, step)

      # Save the model checkpoint periodically.
      if step % 1000 == 0 or (step + 1) == FLAGS.max_steps:
        checkpoint_path = os.path.join(FLAGS.train_dir, 'model.ckpt')
        saver.save(sess, checkpoint_path, global_step=step)


def main(argv=None):  # pylint: disable=unused-argument
  if gfile.Exists(FLAGS.train_dir):
    gfile.DeleteRecursively(FLAGS.train_dir)
  gfile.MakeDirs(FLAGS.train_dir)
  train()


if __name__ == '__main__':
  tf.app.run()
