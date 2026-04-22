import math

class VirtualJoystick:
    """
    虚拟摇杆类 - 与手机APP关联
    用于接收和处理手机APP的摇杆输入数据
    """
    
    def __init__(self, x=0.0, y=0.0, intensity=0.0):
        """
        初始化虚拟摇杆
        
        :param x: X轴值（-1.0到1.0，0为中间）
        :param y: Y轴值（-1.0到1.0，0为中间）
        :param intensity: 强度值（0到1.0）
        """
        self._x = 0.0  # X轴
        self._y = 0.0  # Y轴
        self._intensity = 0.0  # 强度
        self._dead_zone = 0.05  # 死区阈值（小于此值视为0）
        
        # 初始化值
        self.set_x(x)
        self.set_y(y)
        self.set_intensity(intensity)
    
    def set_x(self, x):
        """
        设置X轴值
        
        :param x: X轴值（-1.0到1.0，0为中间）
        :return: None
        """
        self._x = max(-1.0, min(1.0, x))
        # 应用死区处理
        if abs(self._x) < self._dead_zone:
            self._x = 0.0
    
    def get_x(self):
        """
        获取X轴值
        
        :return: X轴值（-1.0到1.0）
        """
        return self._x
    
    def set_y(self, y):
        """
        设置Y轴值
        
        :param y: Y轴值（-1.0到1.0，0为中间）
        :return: None
        """
        self._y = max(-1.0, min(1.0, y))
        # 应用死区处理
        if abs(self._y) < self._dead_zone:
            self._y = 0.0
    
    def get_y(self):
        """
        获取Y轴值
        
        :return: Y轴值（-1.0到1.0）
        """
        return self._y
    
    def set_intensity(self, intensity):
        """
        设置强度值
        
        :param intensity: 强度值（0到1.0）
        :return: None
        """
        self._intensity = max(0.0, min(1.0, intensity))
    
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
    
    def update_from_app(self, x, y, intensity):
        """
        从手机APP接收数据并更新摇杆状态
        
        :param x: X轴值（-1.0到1.0）
        :param y: Y轴值（-1.0到1.0）
        :param intensity: 强度值（0到1.0）
        :return: None
        """
        self.set_x(x)
        self.set_y(y)
        self.set_intensity(intensity)
    
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
            'is_moving': self.is_moving()
        }
    
    def __str__(self):
        """字符串表示"""
        status = self.get_status()
        return (f"虚拟摇杆 [X:{status['x']:>6.2f} Y:{status['y']:>6.2f} "
                f"强度:{status['intensity']:.2f} "
                f"幅度:{status['magnitude']:.2f} "
                f"方向:{status['direction']}]")
    
    def __repr__(self):
        """详细表示"""
        status = self.get_status()
        return (f"VirtualJoystick(x={status['x']}, y={status['y']}, "
                f"intensity={status['intensity']}, "
                f"magnitude={status['magnitude']:.2f}, "
                f"angle={status['angle']:.1f}°)")


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
