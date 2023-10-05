import os
import shutil
import argparse

parser = argparse.ArgumentParser(description="Run clean")
parser.add_argument("--input_images", help="path to input images folder", default="data/yangpyeong")
args = parser.parse_args()

data_path = args.input_images

# Reset dataset
os.system(f"chmod 777 {data_path}")
datas = os.listdir(data_path)
for data in datas:
    path = os.path.join(data_path, data)
    if not (data in ['images', 'queue', 'config.yaml']):
        if os.path.isfile(path):
            os.remove(path)
        else:
            shutil.rmtree(path)