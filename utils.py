
# Copyright 2022 TranNhiem.

# Code base Inherence from https://github.com/facebookresearch/dino/

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.

import os
import sys
import time
import math
from collections import defaultdict, deque
import numpy as np
import torch.nn as nn
import torch
import torchvision
from functools import partial
from typing import Any, Callable, List, Tuple
# For Dataloader Inference
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
from torchvision import io, transforms
from sklearn.model_selection import train_test_split
from PIL import Image

# For Visual Attention Map
import colorsys
import random
import matplotlib.pyplot as plt
import cv2
from skimage.measure import find_contours
from matplotlib.patches import Polygon
import skimage.io
# ******************************************************
# Helper functions
# ******************************************************


def _no_grad_trunc_normal_(tensor, mean, std, a, b):
    # Cut & paste from PyTorch official master until it's in a few official releases - RW
    # Method based on https://people.sc.fsu.edu/~jburkardt/presentations/truncated_normal.pdf
    def norm_cdf(x):
        # Computes standard normal cumulative distribution function
        return (1. + math.erf(x / math.sqrt(2.))) / 2.

    if (mean < a - 2 * std) or (mean > b + 2 * std):
        warnings.warn("mean is more than 2 std from [a, b] in nn.init.trunc_normal_. "
                      "The distribution of values may be incorrect.",
                      stacklevel=2)

    with torch.no_grad():
        # Values are generated by using a truncated uniform distribution and
        # then using the inverse CDF for the normal distribution.
        # Get upper and lower cdf values
        l = norm_cdf((a - mean) / std)
        u = norm_cdf((b - mean) / std)

        # Uniformly fill tensor with values from [l, u], then translate to
        # [2l-1, 2u-1].
        tensor.uniform_(2 * l - 1, 2 * u - 1)

        # Use inverse cdf transform for normal distribution to get truncated
        # standard normal
        tensor.erfinv_()

        # Transform to proper mean, std
        tensor.mul_(std * math.sqrt(2.))
        tensor.add_(mean)

        # Clamp to ensure it's in the proper range
        tensor.clamp_(min=a, max=b)
        return tensor


def trunc_normal_(tensor, mean=0., std=1., a=-2., b=2.):
    # type: (Tensor, float, float, float, float) -> Tensor
    return _no_grad_trunc_normal_(tensor, mean, std, a, b)

# ******************************************************
# Loading Pre-trained Weights
# ******************************************************


def load_pretrained_weights(model, pretrained_weights, checkpoint_key, model_name, patch_size):
    '''
    model: ViT architecutre design with random itit Weight  
    pretrained_weights: The path of pretrained weights from your local machine 
    checkpoint_key:  If specific layer neeed loading check point ?? 
    model_name: provide name to loading checkpoint from MetaAI hub checkpoint if pretrained_weights is not provided
    patch_size: this argument provide the patch_size of pretrained model need to load

    '''

    if os.path.isfile(pretrained_weights):
        state_dict = torch.load(pretrained_weights, map_location='cpu')
        if checkpoint_key is not None and checkpoint_key in state_dict:
            print(f'take key {checkpoint_key} in provided checkpoint dict')
            state_dict = state_dict[checkpoint_key]
        # remove 'Module' prefix
        state_dict = {k.replace("module.", ""): v for k,
                      v in state_dict.items()}
        # remove 'backbone' prefix induced by multicrop wrapper
        state_dict = {k.replace("backbone.", ""): v for k,
                      v in state_dict.items()}
        msg = model.load_state_dict(state_dict, strict=False)
        print(f"Pretrained weight found at {pretrained_weights, msg}")

    else:
        print("Not using '--pretrained weights path', Loading Default Models")

        url = None

        if model_name == "vit_small" and patch_size == 16:
            url = "dino_deitsmall16_pretrain/dino_deitsmall16_pretrain.pth"
        elif model_name == "vit_small" and patch_size == 8:
            url = "dino_deitsmall8_pretrain/dino_deitsmall8_pretrain.pth"
        elif model_name == "vit_base" and patch_size == 16:
            url = "dino_vitbase16_pretrain/dino_vitbase16_pretrain.pth"
        elif model_name == "vit_base" and patch_size == 8:
            url = "dino_vitbase8_pretrain/dino_vitbase8_pretrain.pth"
        elif model_name == "xcit_small_12_p16":
            url = "dino_xcit_small_12_p16_pretrain/dino_xcit_small_12_p16_pretrain.pth"
        elif model_name == "xcit_small_12_p8":
            url = "dino_xcit_small_12_p8_pretrain/dino_xcit_small_12_p8_pretrain.pth"
        elif model_name == "xcit_medium_24_p16":
            url = "dino_xcit_medium_24_p16_pretrain/dino_xcit_medium_24_p16_pretrain.pth"
        elif model_name == "xcit_medium_24_p8":
            url = "dino_xcit_medium_24_p8_pretrain/dino_xcit_medium_24_p8_pretrain.pth"
        elif model_name == "resnet50":
            url = "dino_resnet50_pretrain/dino_resnet50_pretrain.pth"
        
        elif model_name == 'vit_base_ibot_16' and patch_size == 16:
            state_dict = torch.load('/home/rick/pretrained_weight/DINO_Weight/ViT_B_16_ckpt/checkpoint.pth', map_location='cpu')
            # remove 'Module' prefix
            state_dict = {k.replace("module.", ""): v for k,
                        v in state_dict.items()}
            # remove 'backbone' prefix induced by multicrop wrapper
            state_dict = {k.replace("backbone.", ""): v for k,
                        v in state_dict.items()}
            model.load_state_dict(state_dict, strict=False)
        
        elif model_name == 'vit_L_16_ibot' and patch_size == 16: 
            state_dict = torch.load('/home/rick/pretrained_weight/DINO_Weight/ViT_L_16_ckpt/checkpoint.pth', map_location='cpu')
            # remove 'Module' prefix
            state_dict = {k.replace("module.", ""): v for k,
                        v in state_dict.items()}
            # remove 'backbone' prefix induced by multicrop wrapper
            state_dict = {k.replace("backbone.", ""): v for k,
                        v in state_dict.items()}
            model.load_state_dict(state_dict, strict=False)
        
        if url is not None:
            print(
                "Since no pretrained weights have been provided, we load the reference pretrained DINO weights.")
            state_dict = torch.hub.load_state_dict_from_url(
                url="https://dl.fbaipublicfiles.com/dino/" + url)
            model.load_state_dict(state_dict, strict=True)
        else:
            print(
                "There is no reference weights available for this model => We use random weights.")
        
        return model

def load_pretrained_linear_weights(linear_classifier, model_name, patch_size):
    url = None
    if model_name == "vit_small" and patch_size == 16:
        url = "dino_deitsmall16_pretrain/dino_deitsmall16_linearweights.pth"
    elif model_name == "vit_small" and patch_size == 8:
        url = "dino_deitsmall8_pretrain/dino_deitsmall8_linearweights.pth"
    elif model_name == "vit_base" and patch_size == 16:
        url = "dino_vitbase16_pretrain/dino_vitbase16_linearweights.pth"
    elif model_name == "vit_base" and patch_size == 8:
        url = "dino_vitbase8_pretrain/dino_vitbase8_linearweights.pth"
    elif model_name == "resnet50":
        url = "dino_resnet50_pretrain/dino_resnet50_linearweights.pth"
    if url is not None:
        print("We load the reference pretrained linear weights.")
        state_dict = torch.hub.load_state_dict_from_url(
            url="https://dl.fbaipublicfiles.com/dino/" + url)["state_dict"]
        linear_classifier.load_state_dict(state_dict, strict=True)
    else:
        print("We use random linear weights.")


class patch_head(nn.Module):
    def __init__(self, in_dim, num_heads, k_num):
        super().__init__()
        self.cls_token = nn.Parameter(torch.zeros(1, 1, in_dim))

        # Adding the LayerScale Block CA
        #self.cls_blocks= nn.ModuleList([])
        # self.cls_blocks = nn.ModuleList([
        #     LayerScale_Block_CA(
        #         dim=in_dim, num_heads=num_heads, mlp_ratio=4.0, qkv_bias=True, qk_scale=None,
        #         drop=0.0, attn_drop=0.0, drop_path=0.0, norm_layer=partial(nn.LayerNorm, eps=1e-6),
        #         act_layer=nn.GELU, Attention_block=Class_Attention,
        #         Mlp_block=Mlp)
        #         for i in range(2)])

        trunc_normal_(self.cls_token, std=.02)
        self.norm = partial(nn.LayerNorm, eps=1e-6)(in_dim)
        self.apply(self._init_weights)
        self.k_num = k_num
        self.k_size = 3
        self.loc224 = self.get_local_index(196, self.k_size)
        self.loc96 = self.get_local_index(36, self.k_size)
        self.embed_dim = in_dim

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            trunc_normal_(m.weight, std=.02)
            if isinstance(m, nn.Linear) and m.bias is not None:
                nn.init.constant_(m.bias, 0)

    def forward(self, x, loc=False):
        cls_tokens = self.cls_token.expand(x.shape[0], -1. - 1)

        if loc:
            k_size = self.k_size
            if x.shape[1] == 196:
                local_idx = self.loc224
            elif x.shape[1] == 36:
                if self.k_size == 14:
                    k_size = 6
                local_idx = self.loc96

            else:
                print(x.shape)
                assert (False)

            # X here will be Individual Patch (Batches 3, 16, 16)
            x_norm = nn.functional.normalize(x, dim=-1)
            # Compute Cosine Similarity Matrix
            sim_matrix = x_norm[:,
                                local_idx] @ x_norm.unsqueeze(2).transpose(-2, -1)
            top_idx = sim_matrix.squeeze().topk(
                k=self.k_num, dim=-1)[1].view(-1, self.k_num, 1)

            x_loc = x[:, local_idx].view(-1, k_size**2-1, self.embed_dim)
            x_loc = torch.gather(
                x_loc, 1, top_idx.expand(-1, -1, self.embed_dim))
            for i, blk in enumerate(self.cls_blocks):
                if i == 0:
                    glo_tokens = blk(x, cls_tokens)
                    loc_tokens = blk(
                        x_loc, cls_tokens.repeat(x.shape[1], 1, 1))
                else:
                    glo_tokens = blk(x, glo_tokens)
                    loc_tokens = blk(x_loc, loc_tokens)
            loc_tokens = loc_tokens.view(x.shape)
            x = self.norm(torch.cat([glo_tokens, loc_tokens], dim=1))
        else:
            for i, blk in enumerate(self.cls_blocks):
                cls_tokens = blk(x, cls_tokens)
            x = self.norm(torch.cat([cls_tokens, x], dim=1))

        return x

        @staticmethod
        def get_local_index(N_patches, k_size):
            loc_weight = []
            w = torch.LongTensor(list(range(int(math.sqrt(N_patches)))))
            # Why we need to iterate through all patches
            for i in range(N_patches):
                ix, iy = i // len(w), i % len(w)
                wx = torch.zeros(int(math.sqrt(N_patches)))
                wy = torch.zeros(int(math.sqrt(N_patches)))
                wx[ix] = 1
                wy[iy] = 1
                # Iteration through all N patches of Single Images?
                for j in range(1, int(k_size//2)+1):
                    wx[(ix+j) % len(wx)] = 1
                    wx[(ix-j) % len(wx)] = 1
                    wy[(iy+j) % len(wy)] = 1
                    wy[(iy-j) % len(wy)] = 1

                weight = (wy.unsqueeze(0) * wx.unsqueeze(1)).view(-1)
                weight[i] = 0
                loc_weight.append(weight.nonzero().squeeze())

            return torch.stack(loc_weight)

# ******************************************************
# Inference DataLoader
# ******************************************************


class collateFn_patches:

    def __init__(self, image_size, patch_size, chanels):
        self.patch_size = patch_size
        self.chanels = chanels
        self.num_patches = (image_size//patch_size)**2

    def reshape(self, batch):
        patches = torch.stack(batch) \
            .unfold(2, self.patch_size, self.patch_size)\
            .unfold(3, self.patch_size, self.patch_size)

        num_images = len(patches)
        patches = patches.reshape(
            num_images,
            self.chanels,
            self.num_patches,
            self.patch_size,
            self.patch_size,)

        patches.transpose_(1, 2)
        return patches.reshape(num_images, self.num_patches, -1) / 255.0 - 0.5

    def __call__(self, batch: List[Tuple[torch.Tensor, torch.Tensor]]) -> torch.FloatTensor:
        return self.reshape(batch)


class collatesingle_img:

    def __call__(self, batch: List[torch.Tensor]) -> torch.FloatTensor:
        return batch


class ImageOriginalData(Dataset):
    def __init__(self, files: List[str], img_size: int, transform_ImageNet=False):
        self.files = files
        self.resize = transforms.Resize((img_size, img_size))
        self.transform_ImageNet = transform_ImageNet
        if self.transform_ImageNet:
            print("Using imageNet normalization")
        self.transform_normal = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
        ])
    # Iterative through all images in dataste

    def __len__(self):
        return len(self.files)

    def __getitem__(self, i):
        with open(self.files[i], 'rb') as f:
            img = Image.open(f)
            img = img.convert('RGB')
        #img = io.read_image(self.files[i])
        # Checking the Image Channel
        # if img.shape[0] == 1:
        #     img= torch.cat([img]*3)
        if self.transform_ImageNet:
            return self.transform_normal(img)
        else:
            return self.resize(img)


class normal_dataloader:
    '''
    This normal dataloader loading dataset with *ONLY One Folder* 

    '''

    def __init__(self, image_path, image_format="*.jpg", img_size=224, batch_size=4, subset_data=0.2, transform_ImageNet=False):
        image_files_ = [str(file) for file in Path(image_path).glob("*.jpg")]
        _,  self.image_files = train_test_split(
            image_files_, test_size=subset_data, random_state=42)

        self.img_size = img_size
        self.batch_size = batch_size
        self.transform_ImageNet = transform_ImageNet

    def val_dataloader(self):
        val_data = ImageOriginalData(
            self.image_files, self.img_size, self.transform_ImageNet)
        print(f" total images in Demo Dataset: {len(val_data)}")
        val_dl = DataLoader(
            val_data,
            self.batch_size*2,
            shuffle=False,
            drop_last=False,
            num_workers=4,
            pin_memory=True,
            #collate_fn= collatesingle_img()
        )
        return val_dl

    def val_dataloader_patches(self, patch_size, chanels):
        val_data = ImageOriginalData(
            self.image_files, self.img_size, self.transform_ImageNet)
        print(f" total images in Demo Dataset: {len(val_data)}")
        val_dl = DataLoader(
            val_data,
            self.batch_size*2,
            shuffle=False,
            drop_last=False,
            num_workers=4,
            pin_memory=True,
            collate_fn=collateFn_patches(
                image_size=self.img_size, patch_size=patch_size, chanels=chanels)
        )
        return val_dl

# ******************************************************
# Visualization Attention Map Functions
# ******************************************************

company_colors = [
    (0,160,215), # blue
    (220,55,60), # red
    (245,180,0), # yellow
    (10,120,190), # navy
    (40,150,100), # green
    (135,75,145), # purple
]
company_colors = [(float(c[0]) / 255.0, float(c[1]) / 255.0, float(c[2]) / 255.0) for c in company_colors]


# Create the transparence mask
def apply_mask(image, mask, color, alpha=0.5):
    for c in range(3):
        image[:, :, c] = image[:, :, c] * \
            (1 - alpha * mask) + alpha * mask * color[c] * 255
    return image

# Creat Apply Mask 2 
def apply_mask2(image, mask, color, alpha=0.5):
    """Apply the given mask to the image.
    """
    t= 0.2
    mi = np.min(mask)
    ma = np.max(mask)
    mask = (mask - mi) / (ma - mi)
    for c in range(3):
        image[:, :, c] = image[:, :, c] * (1 - alpha * np.sqrt(mask) * (mask>t))+ alpha * np.sqrt(mask) * (mask>t) * color[c] * 255
    return image

# Create the random Color for the mask
def random_colors(N, bright=True):
    """
    Generate random colors.
    """
    brightness = 1.0 if bright else 0.7
    hsv = [(i / N, 1, brightness) for i in range(N)]
    colors = list(map(lambda c: colorsys.hsv_to_rgb(*c), hsv))
    random.shuffle(colors)
    return colors


def display_instances(image, mask, fname='test', figsize=(5, 5), blur=False, contour=True, alpha=0.5, visualize_each_head=False):
    fig = plt.figure(figsize=figsize, frameon=False)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    ax = plt.gca()
    if visualize_each_head:
        N = 1
        mask = mask[None, :, :]
    else: 
        # Change this number corresponding the number of attention heads
        N=6
        #mask = mask[None, :, :]
    # Generate random colors
    colors = random_colors(N)
    # Show area outside image boudaries.
    height, width = image.shape[:2]
    margin = 0
    ax.set_ylim(height + margin, -margin)
    ax.set_xlim(-margin, width + margin)
    ax.axis('off')
    masked_image = image.astype(np.uint32).copy()
    for i in range(N):
        color = colors[i]
        _mask = mask[i]

        if blur:
            _mask = cv2.blur(_mask, (10, 10))
        # Mask
        masked_image = apply_mask(masked_image, _mask, color, alpha)
        # Mask Polygon
        # Pad to ensure proper polygons for masks that touch image edges
        if contour:
            padded_mask = np.zeros((_mask.shape[0] + 2, _mask.shape[1] + 2))
            padded_mask[1:-1, 1:-1] = _mask
            contours = find_contours(padded_mask, 0.5)
            for verts in contours:
                # substract the padding and flip (y, x) to (x, y)
                verts = np.fliplr(verts) - 1
                p = Polygon(verts, facecolor='none', edgecolor=color)
                ax.add_patch(p)

    ax.imshow(masked_image.astype(np.uint8), cmap="inferno", aspect='auto')
    fig.savefig(fname)
    print(f"{fname} saved.")
    return

def attention_retrieving(args, img, threshold, attention_input, save_dir, blur=False, contour=True, alpha=0.5, visualize_each_head=True):
    '''

    Args: 
    image: the input image tensor (3, h, w)
    patch_size: the image will patches into multiple patches (patch_size, patch_size)
    threshold: to a certain percentage of the mass 
    attention_input: the attention output from VIT model (Usually from the last attention block of the ViT architecture)

    '''
    # make the image divisible by the patch size
    w, h = img.shape[1] - img.shape[1] % args.patch_size, img.shape[2] - \
        img.shape[2] % args.patch_size
    img = img[:, :w, :h].unsqueeze(0)
    image = img
    print(f"image after patching shape : {image.shape}")

    w_featmap = image.shape[-2] // args.patch_size
    h_featmap = image.shape[-1] // args.patch_size
    print(f"w_featmap size of : {w_featmap}")
    # Number of head
    nh = attention_input.shape[1]

    # We only keep the output Patch attention#Removing CLS token
    attentions = attention_input[0, :, 0, 1:].reshape(nh, -1)

    print(f"This is the Shape attentions using CLS Token : {attentions.shape}")
    th_attn=None
    if threshold is not None:
        # Keeping only a certain percentage of the mass
        val, idx = torch.sort(attentions)
        val /= torch.sum(val, dim=1, keepdim=True)
        cumval = torch.cumsum(val, dim=1)
        th_attn = cumval > (1-threshold)

        idx2 = torch.argsort(idx)
        for head in range(nh):
            th_attn[head] = th_attn[head][idx2[head]]

        th_attn = th_attn.reshape(nh, w_featmap, h_featmap).float()
        # Interpolate
        th_attn = nn.functional.interpolate(th_attn.unsqueeze(
            0), scale_factor=args.patch_size, mode="nearest")[0].cpu().numpy()

    attentions = attentions.reshape(nh, w_featmap, h_featmap)

    attentions = nn.functional.interpolate(attentions.unsqueeze(
        0), scale_factor=args.patch_size, mode="nearest")[0].cpu().numpy()

    # Saving attention heatmaps
    os.makedirs(save_dir, exist_ok=True)
    torchvision.utils.save_image(torchvision.utils.make_grid(
        image, normalize=True, scale_each=True), os.path.join(save_dir, "attention_visual_.png"))
    
    attns = Image.new('RGB', (attentions.shape[2] * nh, attentions.shape[1]))
    img_= Image.open(os.path.join(save_dir, "attention_visual_.png"))
    for j in range(nh):
        fname = os.path.join(save_dir, "attn-head_" + str(j) + ".png")
        plt.imsave(fname=fname, arr=attentions[j], format='png')
        print(f'{fname} saved.')
        attns.paste(Image.open(fname),(j*attentions.shape[2], 0))

    if threshold is not None:
        image = skimage.io.imread(os.path.join(
            save_dir, "attention_visual_.png"))
        if visualize_each_head:
            for j in range(nh):
                display_instances(image, th_attn[j], fname=os.path.join(
                    save_dir, "mask_th" + str(threshold) + "_head" + str(j) + '.png'), blur=blur, contour=contour, alpha=alpha, visualize_each_head=visualize_each_head)
        else: 
            display_instances(image, th_attn, fname=os.path.join(
                save_dir, "mask_th" + str(threshold) + "all_head" + '.png'), blur=blur, contour=contour, alpha=alpha, visualize_each_head=visualize_each_head)
    
    return attentions, th_attn, img_, attns

def attention_map_color(args, image, th_attn, attention_image, save_dir, blur=False, contour=False, alpha=0.5): 
    M= image.max()
    m= image.min() 
    
    span=64 
    image =  ((image-m)/(M-m))*span + (256 -span)
    image = image.mean(axis=2)
    image= np.repeat(image[:, :, np.newaxis], 3, axis=2)
    print(f"this is image shape: {image.shape}")

    att_head= attention_image.shape[0]

    for j in range(att_head):
        m = attention_image[j]
        m *= th_attn[j]
        attention_image[j]= m 
    mask = np.stack([attention_image[j] for j in range(att_head)])
    print(f"this is mask shape : {mask.shape}")
    
    figsize = tuple([i / 100 for i in (args.image_size, args.image_size,)])
    fig = plt.figure(figsize=figsize, frameon=False, dpi=100)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    ax = plt.gca()

    if len(mask.shape) == 3:
        N = mask.shape[0]
        print(f"this is N : {N}")
    else:
        N = 1
        mask = mask[None, :, :]

    for i in range(N):
        mask[i] = mask[i] * ( mask[i] == np.amax(mask, axis=0))
    a = np.cumsum(mask, axis=0)
    for i in range(N):
        mask[i] = mask[i] * (mask[i] == a[i])
    if N > 6:  
        N=6 
    colors = company_colors[:N]

    # Show area outside image boundaries.
    height, width = image.shape[:2]
    margin = 0
    ax.set_ylim(height + margin, -margin)
    ax.set_xlim(-margin, width + margin)
    ax.axis('off')
    image=image.numpy()
    masked_image = 0.1*image.astype(np.uint32).copy()
    print(f"this is masked image shape : {masked_image.shape}")
    for i in range(N):
        color = colors[i]
        _mask = mask[i]
        if blur:
            _mask = cv2.blur(_mask,(10,10))
        # Mask
        masked_image = apply_mask2(masked_image, _mask, color, alpha)
        # Mask Polygon
        # Pad to ensure proper polygons for masks that touch image edges.
        if contour:
            padded_mask = np.zeros(
                (_mask.shape[0] + 2, _mask.shape[1] + 2))#, dtype=np.uint8)
            padded_mask[1:-1, 1:-1] = _mask
            contours = find_contours(padded_mask, 0.5)
            for verts in contours:
                # Subtract the padding and flip (y, x) to (x, y)
                verts = np.fliplr(verts) - 1
                p = Polygon(verts, facecolor="none", edgecolor=color)
                ax.add_patch(p)
    ax.imshow(masked_image.astype(np.uint8), aspect='auto')
    ax.axis('image')
    #fname = os.path.join(output_dir, 'bnw-{:04d}'.format(imid))
    fname = os.path.join(save_dir, "attn_color.png")
    fig.savefig(fname)
    attn_color = Image.open(fname)

    return attn_color
