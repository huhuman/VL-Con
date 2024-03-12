from clip_retrieval.clip_client import ClipClient
import xmltodict
import numpy as np
import pandas as pd
import numpy as np
import json
import requests
import shutil
import os

def get_uniformat_activities_xml(xml_path='__test_inputs/Uniformat_2010_CSI.xml'):
    # read xml
    uniformat_dict_list = None
    with open(xml_path, 'r') as f:
        tmp = xmltodict.parse(f.read())
        uniformat_dict_list = tmp['BuildingInformation']['Classification']['System']['Items']['Item']
    uniformat_codes, uniformat_texts = [], []
    def __parse_activity_name(activity_dict):
        ID = activity_dict['ID']
        if ID[0] not in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            return
        Name = activity_dict['Name']
        uniformat_codes.append(ID)
        uniformat_texts.append(Name)
        if 'Children' in activity_dict.keys():
            child_dicts = activity_dict['Children']['Item']
            if not isinstance(child_dicts, list):
                child_dicts = [child_dicts]
            for child_dict in child_dicts:
                __parse_activity_name(child_dict)
    _ = list(map(__parse_activity_name, uniformat_dict_list))
    return uniformat_codes, uniformat_texts

def prompt_wrapping(idx, texts, codes, option=1):
    '''
    The proposed prompts
    '''
    text = texts[idx]
    if option == 1:
        return f"A photo of {text}, a type of building construction activity"
    if option == 2:
        code = codes[idx]
        for len_number in [5, 3, 1]:
            if len(code) > len_number:
                text += ','
                text += texts[np.where(codes == code[:len_number])[0]][0]
        return f"A photo of {text}"
    if option == 3:
        return f"A photo of {text}, revit"

def download_img(clip_result, session, headers=None, export_dir='./'):
    url = clip_result['url']
    try:
        r = session.get(result['url'], headers=headers, stream=True, timeout=5)
    except:
        r = None
    # except requests.exceptions.RequestException as e:
    # except requests.exceptions.Timeout as e:
    if r is None:
        return False
    if r.status_code == 200:
        similarity = int(clip_result['similarity']*100)
        img_id = clip_result['id']
        img_save_path = os.path.join(export_dir, f'{similarity}_{img_id}.jpg')
        with open(img_save_path, 'w+b') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
    return True

def main():
    client = ClipClient(url="https://knn.laion.ai/knn-service", indice_name="laion5B-L-14")
    clip_retrieved_images = {}
    uniformat_codes, uniformat_texts = get_uniformat_activities_xml()
    for text in uniformat_texts:
        results = client.query(text=text)
        clip_retrieved_images[text] = results
 
    img_root = "Uniformat_image"
    os.makedirs(img_root, exist_ok=True)
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}
    for code, text in zip(uniformat_codes, uniformat_texts):
        results = clip_retrieved_images[text]
        no_slash_text = text.replace('/', ' ')
        element_root = os.path.join(img_root, f"{code}_{no_slash_text}")
        os.makedirs(element_root, exist_ok=True)
        count = 0
        print(f"{code}_{no_slash_text}")
        for i, result in enumerate(results):
            if count >= 10:
                break
            is_downloaded = download_img(result, session, headers, element_root)
            if is_downloaded:
                count += 1

if __name__ == '__main__':
    main()