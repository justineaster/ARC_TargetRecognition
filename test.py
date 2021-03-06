import tensorflow as tf
import cv2

import prepare_data

#Hyper params
batch_size = 36
display_step = 500

#Graph params
n_input = 16384 # 128*128 Images
n_classes = 36 # Output Classes (0-9 & A-Z)

#Graph input
x = tf.placeholder(tf.float32, [None, n_input])
y = tf.placeholder(tf.float32, [None, n_classes])

#Wrappers
def conv2d(x, W, b):
	#Conv2D wrapper, with bias and relu activation
	x = tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')
	x = tf.nn.bias_add(x, b)
	return tf.nn.relu(x)

def max_pool2d(x):
	# MaxPool2D wrapper
	return tf.nn.max_pool(x, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')

def weight_variable(shape):
	initial = tf.truncated_normal(shape, stddev=0.1)
	return tf.Variable(initial)

def bias_variable(shape):
	initial = tf.constant(0.1, shape=shape)
	return tf.Variable(initial)

def network_layer(input, input_size, output_size):
	conv_weight = weight_variable([5, 5, input_size, output_size])
	conv_bias = bias_variable([output_size])

	h_conv = conv2d(input, conv_weight, conv_bias)
	h_pool = max_pool2d(h_conv)

	return conv_weight, conv_bias, h_conv, h_pool

#Create model
def conv_net(x):
	#Reshape input image
	x_image = tf.reshape(x, shape=[-1, 128, 128, 1])

	#4 convolutional layers
	_, _, _, h_pool1 = network_layer(x_image, 1, 32)
	_, _, _, h_pool2 = network_layer(h_pool1, 32, 64)
	_, _, _, h_pool3 = network_layer(h_pool2, 64, 128)
	_, _, _, h_pool4 = network_layer(h_pool3, 128, 256)
	# Fully connected layer
	# Reshape conv2 output to fit fully connected layer input
	fc1_weight = weight_variable([8*8*256, 2048])
	fc1_bias   = weight_variable([2048])

	h_pool3_flat = tf.reshape(h_pool4, [-1, fc1_weight.get_shape().as_list()[0]])
	h_fc1 = tf.nn.relu(tf.add(tf.matmul(h_pool3_flat, fc1_weight), fc1_bias))

	fc2_weight = weight_variable([2048, n_classes])
	fc2_bias   = weight_variable([n_classes])

	# Output, class prediction
	out = tf.add(tf.matmul(h_fc1, fc2_weight), fc2_bias)
	return out

# Construct model
pred = conv_net(x)

# Initializing the variables
init = tf.initialize_all_variables()

#For saving trained Neural Net for later
saver = tf.train.Saver()

# Launch the graph
with tf.Session() as sess:
	with tf.device('/cpu:0'):
		sess.run(init)
		# Restore variables from disk.
		saver.restore(sess, "model.ckpt")
		print("Model restored.")
		# Keep training until reach max iterations
		images, _ = prepare_data.prep_data()
		step = 0
		while step * batch_size < len(images):
			batch_x = images[step::1016] #Take one image from every character
			# Run optimization op (backprop)
			pred_labels = sess.run(pred, feed_dict={x: batch_x})
			for i in range(0, len(batch_x)):
				cv2.imshow("Display", batch_x[i].reshape((128,128)))
				print(pred_labels[i])
				cv2.waitKey()
			step += 1