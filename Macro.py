# cython: language_level=3

import os
import re
import time
import ctypes
import win32api
import win32con
import pyWinhook
import HookPatched
import pytesseract
from mss import mss
from threading import Thread
from datetime import datetime, timedelta

import Tool
import MouseTool
from KeyMapping import Ascii_code, Hex_code

class Macro:

    def initMacro(self, MySignal):
        self.MySignal = MySignal

        # 初始化OCR
        pytesseract.pytesseract.tesseract_cmd = r'plugins\Tesseract OCR\tesseract.exe'

        # 初始化鼠标工具
        self.mousetool = MouseTool.MouseUtils()
        self.mvka = ctypes.windll.user32.MapVirtualKeyA

        # 宏文件
        self.macroFile = []

        # 天数初始化
        self.num_days = 0
        # 定时任务状态
        self.scheduledTask_state = False
        # 场景指纹标志
        self.sceneFingerprint_flag = False
        # 按键名称
        self.key_name = ''
        # 宏开关标志
        self.switch_key = False
        # 辅助键记录
        self.key_branch = None
        # 跟随限制标志
        self.follow_state = True
        # 已按下按键列表
        self.pressed_keys = []
        # 鼠标渐进字典
        self.mouse_progress_dict = {}
        # 鼠标位置记录
        self.mouse_memory = {}
        # 录制开关标志
        self.record_switch = False
        # 录制延迟时间记录
        self.record_time = 0
        # 录制内容列表
        self.screeningDict = {}
        self.recordKeyList = []
        # 名称调用功能记录列表
        self.NameCallList = []
        # 名称调用功能支持列表
        self.NameCallDict = {
            '固定连击': lambda i: Thread(target=self.fixed_continuous, args=(i,)).start(),
            '宏': lambda i: Thread(target=self.magnificent_key, args=(i,)).start(),
            '鼠标控制': lambda i: Thread(target=self.Mouse_control, args=(i,)).start(),
            '鼠标渐进': lambda i: Thread(target=self.mouse_progress, args=(i,)).start(),
            '鼠标分支': lambda i: Thread(target=self.mouse_branch, args=(i,)).start(),
            '找图': lambda i: Thread(target=self.seek_picture, args=(i,)).start(),
            '找色': lambda i: Thread(target=self.seek_color, args=(i,)).start(),
            '文字识别': lambda i: Thread(target=self.text_recognition, args=(i,)).start(),
            '定时任务': lambda i: Thread(target=self.scheduledTask, args=(i,)).start(),
            '场景指纹': lambda i: Thread(target=self.sceneFingerprint, args=(i,)).start(),
        }

        self.key_down_map = {
            '按下左键': win32con.MOUSEEVENTF_LEFTDOWN,
            '按下右键': win32con.MOUSEEVENTF_RIGHTDOWN,
            '按下中键': win32con.MOUSEEVENTF_MIDDLEDOWN
        }
        self.key_up_map = {
            '弹起左键': win32con.MOUSEEVENTF_LEFTUP,
            '弹起右键': win32con.MOUSEEVENTF_RIGHTUP,
            '弹起中键': win32con.MOUSEEVENTF_MIDDLEUP
        }
        self.click_map = {
            '单击左键': (win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_LEFTUP),
            '单击右键': (win32con.MOUSEEVENTF_RIGHTDOWN, win32con.MOUSEEVENTF_RIGHTUP),
            '单击中键': (win32con.MOUSEEVENTF_MIDDLEDOWN, win32con.MOUSEEVENTF_MIDDLEUP)
        }


#   --------------------------------------------------鼠标功能-------------------------------------------------

    # 鼠标控制
    def Mouse_control(self, data):
        self.x, self.y = self.mousetool.GetCursorPos()
        x_return, y_return = -1, -1
        mouseReturn = False
        if '鼠标回位' in data and data['鼠标回位'] == '开':
            x_return, y_return = self.mousetool.GetCursorPos()
            mouseReturn = True

        try:
            instruct = data['宏指令'].split(',')
            for i in instruct:
                if not self.switch_key:
                    return

                split_instruct = i.split(' ')   # 按空格拆分动作与参数
                action = split_instruct[0]  # 动作类型

                if action == '延迟':
                    self.mouse_return(mouseReturn, x_return, y_return)
                    if not self.delay(float(i.split(' ')[1])):
                        return
                    x_return, y_return = self.mousetool.GetCursorPos()

                elif action == '记忆坐标' or len(split_instruct) > 1 and split_instruct[1].split('.')[0] in self.mouse_memory:
                    self.memory_coordinate(split_instruct, data.get('鼠标回位', '关'))

                elif action in ['按下左键', '按下右键', '按下中键']:
                    self.mouse_down(action, split_instruct)

                elif action in ['弹起左键', '弹起右键', '弹起中键']:
                    win32api.mouse_event(self.key_up_map[action], 0, 0, 0, 0)
                    self.mouse_return(mouseReturn, x_return, y_return)

                elif action in ['单击左键', '单击右键', '单击中键']:
                    self.mouse_click(action, split_instruct)
                    self.mouse_return(mouseReturn, x_return, y_return)

                elif action == '移动':
                    self.mouse_move(split_instruct)

                elif action == '中键滚动':
                    number = int(split_instruct[1]) * 100
                    win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, number, 0)

                elif action in Ascii_code:
                    self.press_key(action)
                    time.sleep(0.02)
                    self.release_key(action)
                    self.mouse_return(mouseReturn, x_return, y_return)

                elif action in self.NameCallList:
                    self.nameCall(action)

                else:
                    self.MySignal.sendInfo({'action': '显示公告', 'info': f'功能 [鼠标控制] 值 不能为 {i}'})
                    return

        except Exception as e:
            print(e)
            NoticesInfo = '鼠标控制 数据错误，请检查'
            if isinstance(e, ValueError):
                NoticesInfo = f'功能 [鼠标控制] 值 不能为 {i}'
            self.MySignal.sendInfo({'action': '显示公告', 'info': NoticesInfo})

    # 鼠标回位
    def mouse_return(self, flag, x_return, y_return):
        if flag:
            self.mousetool.SetCursorPos(int(x_return), int(y_return))

    # 鼠标按下
    def mouse_down(self, action, split_instruct):
        if len(split_instruct) != 1:
            self.x, self.y = map(int, split_instruct[1:])
            self.mousetool.SetCursorPos(self.x, self.y)
        win32api.mouse_event(self.key_down_map[action], 0, 0, 0, 0)

    # 鼠标单击
    def mouse_click(self, action, split_instruct):
        if len(split_instruct) != 1:
            self.x, self.y = map(int, split_instruct[1:])
            self.mousetool.SetCursorPos(self.x, self.y)
        win32api.mouse_event(self.click_map[action][0], 0, 0, 0, 0)
        time.sleep(0.02)
        win32api.mouse_event(self.click_map[action][1], 0, 0, 0, 0)

    # 鼠标移动
    def mouse_move(self, split_instruct):
        x2, y2, = int(split_instruct[1]), int(split_instruct[2])
        delay = float(split_instruct[3]) if len(split_instruct) > 3 else 0.2
        step_num = 20   # 步数
        averagedelay = round(delay / step_num, 4)   # 平均时间
        stepx, stepy = (x2 - self.x) / step_num, (y2 - self.y) / step_num     # 步长
        for _ in range(step_num):
            self.x, self.y = self.x + stepx, self.y + stepy
            self.mousetool.SetCursorPos(int(self.x), int(self.y))
            time.sleep(averagedelay)

    # 记忆坐标
    def memory_coordinate(self, data, mouse_return):
        print(data)
        keys = [
            '中键滚动', '移动',
            '按下左键', '按下右键', '按下中键',
            '弹起左键', '弹起右键', '弹起中键',
            '单击左键', '单击右键', '单击中键',
        ]
        if data[0] == '记忆坐标':
            x, y = self.mousetool.GetCursorPos()
            self.mouse_memory[data[1]] = {
                'x': x,
                'y': y
            }
        else:
            print(self.mouse_memory)
            if data[0] in keys and data[1].split('.')[0] in self.mouse_memory and len(data) > 1:
                print(11111)
                base_points = {}
                x, y = None, None
                extra_args = []

                # 使用正则表达式解析坐标参数
                coord_pattern = re.compile(
                    r'^([^.]+)(?:\.(x|y)([+-]\d+)?)?$'  # 匹配 point / point.x / point.x+10
                )

                # 解析所有参数
                for param in data[1:]:
                    match = coord_pattern.match(param)
                    if not match:  # 非坐标参数
                        extra_args.append(param)
                        continue

                    # 解析参数组件
                    base, axis, offset = match.groups()
                    if base not in self.mouse_memory:  # 无效基点
                        extra_args.append(param)
                        continue

                    # 获取基点坐标
                    if base not in base_points:
                        base_points[base] = self.mouse_memory[base]

                    # 处理坐标计算
                    if not axis:  # 完整坐标点 (如"point")
                        x = base_points[base]['x']
                        y = base_points[base]['y']
                    else:         # 坐标分量 (如"x+10")
                        current = base_points[base][axis]
                        if offset:
                            op = offset[0]
                            num = int(offset[1:])
                            current = current + num if op == '+' else current - num

                        if axis == 'x':
                            x = current
                            if y is None:  # 自动补全Y坐标
                                y = base_points[base]['y']
                        else:
                            y = current
                            if x is None:  # 自动补全X坐标
                                x = base_points[base]['x']

                # 构建宏指令
                print(22222)
                if x is not None and y is not None:
                    cmd = [data[0], str(x), str(y)] + extra_args
                    memory_data = {
                        '功能类型': '鼠标控制',
                        '鼠标回位': mouse_return,
                        '宏指令': ' '.join(cmd).strip()
                    }
                    print(memory_data)
                    Thread(target=self.Mouse_control, args=(memory_data,)).start()

    # 鼠标渐进
    def mouse_progress(self, data, reset=False):

        if '+' not in data['宏指令']:
            self.MySignal.sendInfo({'action': '显示公告', 'info': '功能 [鼠标渐进] 必须存在 + 号'})
            return

        # 生成指令
        def generate_instruct(name):

            if not self.switch_key:
                self.mouse_progress_dict = {}
                return

            progress_data = {
                '功能类型': '鼠标控制',
                '鼠标回位': '开' if data.get('鼠标回位') == '开' else '关',
                '宏指令': '',
            }

            progress = self.mouse_progress_dict[name]
            x, y = progress['x'], progress['y']

            if progress['初次触发']:
                progress_data['宏指令'] = f"{progress['动作']} {x[0]} {y[0]}"
                if '额外指令' in progress:
                    progress_data['宏指令'] += f",{progress['额外指令']}"
                progress['初次触发'] = False
            else:
                x[0] += x[1] if len(x) > 1 else 0
                y[0] += y[1] if len(y) > 1 else 0
                progress_data['宏指令'] = f"{progress['动作']} {x[0]} {y[0]}"
                if '额外指令' in progress:
                    progress_data['宏指令'] += f",{progress['额外指令']}"

            Thread(target=self.Mouse_control, args=(progress_data,)).start()

        name = data.get('名称') or data.get('触发键')
        if not name:
            self.MySignal.sendInfo({'action': '显示公告', 'info': '功能 [鼠标渐进] 缺少名称或触发键'})
            return

        if name in self.mouse_progress_dict and not reset:
            generate_instruct(name)
            return

        self.mouse_progress_dict[name] = {}

        # 检查并清理宏指令格式
        try:
            if ',' in data['宏指令']:
                instruct_all = data['宏指令'].split(',')
            else:
                instruct_all = [data['宏指令']]

            addition_instruct = ''
            if len(instruct_all) > 1:
                for i in instruct_all[1:]:
                    addition_instruct += f"{i},"
                self.mouse_progress_dict[name]['额外指令'] = addition_instruct[:-1]


            instruct = instruct_all[0].replace(' +', '+').replace('+ ', '+').split(' ')
            if len(instruct) < 3:
                raise ValueError('宏指令缺少必要参数')

            action, x, y = instruct[:3]

            # 验证坐标格式
            def validate_axis(axis):
                if '+' in axis:
                    parts = axis.split('+')
                    if len(parts) != 2 or not all(part.isdigit() for part in parts):
                        raise ValueError(f'坐标格式错误: {axis}')
                elif not axis.isdigit():
                    raise ValueError(f'坐标格式错误: {axis}')

            validate_axis(x)
            validate_axis(y)

        except ValueError as e:
            self.MySignal.sendInfo({'action': '显示公告', 'info': f'功能 [鼠标渐进] 数据错误: {str(e)}'})
            return

        self.mouse_progress_dict[name]['动作'] = action

        # 解析坐标
        def parse_axis(axis):
            parts = axis.split('+')
            return [int(parts[0])] + ([int(parts[1])] if len(parts) > 1 else [])

        self.mouse_progress_dict[name]['x'] = parse_axis(x)
        self.mouse_progress_dict[name]['y'] = parse_axis(y)

        if len(instruct) == 4 and action == '移动':
            self.mouse_progress_dict[name]['延迟'] = int(instruct[3])
        elif len(instruct) == 4:
            self.MySignal.sendInfo({'action': '显示公告', 'info': '功能 [鼠标渐进] 只有 [移动] 指令可以设置延迟'})
            return

        self.mouse_progress_dict[name]['初次触发'] = True
        if not reset:
            generate_instruct(name)

    # 鼠标分支
    def mouse_branch(self, data):

        # 重置渐进
        def reset_progress(name):
            for i in self.macroFile:
                if '名称' in i and i['名称'] == name:
                    self.mouse_progress(i, reset=True)
                elif '触发键' in i and i['触发键'] == name:
                    self.mouse_progress(i, reset=True)

        # 生成指令
        def generate_instruct(instructs, mouse_return):
            if not instructs:
                return
            mouse_branch_data = {
                "功能类型": "鼠标控制",
                "鼠标回位": "开" if mouse_return else "关",
                "宏指令": "",
            }

            instructs_list = instructs.split(',')
            for i in instructs_list:
                if '重置渐进' in i:
                    reset_progress(i.split(' ')[1])
                else:
                    mouse_branch_data['宏指令'] = i
                    self.Mouse_control(mouse_branch_data)
                    mouse_branch_data['宏指令'] = ""

        # 解析判断条件
        def check_condition(value, operator, threshold):
            if operator == '>':
                return value > threshold
            elif operator == '<':
                return value < threshold
            elif operator == '=':
                return value == threshold
            else:
                return None

        # 执行判断条件
        def execute_judging_conditions(judgingConditions, value):
            threshold = int(judgingConditions[2])
            result = check_condition(value, judgingConditions[1], threshold)

            if result is None:
                self.MySignal.sendInfo({'action': '显示公告', 'info': '功能 [鼠标分支] 判断条件格式错误'})
            elif result:
                generate_instruct(data['分支Y'], True if data.get('鼠标回位') == '开' else False)
            else:
                generate_instruct(data['分支N'], True if data.get('鼠标回位') == '开' else False)

        x, y = self.mousetool.GetCursorPos()
        judgingConditions = data.get('判断').split(' ')
        if len(judgingConditions) == 3 and judgingConditions[0] in ['x', 'y', 'X', 'Y']:
            value = x if judgingConditions[0] in ['x', 'X'] else y
            execute_judging_conditions(judgingConditions, value)
        else:
            self.MySignal.sendInfo({'action': '显示公告', 'info': '功能 [鼠标分支] 判断条件格式错误'})


#   --------------------------------------------------键盘功能-------------------------------------------------

    # 按下
    def press_key(self, key):
        if self.init_config['键鼠模式'] == 'Ascii':
            win32api.keybd_event(Ascii_code[key], 0, 0, 0)
        else:
            win32api.keybd_event(Hex_code[key], self.mvka(Hex_code[key], 0), 0, 0)

    # 弹起
    def release_key(self, key):
        if self.init_config['键鼠模式'] == 'Ascii':
            win32api.keybd_event(Ascii_code[key], 0, win32con.KEYEVENTF_KEYUP, 0)
        else:
            win32api.keybd_event(Hex_code[key], self.mvka(Hex_code[key], 0), win32con.KEYEVENTF_KEYUP, 0)

    # 连击
    def continuous_key(self, data, frequency):
        try:
            while data['触发键'] in self.pressed_keys:
                if data['连击键'] in Ascii_code:
                    self.press_key(data['连击键'])
                    self.release_key(data['连击键'])
                    time.sleep(frequency)
                elif data['连击键'] in self.NameCallList:
                    self.nameCall(data['连击键'])
                    time.sleep(frequency)
        except Exception as a:
            if type(a) is KeyError:
                NoticesInfo = f'功能 [连击] 连击键 不能为 {a}'
            elif type(a) is ValueError:
                temp = str(a).split("'")[1]
                NoticesInfo = f'功能 [连击] 每秒次数 不能为 {temp}'
            self.MySignal.sendInfo({'action': '显示公告', 'info': NoticesInfo})

    # 固定连击
    def fixed_continuous(self, data):
        try:
            if '连击次数' in data and '连击频率' in data:
                for i in range(int(data['连击次数'])):
                    if not self.switch_key:
                        return
                    self.press_key(data['连击键'])
                    time.sleep(0.02)
                    self.release_key(data['连击键'])
                    time.sleep(float(data['连击频率']))
                if '后置指令' in data:
                    info_data = {
                        '宏指令': data['后置指令'],
                    }
                    Thread(target=self.magnificent_key, args=(info_data,)).start()
            else:
                NoticesInfo = '功能 [固定连击] 连击频率 或 连击次数 未设置'

        except Exception as a:
            if type(a) is KeyError:
                NoticesInfo = f'功能 [固定连击] 连击键 不能为 {a}'
            elif type(a) is ValueError:
                temp = str(a).split("'")[1]
                NoticesInfo = f'功能 [固定连击] 不能为 {temp}'
            self.MySignal.sendInfo({'action': '显示公告', 'info': NoticesInfo})

    # 宏
    def magnificent_key(self, data):
        try:
            instruct = data['宏指令'].split(',')
            for i in instruct:
                if i[0:2] == '延迟':
                    if not self.delay(float(i.split(' ')[1])):
                        return
                elif i[0:2] == '按下':
                    order = i.split(' ')[1]
                    self.press_key(order)
                elif i[0:2] == '弹起':
                    order = i.split(' ')[1]
                    self.release_key(order)
                elif i in Ascii_code:
                    self.press_key(i)
                    time.sleep(0.02)
                    self.release_key(i)
                elif i in self.NameCallList:
                    self.nameCall(i)

        except Exception as a:
            if type(a) is KeyError:
                NoticesInfo = f'功能 [宏] 宏指令 不能为 {a}'
            elif type(a) is ValueError:
                temp = str(a).split("'")[1]
                NoticesInfo = f'功能 [宏] 延迟 不能为 {temp}'
            self.MySignal.sendInfo({'action': '显示公告', 'info': NoticesInfo})

    # 有序宏
    def ordered_key(self, data):
        try:
            instruct = data['宏指令'].split(',')
            while data['触发键'] in self.pressed_keys:
                for i in instruct:
                    if data['触发键'] not in self.pressed_keys:
                        return
                    self.press_key(i)
                    time.sleep(0.02)
                    self.release_key(i)
                    if '后置指令' in data:
                        self.magnificent_key({'宏指令': data['后置指令']})
        except Exception as a:
            if type(a) is KeyError:
                NoticesInfo = f'功能 [有序宏] 宏指令 不能为 {a}'
            elif type(a) is ValueError:
                temp = str(a).split("'")[1]
                NoticesInfo = f'功能 [有序宏] 延迟 不能为 {temp}'
            self.MySignal.sendInfo({'action': '显示公告', 'info': NoticesInfo})

    # 跟随
    def follow_key(self, data, state):
        if state:
            if self.follow_state:
                self.press_key(data['跟随键'])
                self.follow_state = False
        else:
            self.release_key(data['跟随键'])
            self.follow_state = True

    # 组合键
    def catapult(self, data, direction, Ndirection):
        key_mappings = {
            '辅助': direction,
            '反辅助': Ndirection,
        }
        try:
            if '分支1' in data:
                if key_mappings['辅助'] == data['辅助1']:
                    if data['分支1']:
                        i = {"宏指令": data['分支1']}
                        Thread(target=self.Mouse_control, args=(i, )).start()
                else:
                    if data['分支2']:
                        i = {"宏指令": data['分支2']}
                        Thread(target=self.Mouse_control, args=(i, )).start()
            else:
                instruct = data['宏指令'].split(',')
                for i in instruct:

                    if '!' in i:
                        if self.key_state == '点击':
                            i = i[1:]
                        else:
                            continue

                    if '*' in i:
                        if self.key_state == '长按':
                            i = i[1:]
                        else:
                            continue

                    if i[0:2] == '延迟':
                        if not self.delay(float(i.split(' ')[1])):
                            return

                    elif i[0:2] == '按下':
                        order = i.split(' ')[1]
                        if order in key_mappings:
                            self.press_key(key_mappings[order])
                        else:
                            self.press_key(order)

                    elif i[0:2] == '弹起':
                        order = i.split(' ')[1]
                        if order in key_mappings:
                            self.release_key(key_mappings[order])
                        else:
                            self.release_key(order)

                    elif i in Ascii_code:
                        self.press_key(i)
                        time.sleep(0.02)
                        self.release_key(i)

                    elif i in self.NameCallList:
                        self.nameCall(i)

        except Exception as a:
            if type(a) is KeyError:
                if str(a) == '':
                    NoticesInfo = '功能 [组合键] 按下、弹起 多出空格'
                else:
                    NoticesInfo = f'功能 [组合键] 宏指令、辅助键 不能为 {a}'
            elif type(a) is ValueError:
                temp = str(a).split("'")[1]
                NoticesInfo = f'功能 [组合键] 延迟 不能为 {temp}'
            self.MySignal.sendInfo({'action': '显示公告', 'info': NoticesInfo})

    # 映射键
    def mappings(self, data, direction, mapping, Ndirection, Nmapping):
        key_mappings = {
            '辅助': direction,
            '反辅助': Ndirection,
            '映射': mapping,
            '反映射': Nmapping
        }
        try:
            instruct = data['宏指令'].split(',')
            for i in instruct:

                if '!' in i:
                    if self.key_state == '点击':
                        i = i[1:]
                    else:
                        continue

                if '*' in i:
                    if self.key_state == '长按':
                        i = i[1:]
                    else:
                        continue

                if i[0:2] == '延迟':
                    if not self.delay(float(i.split(' ')[1])):
                        return

                elif i[0:2] == '按下':
                    order = i.split(' ')[1]
                    if order in key_mappings:
                        self.press_key(key_mappings[order])
                    else:
                        self.press_key(order)

                elif i[0:2] == '弹起':
                    order = i.split(' ')[1]
                    if order in key_mappings:
                        self.release_key(key_mappings[order])
                    else:
                        self.release_key(order)

                elif i in Ascii_code:
                    self.press_key(i)
                    time.sleep(0.02)
                    self.release_key(i)

                elif i in self.NameCallList:
                    self.nameCall(i)

        except Exception as a:
            if type(a) is KeyError:
                if str(a) == '':
                    NoticesInfo = '功能 [映射键] 按下、弹起 多出空格'
                else:
                    NoticesInfo = f'功能 [映射键] 宏指令、辅助键、映射键 不能为 {a}'
            elif type(a) is ValueError:
                temp = str(a).split("'")[1]
                NoticesInfo = f'功能 [映射键] 延迟 不能为 {temp}'
            self.MySignal.sendInfo({'action': '显示公告', 'info': NoticesInfo})


#   --------------------------------------------------其它功能-------------------------------------------------

    # 延迟
    def delay(self, dtime):
        inttime = int(dtime)
        floattime = round(dtime - inttime, 3)
        if inttime > 0:
            for i in range(inttime):
                if not self.switch_key:
                    return False
                time.sleep(1)
        if floattime > 0:
            time.sleep(floattime)
        return True

    # 找图
    def seek_picture(self, data):

        if '图片名称' not in data:
            self.MySignal.sendInfo({'action': '显示公告', 'info': '请给出需要寻找的图片的名称'})
            return

        target_path = f'data\\img\\seek_picture\\{data["图片名称"]}'
        if not os.path.exists(target_path):
            self.MySignal.sendInfo({'action': '显示公告', 'info': '图片不存在'})
            return

        screen = Tool.screenshot(data, self.desktop_size[0], self.desktop_size[1])
        coordinates = Tool.pictureMatching(data, screen, target_path)
        if coordinates:
            self.mousetool.SetCursorPos(coordinates[0], coordinates[1])
            if data['分支Y']:
                Thread(target=self.Mouse_control, args=({"宏指令": data['分支Y']},)).start()
        else:
            if data['分支N']:
                Thread(target=self.Mouse_control, args=({"宏指令": data['分支N']},)).start()

    # 找色
    def seek_color(self, data):

        # 16进制颜色格式转换为RGB格式
        def hex_to_rgb(hex_color):
            # 去除字符串中的 '#'
            hex_color = hex_color.replace('#', '')
            # RGB 0, 2, 4       BGR 4, 2, 0
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        def get_pixel_color(x, y):
            with mss() as sct:
                monitor = {"top": y, "left": x, "width": 1, "height": 1}
                return sct.grab(monitor).pixel(0, 0)    # 返回(R, G, B)

        # 计算颜色相似度
        def color_similarity(color1, color2):
            print(f'获取到的颜色: {color1}, 目标颜色: {color2}')
            delta = sum(abs(c1 - c2) for c1, c2 in zip(color1, color2))
            return 1 - delta / (255 * 3)

        mode = data['模式'] if '模式' in data else '全部'

        similarity = float(data['相似度']) if '相似度' in data else 0.8

        try:
            targetColorList = [hex_to_rgb(color) for color in data['颜色'].split(',')]
        except Exception:
            self.MySignal.sendInfo({'action': '显示公告', 'info': '功能 [找色] 颜色值错误'})
            return

        try:
            coordinateList = [[int(coord) for coord in coords.split(' ')] for coords in data['坐标'].split(',')]
        except Exception:
            self.MySignal.sendInfo({'action': '显示公告', 'info': '功能 [找色] 坐标值错误'})
            return

        # 检查 颜色数量与坐标数量的一致性
        if len(targetColorList) != len(coordinateList):
            self.MySignal.sendInfo({'action': '显示公告', 'info': '功能 [找色] 颜色数量与坐标数量不一致'})
            return

        # 执行找色
        seekColorFlag = False
        for i, (coord, target_color) in enumerate(zip(coordinateList, targetColorList)):
            if color_similarity(get_pixel_color(*coord), target_color) >= similarity:
                seekColorFlag = True
                if mode == '单一':
                    print(11111111)
                    break
            else:
                seekColorFlag = False
                if mode == '全部':
                    print(22222222)
                    break

        # 执行分支
        if seekColorFlag:
            if data['分支Y']:
                i = {"宏指令": data['分支Y']}
                Thread(target=self.Mouse_control, args=(i, )).start()
        else:
            if data['分支N']:
                i = {"宏指令": data['分支N']}
                Thread(target=self.Mouse_control, args=(i, )).start()

    # 文字识别
    def text_recognition(self, data):
        try:
            if '目标内容' not in data:
                self.MySignal.sendInfo({'action': '显示公告', 'info': '请给出需要识别的目标内容'})
                return

            # 截图
            img_data = Tool.screenshot(data, self.desktop_size[0], self.desktop_size[1], PILMD=True)

            # 预处理
            if '字体颜色' not in data:
                img_data = Tool.imagePreprocessing(img_data)
            else:
                img_data = Tool.imagePreprocessings(img_data, data['字体颜色'], int(data['颜色阈值']) if '颜色阈值' in data else 150)
            if '调试模式' in data:
                if data['调试模式'] == '开':
                    img_data.save(r'data\img\seek_picture\color_processed.png')

            # 文字识别
            text = pytesseract.image_to_string(img_data, lang='chi_sim')
            print(f'识别结果: {text}')

            if data['目标内容'] in text:
                if data['分支Y']:
                    i = {"宏指令": data['分支Y']}
                    Thread(target=self.Mouse_control, args=(i, )).start()
            else:
                if data['分支N']:
                    i = {"宏指令": data['分支N']}
                    Thread(target=self.Mouse_control, args=(i, )).start()

        except Exception as e:
            print(e)
            self.MySignal.sendInfo({'action': '显示公告', 'info': f'功能 [文字识别] 错误：{e}'})

    # 录制
    def transcribe(self, delay, instruction):
        data = instruction.split(' ')
        # 存在就累加延迟时间
        if data[0] == '按下' and data[1] in self.screeningDict:
            self.screeningDict[data[1]] += delay
            return

        # 不存在就记录
        if data[0] == '按下' and data[1] not in self.screeningDict:
            self.screeningDict[data[1]] = 0

        # 等于 弹起 就删除记录
        elif data[0] == '弹起' and data[1] in self.screeningDict:
            delay += self.screeningDict[data[1]]
            del self.screeningDict[data[1]]

        if delay is None:
            self.recordKeyList.append(instruction)
        else:
            delay = round(delay, 3)
            self.recordKeyList.append(f'延迟 {delay}')
            self.recordKeyList.append(instruction)

    # 保存录制
    def save_transcribe(self):

        key_len = len(self.recordKeyList)
        instructions = ''

        for i in self.macroFile:
            if '功能类型' in i and i['功能类型'] == '录制':
                for k in self.recordKeyList:
                    key_len = key_len - 1
                    if key_len == 0:
                        instructions = instructions + k
                    else:
                        instructions = instructions + (k + ',')
                i['宏指令'] = instructions
                break
        self.recordKeyList = []
        self.MySignal.sendInfo({'action': '录制写入', 'info': self.macroFile})

    # 回放录制
    def playback_transcribes(self, data):
        try:
            instruct = data['宏指令'].split(',')
            for i in instruct:
                if i[0:2] == '延迟':
                    if not self.delay(float(i.split(' ')[1])):
                        return

                elif i[0:2] == '按下':
                    order = i.split(' ')[1]
                    self.press_key(order)

                elif i[0:2] == '弹起':
                    order = i.split(' ')[1]
                    self.release_key(order)

                elif i in Ascii_code:
                    self.press_key(i)
                    time.sleep(0.02)
                    self.release_key(i)

                elif i in self.NameCallList:
                    self.nameCall(i)

        except Exception as a:
            if type(a) is KeyError:
                if str(a) == '':
                    NoticesInfo = '功能 [录制] 按下、弹起 多出空格'
                else:
                    NoticesInfo = f'功能 [录制] 宏指令、辅助键、映射键 不能为 {a}'
            elif type(a) is ValueError:
                temp = str(a).split("'")[1]
                NoticesInfo = f'功能 [录制] 延迟 不能为 {temp}'
            self.MySignal.sendInfo({'action': '显示公告', 'info': NoticesInfo})

    # 设置鼠标图标
    def set_mouse_cursor(self, state:bool):
        if state:
            cursor_normal_file = r'res\img\CursorNormal.cur'
            if os.path.exists(cursor_normal_file):
                cursor = ctypes.windll.user32.LoadCursorFromFileW(cursor_normal_file)
                if cursor:
                    ctypes.windll.user32.SetSystemCursor(cursor, 32512)
        else:
            ctypes.windll.user32.SystemParametersInfoW(0x0057, 0, None, 0)

    # 定时任务
    def scheduledTask(self, data):

        # 获取当前时间
        def get_currentTime():
            today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
            return datetime.now().replace(year=today.year, month=today.month, day=today.day)

        # 计算时间是否为下一天
        def is_next_day(time_str1, time_str2):
            time1 = datetime.strptime(time_str1, '%H:%M:%S')
            time2 = datetime.strptime(time_str2, '%H:%M:%S')

            today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
            if time1 > time2:
                return (time2 + timedelta(days=1)).replace(year=today.year, month=today.month, day=today.day + 1)
            else:
                return (time2).replace(year=today.year, month=today.month, day=today.day)

        # 启动任务
        def startTask():
            startupTime =  is_next_day(datetime.fromtimestamp(time.time()).strftime('%H:%M:%S'), data['启动时间'])
            while self.scheduledTask_state:
                if get_currentTime() > startupTime:
                    i = {"宏指令": f"{self.init_config['启动键鼠控制']},{data['宏指令']}"}
                    Thread(target=self.Mouse_control, args=(i, )).start()
                    break
                time.sleep(10)
            endTask()

        # 结束任务
        def endTask():
            endTime =  is_next_day(data['启动时间'], data['结束时间'])
            while self.scheduledTask_state:
                time.sleep(10)
                if get_currentTime() > endTime:
                    i = {"宏指令": f"{self.init_config['停止键鼠控制']}"}
                    Thread(target=self.Mouse_control, args=(i, )).start()
                    break
            self.num_days += 1
            if self.num_days >= int(data['执行次数']):
                return
            startTask()

        self.scheduledTask_state = not self.scheduledTask_state
        if self.scheduledTask_state:
            Thread(target=startTask).start()

    # 场景指纹
    def sceneFingerprint(self, data):
        # 切换状态
        self.sceneFingerprint_flag = not self.sceneFingerprint_flag

        if '图片名称' not in data:
            self.MySignal.sendInfo({'action': '显示公告', 'info': '请给出需要寻找的图片的名称'})
            return

        target_path = f'data\\img\\seek_picture\\{data["图片名称"]}'
        if not os.path.exists(target_path):
            self.MySignal.sendInfo({'action': '显示公告', 'info': '图片不存在'})
            return

        flag_SF1 = True
        flag_SF2 = True
        while self.sceneFingerprint_flag:
            time.sleep(0.3)
            screen = Tool.screenshot(data, self.desktop_size[0], self.desktop_size[1])
            if Tool.pictureMatching(data, screen, target_path):
                if data['分支Y'] and flag_SF1:
                    flag_SF1 = False
                    flag_SF2 = True
                    Thread(target=self.Mouse_control, args=({"宏指令": data['分支Y']},)).start()
            else:
                if data['分支N'] and flag_SF2:
                    flag_SF1 = True
                    flag_SF2 = False
                    Thread(target=self.Mouse_control, args=({"宏指令": data['分支N']},)).start()

    # 名称调用
    def nameCall(self, data):
        for i in self.macroFile:
            if '名称' in i and i['名称'] == data:
                if i['功能类型'] in self.NameCallDict:
                    self.NameCallDict[i['功能类型']](i)
                else:
                    NoticesInfo = f'{i["功能类型"]} 不支持 名称 调用模式，错误字符 {i}'
                    self.MySignal.sendInfo({'action': '显示公告', 'info': NoticesInfo})


#   --------------------------------------------------触发控制-------------------------------------------------

    # 获得按下的键
    def KeyDown(self, event):
        if event.Message == HookPatched.WM_XBUTTONDOWN:
            if event.XButton == 1:
                self.key_name = '侧键1'
            elif event.XButton == 2:
                self.key_name = '侧键2'
        else:
            try:
                self.key_name = str(event.Key)
            except Exception:
                return True

        # 调用快捷键函数
        if self.key_name in self.shortcut_key:
            self.shortcut()

        if self.switch_key:

            if self.key_name in self.support1_trigger:
                self.support1 = True
                self.support2 = False
                self.key_branch = self.key_name
            if self.key_name in self.support2_trigger:
                self.support1 = False
                self.support2 = True
                self.key_branch = self.key_name

            if self.key_name in self.toggleKey:

                # 连击
                def continuous_trigger(data):
                    frequency = round(1 / (int(data['每秒次数']) * 2), 3)
                    Thread(target=self.continuous_key, args=(data, frequency)).start()

                # 组合键
                def catapult_trigger(data):
                    self.key_state = '长按'
                    if self.support1:
                        Thread(target=self.catapult, args=(data, data['辅助1'], data['辅助2'])).start()
                    elif self.support2:
                        Thread(target=self.catapult, args=(data, data['辅助2'], data['辅助1'])).start()

                # 映射键
                def mappings_trigger(data):
                    self.key_state = '长按'
                    if self.support1:
                        Thread(target=self.mappings, args=(data, data['辅助1'], data['映射1'], data['辅助2'], data['映射2'])).start()
                    elif self.support2:
                        Thread(target=self.mappings, args=(data, data['辅助2'], data['映射2'], data['辅助1'], data['映射1'])).start()

                # 录制
                def record_trigger(data):
                    if self.key_name == data['录制停止']:
                        # 录制
                        if not self.record_switch:
                            self.shield = data['屏蔽'].split(',')
                            self.record_switch = True

                        # 保存录制
                        else:
                            self.record_switch = False
                            self.record_time = 0
                            Thread(target=self.save_transcribe).start()

                    if self.key_name == i['回放']:
                        Thread(target=self.playback_transcribes, args=(i, )).start()

                # 检查是否已按下该键
                if self.key_name in self.pressed_keys:
                    return True
                else:
                    self.pressed_keys.append(self.key_name)

                # 触发
                macro = None
                for i in self.macroFile:
                    if '功能类型' in i:
                        if i['功能类型'] == '组合键' and self.key_name == i['触发键']:
                            if self.key_branch == i['辅助1'] or self.key_branch == i['辅助2']:
                                macro = i
                                break
                        elif '触发键' in i and self.key_name == i['触发键']:
                            macro = i
                            break
                        elif '录制停止' in i and (self.key_name == i['录制停止'] or self.key_name == i['回放']):
                            macro = i
                            break

                branch = {
                    '连击': lambda: continuous_trigger(macro),
                    '固定连击': lambda:  Thread(target=self.fixed_continuous, args=(macro, )).start(),
                    '宏': lambda: Thread(target=self.magnificent_key, args=(macro, )).start(),
                    '有序宏': lambda: Thread(target=self.ordered_key, args=(macro, )).start(),
                    '跟随': lambda: Thread(target=self.follow_key, args=(macro, True)).start(),
                    '组合键': lambda: catapult_trigger(macro),
                    '映射键': lambda: mappings_trigger(macro),
                    '录制': lambda: record_trigger(macro),
                    '鼠标控制': lambda: Thread(target=self.Mouse_control, args=(macro, )).start(),
                    '鼠标渐进': lambda: Thread(target=self.mouse_progress, args=(macro, )).start(),
                    '鼠标分支': lambda: Thread(target=self.mouse_branch, args=(macro, )).start(),
                    '找图': lambda: Thread(target=self.seek_picture, args=(macro, )).start(),
                    '找色': lambda: Thread(target=self.seek_color, args=(macro, )).start(),
                    '文字识别': lambda: Thread(target=self.text_recognition, args=(macro, )).start(),
                    '定时任务': lambda: Thread(target=self.scheduledTask, args=(macro, )).start(),
                    '场景指纹': lambda: Thread(target=self.sceneFingerprint, args=(macro, )).start(),
                }

                if macro:
                    branch.get(macro['功能类型'])()

            # 录制
            if self.record_switch:
                if self.key_name not in self.shield:

                    if self.record_time == 0:
                        self.record_time = time.time()
                        Thread(target=self.transcribe, args=(None, f'按下 {self.key_name}')).start()
                    else:
                        delay = round(time.time() - self.record_time, 5)
                        self.record_time = time.time()
                        Thread(target=self.transcribe, args=(delay, f'按下 {self.key_name}')).start()

        return True

    # 获得松开的键
    def KeyUp(self, event):
        if event.Message == HookPatched.WM_XBUTTONUP:
            if event.XButton == 1:
                self.key_name = '侧键1'
            elif event.XButton == 2:
                self.key_name = '侧键2'
        else:
            try:
                self.key_name = str(event.Key)
            except Exception:
                return True

        if self.focus_flag:
            self.startAStopKeyControl('修改启动与停止键')

        elif self.switch_key:

            # if self.key_name in self.support1_trigger or self.key_name in self.support2_trigger:
            #     self.key_branch = None
            #     self.support1 = False
            #     self.support2 = False

            for i in self.macroFile:
                if '功能类型' in i:

                    if i['功能类型'] == '跟随':
                        if self.key_name == i['触发键']:
                            self.follow_key(i, False)

                    elif i['功能类型'] == '组合键' or i['功能类型'] == '映射键':
                        if self.key_name == i['触发键']:
                            self.key_state = '点击'

            # 检查是否已松开该键
            if self.key_name in self.pressed_keys:
                self.pressed_keys.remove(self.key_name)

            # 录制
            if self.record_switch:
                if self.key_name not in self.shield:
                        delay = round(time.time() - self.record_time, 5)
                        self.record_time = time.time()
                        Thread(target=self.transcribe, args=(delay, f'弹起 {self.key_name}')).start()

        return True

    # 监听键鼠
    def KeyHook(self):
        # 实例化监听对象
        hm = pyWinhook.HookManager()
        # 监听按下的键
        hm.KeyDown = self.KeyDown
        # 监听松开的键
        hm.KeyUp = self.KeyUp
        # 监听鼠标按下的键
        hm.MouseAllButtonsDown = self.KeyDown
        # 监听鼠标松开的键
        hm.MouseAllButtonsUp = self.KeyUp
        # 设置键盘钩子
        hm.HookKeyboard()
        # 设置鼠标钩子
        hm.HookMouse()


