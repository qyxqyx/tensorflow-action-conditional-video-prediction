import tensorflow as tf
import numpy as np
import cv2

import argparse
import sys, os
import logging

from model import ActionConditionalVideoPredictionModel
from dataset import Dataset

def get_config(args):
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    return config

def main(args):
    with tf.Graph().as_default() as graph:
        # Create dataset
        logging.info('Create data flow from %s' % args.train)
        train_data = Dataset(directory=args.train, mean_path=args.mean, batch_size=args.batch_size)
        test_data = Dataset(directory=args.test, mean_path=args.mean, batch_size=args.batch_size)
    
        # Create model
        logging.info('Create model for training [lr = %f, epochs = %d, batch_size = %d]' % (args.lr, args.epoch, args.batch_size) )
        model = ActionConditionalVideoPredictionModel(train_data(), 
                                                    optimizer_args={'lr': args.lr})
        
        # Create initializer
        init = tf.group(tf.global_variables_initializer(), tf.local_variables_initializer())
        
        # Get optimizer operation and loss opearation from model
        train_op = model.train
        loss_op = model.loss
        global_step = model.global_step
       
        # Config session
        config = get_config(args)
        
        # Setup summary
        train_summary_op = tf.summary.merge_all('train')
        test_summary_op = tf.summary.merge_all('test')
        test_summary_writer = tf.summary.FileWriter(os.path.join(args.log, 'test'), graph)

        # Setup supervisor
        sv = tf.train.Supervisor(logdir=os.path.join(args.log, 'train'),
                init_op=init,
                graph=graph,
                summary_op=train_summary_op,
                global_step=global_step)
        
        # Start session
        with sv.managed_session(config=config) as sess:
            sv.start_queue_runners(sess)
            for epoch in range(args.epoch):
                _, train_loss, train_summary = sess.run([train_op, loss_op, train_summary_op])
                sv.summary_computed(sess, train_summary)
                
                if (epoch + 1) % args.show_per_epoch == 0:
                    logging.info('Epoch %d: Training L2 loss = %f' % (epoch, train_loss))
                
                if (epoch + 1) % args.test_per_epoch == 0:
                    test_loss, test_summary = sess.run([loss_op, test_summary_op])
                    logging.info('Epoch %d: Testing L2 loss = %f' % (epoch, test_loss))
                    test_summary_writer.add_summary(test_summary, (epoch + 1) / args.test_per_epoch)
            sv.request_stop()
        
    
if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', help='summary directory', type=str, default='example/log')
    parser.add_argument('--train', help='training data directory', type=str, default='example/train')
    parser.add_argument('--test', help='testing data directory', type=str, default='example/test')
    parser.add_argument('--mean', help='image mean path', type=str, default='example/mean.npy')
    parser.add_argument('--lr', help='learning rate', type=float, default=0.001)
    parser.add_argument('--epoch', help='epoch', type=int, default=1500000)
    parser.add_argument('--show_per_epoch', help='epoch', type=int, default=1000)
    parser.add_argument('--test_per_epoch', help='epoch', type=int, default=2000)
    parser.add_argument('--batch_size', help='batch size', type=int, default=32)
    args = parser.parse_args()

    main(args)



