import numpy as np
import csv
from scipy.ndimage import imread
import sys

class NetworkInput(object):
    def __init__(self, path, input_shape, num_labels):
        self.path = path
        self.num_labels = num_labels
        self.batch_start = 0
        self.epochs_completed = 0
        self.input_shape = input_shape

    def next_batch(self, batch_size):
        raise NotImplemented

    def create_label_vector(self, label):
        v = np.zeros(self.num_labels)
        v[label] = 1
        return v

class CSVInput(NetworkInput):
    def __init__(self, path, input_shape, num_labels, delimiter=",", mode="RGB", shuffle=False):
        super(CSVInput, self).__init__(path, input_shape, num_labels)
        self.delimiter = delimiter
        self.mode = mode
        self.shuffle = shuffle
        self.initialize_input()

    def initialize_input(self):
        self.images = np.array([])
        self.labels = np.array([])
        with open(self.path, "rb") as csvfile:
            reader = csv.reader(csvfile, delimiter=self.delimiter)
            for row in reader:
                image, label = row
                self.images = np.append(self.images, image)
                self.labels = np.append(self.labels, label)
        self.sample_size = self.images.shape[0]
        self.shuffled_images = None
        self.shuffled_labels = None

    def read_png(self, file_path):
        image = imread(file_path, mode=self.mode)
        if self.mode == "L":
            #Adding third dimension to fit channel structure
            image = np.reshape(image, image.shape+(1,))
        assert(len(image.shape) >= 3)
        return image

    def get_shuffled_samples(self):
        perm = np.arange(self.sample_size)
        np.random.shuffle(perm)
        return self.images[perm], self.labels[perm]

    def _read(self, start, batch_size, image_paths, labels):
        images_read = np.array([self.read_png(path) for path in image_paths[start:start+batch_size]])
        labels_read = np.array([self.create_label_vector(label) for label in labels[start:start+batch_size]])
        assert(list(images_read.shape[1:]) == self.input_shape)
        assert(labels_read.size == batch_size * self.num_labels)
        return images_read, labels_read

    def _read_ordered(self, start, batch_size):
        return self._read(start, batch_size, self.images, self.labels)
        
    def _read_random(self, start, batch_size):
        if start == 0 or not self.shuffled_images or not self.shuffled_labels:
            self.shuffled_images, self.shuffled_labels = self.get_shuffled_samples()

        return self._read(start, batch_size, self.shuffled_images, self.shuffled_labels)

    def _read_images_and_labels(self, batch_start, batch_size):
        if self.shuffle:
            return self._read_random(self.batch_start, batch_size)
        else:
            return self._read_ordered(self.batch_start, batch_size)

    def next_batch(self, batch_size):
        def loop(batch_size, accumulated_images = None, accumulated_labels = None):
            if self.batch_start + batch_size >= self.sample_size:
                remaining_batch_size = self.sample_size - self.batch_start
                next_epoch_batch_size = batch_size - remaining_batch_size
                images, labels = self._read_images_and_labels(self.batch_start, remaining_batch_size)

                self.epochs_completed += 1
                self.batch_start = 0
                if accumulated_images:
                    return loop(next_epoch_batch_size, 
                            np.append(accumulated_images, images, axis=0), 
                            np.append(accumulated_labels, labels, axis=0))
                else:
                    return loop(next_epoch_batch_size, images, labels)

            else:
                images, labels = self._read_images_and_labels(self.batch_start, batch_size)
                self.batch_start += batch_size
                if accumulated_images:
                    return np.append(accumulated_images, images, axis=0), np.append(accumulated_labels, labels, axis=0)
                else:
                    return images, labels

        images, labels = loop(batch_size)
        images = images.astype(np.float32)
        images = np.multiply(images, 1.0 / 255.0)
        return images, labels

