import sys
import os
import torch
import yaml

# Path setup
styletts2_path = "/app/libs/StyleTTS2-Vocos"
sys.path.insert(0, styletts2_path)

from models import build_model
from Utils.PLBERT.util import load_checkpoint

config_path = "/app/models/styletts2/Vocos/AIHUB_ML/config_aihub_multi_lingual_en_jp_ko_zh_vocos.yml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

print("Building model...")
model, sampler = build_model(config)

checkpoint_path = "/app/models/styletts2/Vocos/AIHUB_ML/epoch_2nd_00006.pth"
print(f"Loading checkpoint from {checkpoint_path}...")
checkpoint = torch.load(checkpoint_path, map_location='cpu')
model.load_state_dict(checkpoint['model'])
print("Model loaded successfully!")

try:
    from meldataset import TextCleaner
    cleaner = TextCleaner()
    print("TextCleaner loaded from meldataset!")
except Exception as e:
    print(f"Failed to load TextCleaner: {e}")
