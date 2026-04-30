import json
import math

class VirtualJoystick:
    """
    虚拟摇杆类 - 与手机APP关联
    用于接收和处理手机APP的摇杆输入数据
    """

    BEHAVIOR_WANDER = 0
    BEHAVIOR_ATTACK = 1

    SERVO_CENTER = 0
    SERVO_LEFT = -1
    SERVO_RIGHT = 1

    def __init__(self, x=0.0, y=0.0, intensity=0.0,
                 behavior=BEHAVIOR_WANDER, debug=False,
                 fire=False, target_offset=0.0):
        """
        初始化虚拟摇杆

        :param x: X轴值（-1.0到1.0，0为中间）
        :param y: Y轴值（-1.0到1.0，0为中间）
        :param intensity: 强度值（0到1.0）
        :param behavior: 行为模式（0=游走，1=攻击）
        :param debug: 是否进入调试模式
        :param fire: 是否触发发射
        :param target_offset: 攻击目标相机偏移量（-1.0到1.0）
        """
        self._raw_x = 0.0
        self._raw_y = 0.0
        self._x = 0.0  # 实际x轴输出
        self._y = 0.0  # 实际y轴输出
        self._intensity = 0.0  # 强度
        self._dead_zone = 0.05  # 死区阈值（小于此值视为0）
        self._behavior = self.BEHAVIOR_WANDER
        self._debug_mode = False
        self._fire_state = 0
        self._target_offset = 0.0
        self._wander_mode_just_switched = False

        # 初始化值
        self.set_behavior(behavior)
        self.set_debug_mode(debug)
        self.set_fire_state(fire)
        self.set_x(x)
        self.set_y(y)
        self.set_intensity(intensity)
        self.set_target_offset(target_offset)
    
    def set_x(self, x):
        """
        设置X轴值
        
        :param x: X轴值（-1.0到1.0，0为中间）
        :return: None
        """
        self._raw_x = max(-1.0, min(1.0, x))
        self._apply_debug_filter()

    def set_y(self, y):
        """
        设置Y轴值
        
        :param y: Y轴值（-1.0到1.0，0为中间）
        :return: None
        """
        self._raw_y = max(-1.0, min(1.0, y))
        self._apply_debug_filter()

    def set_intensity(self, intensity):
        """
        设置强度值
        
        :param intensity: 强度值（0到1.0）
        :return: None
        """
        if intensity is None:
            intensity = self.calculate_magnitude()
        self._intensity = max(0.0, min(1.0, intensity))

    def set_behavior(self, behavior):
        """
        设置行为模式
        :param behavior: 0=游走，1=攻击
        :return: None
        """
        old_behavior = self._behavior
        self._behavior = self.BEHAVIOR_ATTACK if behavior == self.BEHAVIOR_ATTACK else self.BEHAVIOR_WANDER
        if self._behavior == self.BEHAVIOR_WANDER and old_behavior != self.BEHAVIOR_WANDER:
            self._wander_mode_just_switched = True

    def set_debug_mode(self, debug):
        """
        设置调试模式
        :param debug: bool
        :return: None
        """
        self._debug_mode = bool(debug)
        self._apply_debug_filter()

    def set_fire_state(self, fire):
        """
        设置发射状态
        :param fire: bool
        :return: None
        """
        self._fire_state = 1 if fire else 0

    def set_target_offset(self, offset):
        """
        设置相机目标偏移，用于攻击模式伺服控制
        :param offset: -1.0到1.0
        :return: None
        """
        self._target_offset = max(-1.0, min(1.0, offset))

    def _apply_debug_filter(self):
        """
        根据调试模式过滤X/Y轴输入，使其只保留主方向
        """
        self._x = self._raw_x
        self._y = self._raw_y
        if self._debug_mode:
            if abs(self._raw_x) > abs(self._raw_y):
                self._y = 0.0
            else:
                self._x = 0.0
        if abs(self._x) < self._dead_zone:
            self._x = 0.0
        if abs(self._y) < self._dead_zone:
            self._y = 0.0
    
    def get_x(self):
        """
        获取X轴值
        
        :return: X轴值（-1.0到1.0）
        """
        return self._x

    def get_y(self):
        """
        获取Y轴值
        
        :return: Y轴值（-1.0到1.0）
        """
        return self._y

    def get_intensity(self):
        """
        获取强度值
        
        :return: 强度值（0到1.0）
        """
        return self._intensity

    def calculate_magnitude(self):
        """
        根据X、Y轴计算摇杆的实际幅度（距离中心的距离）
        
        :return: 摇杆的实际强度（0到1.0）
        """
        # 计算从原点到(x,y)的距离
        magnitude = math.sqrt(self._x ** 2 + self._y ** 2)
        # 限制在0-1.0范围
        return min(1.0, magnitude)
    
    def get_angle(self):
        """
        计算摇杆的角度（弧度）
        0弧度指向右方(+X)，π/2指向上方(+Y)
        
        :return: 角度（0到2π弧度）
        """
        if self._x == 0.0 and self._y == 0.0:
            return 0.0
        return math.atan2(self._y, self._x)
    
    def get_angle_degrees(self):
        """
        获取摇杆的角度（度数）
        0度指向右方(+X)，90度指向上方(+Y)
        
        :return: 角度（0到360度）
        """
        angle_rad = self.get_angle()
        angle_deg = math.degrees(angle_rad)
        return angle_deg % 360
    
    def is_centered(self):
        """
        判断摇杆是否在中间位置
        
        :return: bool值，True表示在中间
        """
        return self._x == 0.0 and self._y == 0.0
    
    def is_moving(self):
        """
        判断摇杆是否有移动
        
        :return: bool值，True表示在移动
        """
        return not self.is_centered()
    
    def set_dead_zone(self, dead_zone):
        """
        设置死区阈值
        
        :param dead_zone: 死区阈值（建议0.01-0.1之间）
        :return: None
        """
        self._dead_zone = max(0.0, min(0.5, dead_zone))
    
    def get_dead_zone(self):
        """
        获取死区阈值
        
        :return: 死区阈值
        """
        return self._dead_zone
    
    def reset(self):
        """
        重置摇杆到中间位置
        
        :return: None
        """
        self._x = 0.0
        self._y = 0.0
        self._intensity = 0.0
    
    def update_from_app(self, x, y, intensity=None, behavior=None, debug=None,
                        fire=None, target_offset=None):
        """
        从手机APP接收数据并更新摇杆状态

        :param x: X轴值（-1.0到1.0）
        :param y: Y轴值（-1.0到1.0）
        :param intensity: 强度值（0到1.0），若为None则使用XY轴幅度
        :param behavior: 行为模式（0=游走，1=攻击）
        :param debug: 是否调试模式
        :param fire: 是否发射
        :param target_offset: 攻击目标相机偏移（-1.0到1.0）
        :return: None
        """
        self.set_x(x)
        self.set_y(y)
        if behavior is not None:
            self.set_behavior(behavior)
        if debug is not None:
            self.set_debug_mode(debug)
        if fire is not None:
            self.set_fire_state(fire)
        if target_offset is not None:
            self.set_target_offset(target_offset)
        self.set_intensity(intensity if intensity is not None else self.calculate_magnitude())
    
    def get_direction(self):
        """
        获取摇杆的方向名称
        用于调试和显示
        
        :return: 方向字符串
        """
        if self.is_centered():
            return "中间"
        
        # 根据X、Y值确定方向
        directions = []
        if self._y > 0.5:
            directions.append("上")
        elif self._y < -0.5:
            directions.append("下")
        
        if self._x > 0.5:
            directions.append("右")
        elif self._x < -0.5:
            directions.append("左")
        
        return "".join(directions) if directions else "轻微偏移"
    
    def get_servo_command(self):
        """
        获取当前伺服控制命令
        :return: -1（左）、0（中）、1（右）
        """
        if self._behavior == self.BEHAVIOR_WANDER:
            if self._wander_mode_just_switched:
                self._wander_mode_just_switched = False  # 清除标志，下次允许手动
                return self.SERVO_CENTER  # 切换时调整到90度
            return self.SERVO_CENTER  # 游走模式固定中心（手动控制在app端）
        if self._behavior == self.BEHAVIOR_ATTACK:
            if self._target_offset < -0.2:
                return self.SERVO_LEFT
            if self._target_offset > 0.2:
                return self.SERVO_RIGHT
            return self.SERVO_CENTER
        return self.SERVO_CENTER

    def get_speed(self):
        """
        获取实际发送的速度值
        :return: 0-1.0
        """
        base_intensity = self._intensity
        if self._debug_mode:
            return min(1.0, base_intensity * 0.3)
        return base_intensity

    def get_status(self):
        """
        获取摇杆的完整状态
        
        :return: 状态字典
        """
        return {
            'x': self._x,
            'y': self._y,
            'intensity': self._intensity,
            'magnitude': self.calculate_magnitude(),
            'angle': self.get_angle_degrees(),
            'direction': self.get_direction(),
            'is_centered': self.is_centered(),
            'is_moving': self.is_moving(),
            'speed': self.get_speed(),
            'servo': self.get_servo_command(),
            'fire': self._fire_state,
            'behavior': self._behavior,
            'debug': 1 if self._debug_mode else 0,
            'target_offset': self._target_offset
        }

    def to_command_dict(self):
        """
        将当前摇杆状态转换为与APP命令对应的字典
        """
        return {
            'x': round(self._x, 2),
            'y': round(self._y, 2),
            'speed': int(self.get_speed() * 100),
            'servo': self.get_servo_command(),
            'fire': self._fire_state,
            'behavior': self._behavior,
            'debug': 1 if self._debug_mode else 0
        }

    def to_json(self):
        """
        将当前摇杆命令转换为JSON字符串，便于发送
        """
        return json.dumps(self.to_command_dict(), ensure_ascii=False)
    
    def __str__(self):
        """字符串表示"""
        status = self.get_status()
        msg = "VirtualJoystick [X:{:.2f} Y:{:.2f} ".format(status['x'], status['y'])
        msg += "Intensity:{:.2f} ".format(status['intensity'])
        msg += "Magnitude:{:.2f} ".format(status['magnitude'])
        msg += "Direction:{}]".format(status['direction'])
        return msg
    
    def __repr__(self):
        """详细表示"""
        status = self.get_status()
        msg = "VirtualJoystick(x={}, y={}, ".format(status['x'], status['y'])
        msg += "intensity={}, ".format(status['intensity'])
        msg += "magnitude={:.2f}, ".format(status['magnitude'])
        msg += "angle={:.1f} deg)".format(status['angle'])
        return msg


class JoystickDataBuffer:
    """
    摇杆数据缓冲区
    用于存储多个摇杆数据记录，便于数据分析和平滑处理
    """
    
    def __init__(self, buffer_size=10):
        """
        初始化数据缓冲区
        
        :param buffer_size: 缓冲区大小
        """
        self.buffer_size = buffer_size
        self.buffer = []
        self.index = 0
    
    def add_sample(self, joystick):
        """
        添加一个摇杆数据样本
        
        :param joystick: VirtualJoystick对象
        :return: None
        """
        if len(self.buffer) < self.buffer_size:
            self.buffer.append(joystick.get_status())
        else:
            self.buffer[self.index] = joystick.get_status()
            self.index = (self.index + 1) % self.buffer_size
    
    def get_average(self):
        """
        获取缓冲区中数据的平均值
        用于平滑摇杆输入
        
        :return: 平均状态字典
        """
        if not self.buffer:
            return {'x': 0.0, 'y': 0.0, 'intensity': 0.0}
        
        avg_x = sum(s['x'] for s in self.buffer) / len(self.buffer)
        avg_y = sum(s['y'] for s in self.buffer) / len(self.buffer)
        avg_intensity = sum(s['intensity'] for s in self.buffer) / len(self.buffer)
        
        return {
            'x': avg_x,
            'y': avg_y,
            'intensity': avg_intensity
        }
    
    def clear(self):
        """
        清空缓冲区
        
        :return: None
        """
        self.buffer = []
        self.index = 0
