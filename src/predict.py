import argparse
import logging
import os
from mypredictor import Predictor
from metric import Metric
import csv
import json
import pickle
from preprocess import Embedding, CSDataset
import torch
from sklearn.metrics import confusion_matrix
import seaborn as sn

def main(args, config_path, model_path):

    logging.info('Loading configuration file from {}'.format(config_path))
    with open(config_path) as f:
        config = json.load(f)

    embedding_pkl_path = os.path.join(args.model_dir, config["embedding_pkl_path"])
    val_pkl_path = os.path.join(args.model_dir, config["val_pkl_path"])
    labelEncoder_path = os.path.join(args.model_dir, config["labelEncoder_path"])
    with open(embedding_pkl_path, "rb") as f:
        config["model_parameters"]["embedding"] = pickle.load(f).vectors
        logging.info( "Load embedding from {}".format(embedding_pkl_path))
    with open(val_pkl_path, "rb") as f:
        config["model_parameters"]["valid"] = pickle.load(f)
        logging.info( "Load val from {}".format(val_pkl_path))
    with open(labelEncoder_path, "rb") as f:
        config["model_parameters"]["labelEncoder"] = pickle.load(f)
        logging.info( "Load labelEncoder from {}".format(labelEncoder_path))


    
    predictor = Predictor(metric=Metric(), **config["model_parameters"])
    predictor.load(model_path)
    

    logging.info("Loading testing data.")
    #with open(args.test_data_path, "rb") as f:
    #    pass
    valid = config["model_parameters"]["valid"] # CSDataset
    test = valid


    logging.info("Predicting...")
    predicts, solution = predictor.predict_dataset(test, test.collate_fn)
    
    output_path = os.path.join(args.model_dir, "predict-{}.csv".format(args.epoch))
    analysis(predicts, solution)

    write_predict_csv(predicts, test, output_path)

def write_predict_csv(predicts, test, output_path):
    #print(predicts)
    pass

def analysis(output, gt):
    maxindex = torch.argmax(output, dim=1)
    solution = torch.argmax(gt, dim=1)
    print(maxindex)
    print(solution)
    matrix = confusion_matrix(solution, maxindex)
    print(matrix)
    sn.heatmap(matrix, annot=True, annot_kws={"size": 16})

    n = 0
    n_correct = 0
    for i in range(len(gt)):
        n += 1
        if gt[i][maxindex[i]] == 1:
            n_correct += 1
    print("Accuracy: {}".format(n_correct / n))




def _parse_args():
    parser = argparse.ArgumentParser(description="Script to predict.")
    parser.add_argument("model_dir", type=str, help="Directory of the model.")
    parser.add_argument("epoch", type=int, help="Which epoch of the model we want to choose.")
    #parser.add_argument("test_data_path", type=str, help="Path to testing data.")
    args = parser.parse_args()

    return args

if __name__ == "__main__":
    args = _parse_args()
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    model_path = os.path.join(args.model_dir, "model.pkl.{}".format(args.epoch))
    config_path = os.path.join(args.model_dir, "config.json")

    if os.path.isfile(config_path) and os.path.isfile(model_path):
        main(args, config_path, model_path)
    else:
        logging.error("{} or {} NOT exist.".format(config_path, model_path))
        exit(1)
