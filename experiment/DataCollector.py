import os
import time
import cv2
from os.path import join as pjoin
import xmltodict
import json


class DataCollector:
    def __init__(self, adb_device, app_name='twitter', test_case_no=1, output_file_root='datacollect'):
        self.adb_device = adb_device  # ppadb device
        self.device_name = self.adb_device.get_serial_no()

        self.app_name = app_name
        self.test_case_no = test_case_no
        self.ui_no = 0

        self.screenshot = None  # cv2 image
        self.vh = None          # dict

        self.action = {'type': '', 'coordinate': [(-1, -1), (-1, -1)]}  # {'type': 'click' or 'swipe', 'coordinate': [(start), (end)]}
        self.actions = []       # list of actions for this test case

        # output file paths
        self.testcase_save_dir = pjoin(output_file_root, app_name, 'testcase' + str(test_case_no))
        os.makedirs(self.testcase_save_dir, exist_ok=True)
        print('*** Save data to dir', self.testcase_save_dir, '***')
        self.output_file_path_screenshot = pjoin(self.testcase_save_dir, str(self.ui_no) + '.png')
        self.output_file_path_xml = pjoin(self.testcase_save_dir, str(self.ui_no) + '.xml')
        self.output_file_path_json = pjoin(self.testcase_save_dir, str(self.ui_no) + '.json')

    def get_devices_info(self):
        print("Device Name:%s Resolution:%s" % (self.device_name, self.adb_device.wm_size()))

    def cap_screenshot(self, recur_time=0):
        screen = self.adb_device.screencap()
        with open(self.output_file_path_screenshot, "wb") as fp:
            fp.write(screen)
        self.screenshot = cv2.imread(self.output_file_path_screenshot)
        print('Save screenshot to', self.output_file_path_screenshot)
        # recurrently load to avoid failure
        if recur_time < 3 and self.screenshot is None:
            self.cap_screenshot(recur_time+1)

    def cap_vh(self):
        self.adb_device.shell('uiautomator dump')
        self.adb_device.pull('/sdcard/window_dump.xml', self.output_file_path_xml)
        print('Save xml to', self.output_file_path_xml)
        self.vh = xmltodict.parse(open(self.output_file_path_xml, 'r', encoding='utf-8').read())
        json.dump(self.vh, open(self.output_file_path_json, 'w', encoding='utf-8'), indent=4)
        print('Save view hierarchy to', self.output_file_path_json)

    def cap_ui_info(self):
        self.update_output_file_path()
        self.cap_screenshot()
        self.cap_vh()

    def update_output_file_path(self):
        self.output_file_path_screenshot = pjoin(self.testcase_save_dir, str(self.ui_no) + '.png')
        self.output_file_path_xml = pjoin(self.testcase_save_dir, str(self.ui_no) + '.xml')
        self.output_file_path_json = pjoin(self.testcase_save_dir, str(self.ui_no) + '.json')

    '''
    ********************************************
    *** Convert the VH format to Rico format ***
    ********************************************
    '''
    def reformat_node(self, node):
        node_new = {}
        for key in node.keys():
            if node[key] == 'true':
                node[key] = True
            elif node[key] == 'false':
                node[key] = False

            if key == 'node':
                node_new['children'] = node['node']
            elif key == '@bounds':
                node_new['bounds'] = eval(node['@bounds'].replace('][', ','))
            elif key == '@index':
                continue
            else:
                node_new[key.replace('@', '')] = node[key]
        return node_new

    def cvt_node_to_rico_format(self, node):
        node = self.reformat_node(node)
        if 'children' in node:
            if type(node['children']) == list:
                new_children = []
                for child in node['children']:
                    new_children.append(self.cvt_node_to_rico_format(child))
                node['children'] = new_children
            else:
                node['children'] = [self.cvt_node_to_rico_format(node['children'])]
        return node

    def reformat_vh_json(self):
        self.vh = {'activity': {'root': self.cvt_node_to_rico_format(self.vh['hierarchy']['node'])}}
        json.dump(self.vh, open(self.output_file_path_json, 'w', encoding='utf-8'), indent=4)
        print('Save reformatted vh to', self.output_file_path_json)

    '''
    *********************
    *** Record action ***
    *********************
    '''
    def record_action(self, window_resize_ratio=3):
        '''
        :param window_resize_ratio: the ratio to shrink the window for better view
            window_size = device_size // window_resize_ratio
        '''
        win_name = 'Control panel screen (Press "q" to exit)'
        device_size = self.adb_device.wm_size()    # width, height
        window_size = (device_size[0] // window_resize_ratio, device_size[1] // window_resize_ratio)

        def on_mouse(event, x, y, flag, params):
            '''
            :param params: [board (image), is pressing (boolean), press time (float)]
            :param x: (width direction) click position on the window
            :param y: (height direction) click position on the window
            '''
            x_device, y_device = int(x * window_resize_ratio), int(y * window_resize_ratio)
            # Press button
            if event == cv2.EVENT_LBUTTONDOWN:
                params[1] = True
                # draw the press location
                cv2.circle(params[0], (x, y), 10, (255, 0, 255), -1)
                cv2.imshow(win_name, params[0])
                self.action['coordinate'][0] = (x_device, y_device)
                params[2] = time.time()     # record the time of pressing down, for checking long press action
            # Drag
            elif params[1] and event == cv2.EVENT_MOUSEMOVE:
                cv2.circle(params[0], (x, y), 10, (255, 0, 255), 2)
                cv2.imshow(win_name, params[0])
            # Lift button
            elif event == cv2.EVENT_LBUTTONUP:
                params[1] = False
                x_start, y_start = self.action['coordinate'][0]
                # swipe
                if abs(x_start - x_device) >= 10 or abs(y_start - y_device) >= 10:
                    print('\n****** Scroll from (%d, %d) to (%d, %d) in %.3fs ******' % (x_start, y_start, x_device, y_device, time.time() - params[2]))
                    self.adb_device.input_swipe(x_start, y_start, x_device, y_device, 500)
                    # record action
                    self.action['type'] = 'swipe'
                    self.action['coordinate'][0] = (x_device, y_device)
                # click
                else:
                    print('\n****** Click (%d, %d) ******' % (x_start, y_start))
                    self.adb_device.input_tap(x_start, y_start)
                    # record action
                    self.action['type'] = 'click'
                    self.action['coordinate'][1] = (-1, -1)
                self.actions.append(self.action)
                # next ui
                time.sleep(0.5)
                self.ui_no += 1
                self.cap_ui_info()
                params[0] = cv2.resize(self.screenshot.copy(), window_size)
                cv2.imshow(win_name, params[0])

        self.cap_ui_info()
        board = cv2.resize(self.screenshot.copy(), window_size)
        cv2.imshow(win_name, board)
        cv2.setMouseCallback(win_name, on_mouse, [board, False, time.time()])
        key = cv2.waitKey()
        if key == ord('q'):
            cv2.destroyWindow(win_name)
            return


if __name__ == '__main__':
    # start emulator in Android studio first and run to capture screenshot and view hierarchy
    # save vh xml, json and screenshot image to 'data/app_name/test_case_no/device'
    from ppadb.client import Client as AdbClient
    client = AdbClient(host="127.0.0.1", port=5037)

    device = DataCollector(client.devices()[0], app_name='twitter', test_case_no=1)
    device.cap_screenshot()
    device.cap_vh()
    device.reformat_vh_json()