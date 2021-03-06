import tensorflow as tf

import prepare_data

import random

#Hyper params
learning_rate = 0.001
batch_size = 10
display_step = 100

#Graph params
n_input = 3600 # 128*128 Images
n_classes = 13 # Output Classes (0-9 & A-Z)
dropout = 0.75 # Keep Probability

#Graph input
x = tf.placeholder(tf.float32, [None, n_input])
y = tf.placeholder(tf.float32, [None, n_classes])
keep_prob = tf.placeholder(tf.float32) #dropout (keep probability)


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

def conv_layer(input, input_size, output_size):
	conv_weight = weight_variable([5, 5, input_size, output_size])
	conv_bias = bias_variable([output_size])

	h_conv = conv2d(input, conv_weight, conv_bias)
	return h_conv

#Create model
def conv_net(x, dropout):
	#Reshape input image
	x_image = tf.reshape(x, shape=[-1, 60, 60, 1])

	#2 convolutional layers, 1 pooling layer
	h_conv1 = conv_layer(x_image, 1, 32)
	h_conv2 = conv_layer(h_conv1, 32, 64)

	h_pool1 = max_pool2d(h_conv2)

	#2 convolutional layers, 1 pooling layer
	h_conv3 = conv_layer(h_pool1, 64, 64)
	h_conv4 = conv_layer(h_conv3, 64, 64)

	h_pool2 = max_pool2d(h_conv4)

	# Fully connected layer
	fc1_weight = weight_variable([15*15*64, 2048])
	fc1_bias   = weight_variable([2048])

	# Reshape pooling output to fit fully connected layer input
	h_pool3_flat = tf.reshape(h_pool2, [-1, fc1_weight.get_shape().as_list()[0]])
	h_fc1 = tf.nn.relu(tf.add(tf.matmul(h_pool3_flat, fc1_weight), fc1_bias))
	# Apply Dropout
	h_fc1_drop = tf.nn.dropout(h_fc1, dropout)

	fc2_weight = weight_variable([2048, n_classes])
	fc2_bias   = weight_variable([n_classes])

	# Output, class prediction
	out = tf.add(tf.matmul(h_fc1_drop, fc2_weight), fc2_bias)
	return out

# Construct model
pred = conv_net(x, keep_prob)

# Define loss and optimizer
cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(pred, y))
optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)

# Evaluate model
correct_pred = tf.equal(tf.argmax(pred, 1), tf.argmax(y, 1))
accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

# Initializing the variables
init = tf.initialize_all_variables()

#For saving trained Neural Net for later
saver = tf.train.Saver(tf.trainable_variables(),  write_version=tf.train.SaverDef.V1)

# Launch the graph
with tf.Session() as sess:
	with tf.device('/cpu:0'):
		sess.run(init)
		# Keep training until reach max iterations
		images, labels = prepare_data.prep_data()
		step = 0
		while step * batch_size < len(images):
			batch_x = images[step*batch_size:(step+1)*batch_size] #Take one image from every character
			batch_y = labels[step*batch_size:(step+1)*batch_size]
			# Run optimization op (backprop)
			sess.run(optimizer, feed_dict={x: batch_x, y: batch_y, keep_prob: dropout})
			if step % display_step == 0:
				# Calculate batch loss and accuracy
				loss, acc = sess.run([cost, accuracy], feed_dict={x: batch_x, y: batch_y, keep_prob: 1.})
				# Save the variables to disk.
				save_path = saver.save(sess, "model.ckpt")

				print("Checkpoint saved in file: %s" % save_path)
				print("Iter " + str(step*batch_size) + ", Minibatch Loss= " + \
					  "{:.6f}".format(loss) + ", Training Accuracy= " + \
					  "{:.5f}".format(acc))
			step += 1
		print("Optimization Finished!")


		# Calculate accuracy for 2 random batches
		random.seed()
		step = random.randint(0, 508)
		
		print("Testing Accuracy:", \
			sess.run(accuracy, feed_dict={x: images[step::508],
										  y: labels[step::508],
										  keep_prob: 1.}))
