import os
import cv2
import json
import pandas as pd
from os.path import join as pjoin


class GUIData:
    def __init__(self, gui_img_file, gui_json_file):
        self.img_file = gui_img_file
        self.json_file = gui_json_file
        self.gui_name = gui_img_file.replace('/', '\\').split('\\')[-1].split('.')[0]

        self.img = cv2.resize(cv2.imread(gui_img_file), (1440, 2560))  # cv2 image, the screenshot of the GUI
        self.json = json.load(open(gui_json_file, 'r'))  # json data, the view hierarchy of the GUI

        self.elements = []       # list of element in dictionary {'id':, 'class':...}
        self.element_id = 0
        self.elements_df = None  # pandas.dataframe

    def extract_elements_from_vh(self):
        '''
        Extract elements from raw view hierarchy Json file and store them as dictionaries
        '''
        element_root = self.json['activity']['root']
        self.extract_children_elements(element_root)

    def extract_element_from_semantic_tree(self):
        '''
        Extract element from Rico semantic Json file
        '''
        element_root = self.json
        self.extract_children_elements(element_root)

    def extract_children_elements(self, element):
        '''
        Recursively extract children from an element
        '''
        element['id'] = self.element_id
        # discard illegal elements
        if self.check_if_element_valid(element):
            self.elements.append(element)
        if 'children' in element:
            element['children-id'] = []
            for child in element['children']:
                self.element_id += 1
                element['children-id'].append(self.element_id)
                self.extract_children_elements(child)
            # replace wordy 'children' with 'children-id'
            del element['children']
        del element['ancestors']

    def check_if_element_valid(self, element):
        '''
        Check if the element is valid and should be kept
        '''
        if (element['bounds'][0] >= element['bounds'][2] or element['bounds'][1] >= element['bounds'][3]) or \
                'layout' in element['class'].lower() or\
                'componentLabel' not in element:
            return False
        return True

    def cvt_elements_to_dataframe(self):
        self.elements_df = pd.DataFrame(self.elements)

    def save_element_as_csv(self, file_name='elements.csv'):
        if self.elements_df is None:
            self.cvt_elements_to_dataframe()
        self.elements_df.to_csv(file_name)

    def save_elements_clips_by_compo_label(self, output_dir, elements_count):
        for i, ele in enumerate(self.elements):
            bounds = ele['bounds']
            clip = self.img[bounds[1]: bounds[3], bounds[0]: bounds[2]]
            compo_cls_dir = pjoin(output_dir, ele['componentLabel'])
            if ele['componentLabel'] not in elements_count:
                os.makedirs(compo_cls_dir, exist_ok=True)
                elements_count[ele['componentLabel']] = 1
            else:
                elements_count[ele['componentLabel']] += 1
            clip_name = str(self.gui_name) + '-' + str(i) + '.jpg'
            cv2.imwrite(pjoin(compo_cls_dir, clip_name), clip)
        print(elements_count)

    def save_icon_by_icon_class(self, output_dir, icon_count):
        for i, ele in enumerate(self.elements):
            if ele['componentLabel'] == 'Icon' and 'iconClass' in ele:
                bounds = ele['bounds']
                clip = self.img[bounds[1]: bounds[3], bounds[0]: bounds[2]]
                compo_cls_dir = pjoin(output_dir, ele['iconClass'])
                if ele['iconClass'] not in icon_count:
                    os.makedirs(compo_cls_dir, exist_ok=True)
                    icon_count[ele['iconClass']] = 1
                else:
                    icon_count[ele['iconClass']] += 1
                clip_name = str(self.gui_name) + '-' + str(i) + '.jpg'
                cv2.imwrite(pjoin(compo_cls_dir, clip_name), clip)
        print(icon_count)

    def visualize_elements(self):
        board = self.img.copy()
        for ele in self.elements:
            print(ele['id'], ele['class'])
            print(ele, '\n')
            bounds = ele['bounds']
            clip = self.img[bounds[1]: bounds[3], bounds[0]: bounds[2]]
            cv2.rectangle(board, (bounds[0], bounds[1]), (bounds[2], bounds[3]), (0, 255, 0), 3)
            cv2.imshow('clip', cv2.resize(clip, (clip.shape[1] // 3, clip.shape[0] // 3)))
            cv2.imshow('ele', cv2.resize(board, (board.shape[1] // 3, board.shape[0] // 3)))
            if cv2.waitKey() == ord('q'):
                break
        cv2.destroyAllWindows()
