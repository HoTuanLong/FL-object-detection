import os
import json
import xml.etree.ElementTree as ET
from typing import Dict, List
from tqdm import tqdm

sets = ['train', 'val']
# classes = ["basket", "carton", "chair", "electrombile", "gastank", "sunshade", "table"]
classes = ['vehicles', 'household', 'animals', 'aeroplane', 'bicycle', 'boat', 'bus', 'car', 'motorbike', 'train',
           'bottle', 'chair',
           'dining', 'table', 'potted', 'plant', 'sofa', 'TV/monitor', 'bird', 'cat', 'cow', 'dog', 'horse', 'sheep',
           'person']
dataset = "voc_2"
model = "yolo"
num_client = int(dataset.split('_')[-1])


def convert(size, box):
    dw = 1. / (size[0])
    dh = 1. / (size[1])
    x = (box[0] + box[1]) / 2.0 - 1
    y = (box[2] + box[3]) / 2.0 - 1
    w = box[1] - box[0]
    h = box[3] - box[2]
    x = x * dw
    w = w * dw
    y = y * dh
    h = h * dh
    return x, y, w, h


def convert_annotation(anno_path, label_path, image_set, image_id):
    with open(os.path.join("custom", image_set + "_label.json"), 'r') as f:
        in_file = json.load(f)

    out_file = open(os.path.join(label_path, image_id + ".txt"), 'w')
    print(out_file)

    w = 704
    h = 576

    for data in in_file:
        if data['image_id'] == image_id:
            for obj in data['items']:
                cls = obj['class']
                if cls not in classes:
                    continue
                cls_id = classes.index(cls)
                b = (float(obj['bbox'][0]), float(obj['bbox'][2]), float(obj['bbox'][1]), float(obj['bbox'][3]))
                bb = convert((w, h), b)
                out_file.write(str(cls_id) + " " + " ".join([str(a) for a in bb]) + '\n')
    out_file.close()

    # for obj in root.iter('object'):
    #     difficult = obj.find('difficult').text
    #     cls = obj.find('name').text
    #     if cls not in classes or int(difficult) == 1:
    #         continue
    #     cls_id = classes.index(cls)
    #     xmlbox = obj.find('bndbox')
    #     b = (float(xmlbox.find('xmin').text), float(xmlbox.find('xmax').text), float(xmlbox.find('ymin').text),
    #          float(xmlbox.find('ymax').text))
    #     bb = convert((w, h), b)
    #     out_file.write(str(cls_id) + " " + " ".join([str(a) for a in bb]) + '\n')


if model == "faster":
    server_task_file = os.path.join("task_configs", model, dataset, "faster_task.json")
    os.makedirs(os.path.dirname(server_task_file))
    server_task_config = dict()
    server_task_config["model_name"] = "FasterRCNN"
    server_task_config["model_config"] = os.path.join("data", "task_configs", model, dataset,
                                                      "faster_model.json")
    server_task_config["log_dir"] = "{}/{}".format(model, dataset)
    server_task_config["data_path"] = "data/Street_voc/total"
    server_task_config["model_path"] = "faster_model.pkl"
    server_task_config["MIN_NUM_WORKERS"] = num_client
    server_task_config["MAX_NUM_ROUNDS"] = 1000
    server_task_config["NUM_TOLERATE"] = -1
    server_task_config["NUM_CLIENTS_CONTACTED_PER_ROUND"] = num_client
    server_task_config["ROUNDS_BETWEEN_VALIDATIONS"] = 1000
    with open(server_task_file, "w") as f:
        json.dump(server_task_config, f, indent=4)

    model_config_file = os.path.join("task_configs", model, dataset, model + "_model.json")
    model_config = dict()
    model_config["model_name"] = "fasterrcnn-faccee"
    model_config["env"] = "FasterRCNN"
    model_config["plot_every"] = 100
    model_config["batch_size"] = 1
    model_config["label_names"] = classes
    with open(model_config_file, 'w') as f:
        json.dump(model_config, f, indent=4)

    for i in range(1, int(dataset.split('_')[-1]) + 1):
        dir_path = os.path.join(str(i), "ImageSets", "Main", "train.txt")
        task_file_path = os.path.join("task_configs", model, dataset, "faster_task" + str(i) + ".json")
        task_config = dict()
        task_config["model_name"] = "FasterRCNN"
        task_config["model_config"] = os.path.join("data", "task_configs", model, dataset,
                                                   "faster_model.json")
        task_config["log_filename"] = "{}/{}/FL_client_{}_log".format(model, dataset, str(i))
        task_config["data_path"] = "data/{}/{}".format(dataset, str(i))
        task_config["local_epoch"] = 5

        with open(task_file_path, "w") as f:
            json.dump(task_config, f, indent=4)


elif model == "yolo":
    server_task_file = os.path.join("task_configs", model, dataset, model + "_task.json")
    os.makedirs(os.path.dirname(server_task_file))
    server_task_config = dict()
    server_task_config["model_name"] = "Yolo"
    server_task_config["model_config"] = os.path.join("data", "task_configs", model, dataset, "yolo_model.json")
    server_task_config["log_dir"] = "{}/{}".format(model, dataset)
    server_task_config["model_path"] = "yolo_model.pkl"
    server_task_config["MIN_NUM_WORKERS"] = num_client
    server_task_config["MAX_NUM_ROUNDS"] = 1000
    server_task_config["NUM_TOLERATE"] = -1
    server_task_config["NUM_CLIENTS_CONTACTED_PER_ROUND"] = num_client
    server_task_config["ROUNDS_BETWEEN_VALIDATIONS"] = 1000
    with open(server_task_file, "w") as f:
        json.dump(server_task_config, f, indent=4)

    model_config_file = os.path.join("task_configs", model, dataset, model + "_model.json")
    model_config = dict()
    model_config["model_def"] = "config/yolov3-custom-{}.cfg".format(dataset.split('_')[0])
    model_config["pretrained_weights"] = "weights/darknet53.conv.74"
    model_config["multiscale_training"] = True
    model_config["gradient_accumulations"] = 2
    model_config["img_size"] = 416
    with open(model_config_file, 'w') as f:
        json.dump(model_config, f, indent=4)
    for i in range(1, int(dataset.split('_')[-1]) + 1):
        label_path = os.path.join(dataset, str(i), "labels")
        if not os.path.exists(label_path):
            os.makedirs(label_path)
        for image_set in sets:
            anno_path = os.path.join(dataset, str(i), "Annotations")
            image_path = os.path.join(dataset, str(i), "ImageSets", "Main", image_set + ".txt")
            image_ids = open(image_path).read().strip().split()
            list_file = open('%s/%s/%s.txt' % (dataset, str(i), image_set), 'w')
            for image_id in image_ids:
                list_file.write('%s/%s/%s/%s.jpg\n' % ("data", "custom", "images", image_id))
                # convert_annotation(anno_path, label_path, image_set, image_id)
            list_file.close()
        task_file_path = os.path.join("task_configs", model, dataset, "yolo_task" + str(i) + ".json")
        task_config = dict()
        task_config["model_name"] = "Yolo"
        task_config["model_config"] = "data/task_configs/{}/{}/yolo_model.json".format(model, dataset)
        task_config["log_filename"] = "{}/{}/FL_client_{}_log".format(model, dataset, str(i))
        task_config["train"] = "data/{}/{}/train.txt".format(dataset, str(i))
        task_config["test"] = "data/{}/{}/test.txt".format(dataset, str(i))
        task_config["names"] = "data/{}/classes.names".format(dataset)
        task_config["n_cpu"] = 4
        task_config["local_epoch"] = 5
        task_config["batch_size"] = 1
        with open(task_file_path, "w") as f:
            json.dump(task_config, f, indent=4)
