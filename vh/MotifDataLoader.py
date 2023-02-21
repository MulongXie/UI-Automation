import os
import json
from os.path import join as pjoin
from glob import glob


class MotifDataLoader:
    def __init__(self, motif_data_root='C:/Mulong/Data/motif_raw_data/raw_data/', processing_app_number=0, processing_task_number=0):
        '''
        motif_raw_data/raw_data/
        -- [app names]
        ---- [task names]
        ------ feasibility.txt
        ------ task.txt
        ------ screens
        -------- [state_name.jpg]
        ------ view_hierarchies
        -------- [state_name.json]
        '''
        self.motif_data_root = motif_data_root
        self.dir_apps = glob(pjoin(self.motif_data_root, '*'))

        self.processing_app_number = processing_app_number
        self.processing_app_path = self.dir_apps[self.processing_app_number]
        print('*** Loading app No %d from %s} ***' % (self.processing_app_number, self.processing_app_path))
        self.dir_tasks = glob(pjoin(self.processing_app_path, '*'))

        self.processing_task_number = processing_task_number
        self.processing_task_path = self.dir_tasks[self.processing_task_number]
        print('* Loading task No %d from %s} *' % (self.processing_task_number, self.processing_task_path))
        self.dir_task_screens = glob(pjoin(self.processing_task_path, 'screens', '*'))
        self.dir_task_vh = glob(pjoin(self.processing_task_path, 'view_hierarchies', '*'))
        self.correct_vh_file_name()

    def load_app_task(self, app_number, task_number):
        self.processing_app_number = app_number
        self.processing_app_path = self.dir_apps[self.processing_app_number]
        print('*** Loading app No %d from %s} ***' % (self.processing_app_number, self.processing_app_path))
        self.dir_tasks = glob(pjoin(self.processing_app_path, '*'))
        self.load_task(task_number)

    def load_task(self, task_number):
        self.processing_task_number = task_number
        self.processing_task_path = self.dir_tasks[self.processing_task_number]
        print('* Loading task No %d from %s} *' % (self.processing_task_number, self.processing_task_path))
        self.dir_task_screens = glob(pjoin(self.processing_task_path, 'screens', '*'))
        self.dir_task_vh = glob(pjoin(self.processing_task_path, 'view_hierarchies', '*'))
        # check if the json file is correctly ended with .json
        self.correct_vh_file_name()

    def correct_vh_file_name(self):
        # check if the json file is correctly ended with .json
        for vh_file in self.dir_task_vh:
            os.rename(vh_file, vh_file.replace('jpg', 'json'))
        self.dir_task_vh = glob(pjoin(self.processing_task_path, 'view_hierarchies', '*'))

    def get_screen_and_vh_file(self, screen_no):
        return self.dir_task_screens[screen_no], self.dir_task_vh[screen_no]
