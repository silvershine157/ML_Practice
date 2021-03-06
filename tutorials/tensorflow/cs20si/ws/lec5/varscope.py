import tensorflow as tf

def two_hidden_layers(x):
    assert x.shape.as_list() == [200, 100]
    w1 = tf.Variable(tf.random_normal([100, 50]), name="h1_weights")
    b1 = tf.Variable(tf.zeros([50]), name="h1_biases")
    h1 = tf.matmul(x, w1) + b1
    assert h1.shape.as_list() == [200, 50]
    w2 = tf.Variable(tf.random_normal([50, 10]), name="h2_weights")
    b2 = tf.Variable(tf.zeros([10]), name="h2_biases")
    logits = tf.matmul(h1, w2) + b2
    return logits

def test1():
    x1 = tf.truncated_normal([200, 100], name='x1')
    x2 = tf.truncated_normal([200, 100], name='x2')
    
    logits1 = two_hidden_layers(x1)
    logits2 = two_hidden_layers(x2)
    # no variable sharing because we used 'tf.Variable()'

    with tf.Session() as sess:
        writer = tf.summary.FileWriter('graphs/varscope', sess.graph)
        writer.close()

def two_hidden_layers_2(x):
    assert x.shape.as_list() == [200, 100]
    w1 = tf.get_variable("h1_weights", [100, 50], initializer=tf.random_normal_initializer())
    b1 = tf.get_variable("h1_biases", [50], initializer=tf.constant_initializer(0.0))
    h1 = tf.matmul(x, w1) + b1
    assert h1.shape.as_list() == [200, 50]
    w2 = tf.get_variable("h2_weights", [50, 10], initializer=tf.random_normal_initializer())
    b2 = tf.get_variable("h2_biases", [10], initializer=tf.constant_initializer(0.0))
    logits = tf.matmul(h1, w2) + b2
    return logits


def test2():
    x1 = tf.truncated_normal([200, 100], name='x1')
    x2 = tf.truncated_normal([200, 100], name='x2')
    
    with tf.variable_scope("two_layers") as scope:
        logits1 = two_hidden_layers_2(x1)
        scope.reuse_variables()
        logits2 = two_hidden_layers_2(x2)

    with tf.Session() as sess:
        writer = tf.summary.FileWriter('graphs/varscope', sess.graph)
        writer.close()

def fc_layer(x, output_dim, scope_name):
    with tf.variable_scope(scope_name) as scope:
        w = tf.get_variable("weights", [x.shape[1], output_dim],
                initializer=tf.random_normal_initializer())
        b = tf.get_variable("bias", [output_dim],
                initializer=tf.constant_initializer(0.0))
        h = tf.matmul(x, w) + b
        return h

def two_hidden_layers_3(x):
    h1 = fc_layer(x, 50, 'h1')
    h2 = fc_layer(h1, 10, 'h2')
    return h2

def test3():
    x1 = tf.truncated_normal([200, 100], name='x1')
    x2 = tf.truncated_normal([200, 100], name='x2')
     
    with tf.variable_scope("two_layers") as scope:
        logits1 = two_hidden_layers_3(x1)
        scope.reuse_variables()
        logits2 = two_hidden_layers_3(x2)

    with tf.Session() as sess:
        writer = tf.summary.FileWriter('graphs/varscope', sess.graph)
        writer.close()

test3()
