import math

class TrackCarController:
    """
    履带小车控制类 (差速转向版)
    
    设计说明：
    - 双电机控制，每条履带一个电机（左电机、右电机）
    - 车头始终朝向运动方向（前进或后退）
    - 采用差速转向原理实现复杂运动
    - 支持原地掉头、斜向运动等
    
    坐标系定义：
    - X轴（-1.0 ~ 1.0）：向右为正，向左为负
    - Y轴（-1.0 ~ 1.0）：向前为正，向后为负
    
    运动模式：
    1. 前进方向（Y >= 0）：
       - 正上 (X=0, Y>0)：直线前进，左右电机同速
       - 右上 (X>0, Y>0)：斜向右上，左电机快，右电机慢
       - 左上 (X<0, Y>0)：斜向左上，右电机快，左电机慢
    
    2. 后退方向（Y < 0）：
       - 先执行原地调头180度（履带反转仅在调头时出现）
       - 调头完成后，车头朝后，再进行差速运动
       - 正下 (X≈0, Y<0)：直线后退
       - 右下 (X>0, Y<0)：斜向右下，先向右调头，再差速后退
       - 左下 (X<0, Y<0)：斜向左下，先向左调头，再差速后退
    
    差速转向公式：
    - 基础速度 = |Y| （前后速度幅度）
    - 转向修正 = X × turning_ratio （左右差速）
    - 左电机速度 = 基础速度 - 转向修正
    - 右电机速度 = 基础速度 + 转向修正
    
    例如（前进方向）：
    - (X=0, Y=0.8)：直线前进，左电机=0.8，右电机=0.8
    - (X=0.5, Y=0.8)：右上方向，左电机=1.0，右电机=0.6（归一化后）
    - (X=-0.5, Y=0.8)：左上方向，左电机=0.6，右电机=1.0（归一化后）
    - (X=1.0, Y=0)：原地右转，左电机=1.0，右电机=-1.0
    
    调头逻辑：
    - 从前进切换到后退时，自动执行180度原地旋转
    - 根据目标方向的X值决定旋转方向（左下向左转，右下向右转）
    - 调头过程中履带会出现反转现象
    """
    
    def __init__(self, left_motor=None, right_motor=None):
        """
        初始化履带小车
        
        :param left_motor: 左电机对象（MotorController实例）
        :param right_motor: 右电机对象（MotorController实例）
        """
        self.left_motor = left_motor
        self.right_motor = right_motor
        
        # 小车状态
        self._mode = "stop"  # stop, forward, backward, turn_left, turn_right, rotate
        self._direction_x = 0.0  # X轴方向 (-1.0 ~ 1.0)
        self._direction_y = 0.0  # Y轴方向 (-1.0 ~ 1.0)
        self._speed = 0.0  # 总体速度 (0 ~ 1.0)
        
        # 控制参数
        self._turning_speed_ratio = 1.0  # 转向系数（0~1.0），用于调节转向灵敏度
        self._rotate_speed_ratio = 0.0   # 原地旋转时的速度比例
        self._forward_heading = True  # True表示当前朝向是前进方向
        self._heading_change_counter = 0  # 掉头计数器
        
    def update_from_joystick(self, joystick):
        """
        从虚拟摇杆接收数据并更新小车运动
        
        将摇杆的XY轴输入映射到左右电机的差速控制：
        - 摇杆X轴 → 左右电机差速（转向）
        - 摇杆Y轴 → 左右电机平均速度（前后）
        
        差速计算：
        - 左电机 = |Y| - X
        - 右电机 = |Y| + X
        
        :param joystick: VirtualJoystick对象
        :return: None
        """
        self._direction_x = joystick.get_x()
        self._direction_y = joystick.get_y()
        self._speed = joystick.calculate_magnitude()
        
        self.calculate_motor_control()
    
    def apply_app_data(self, x_axis, y_axis, intensity):
        """
        应用APP摇杆的XY轴和强度值到小车控制
        
        参数说明：
        - x_axis: X轴值 (-1.0 ~ 1.0)，正值向右转，负值向左转
        - y_axis: Y轴值 (-1.0 ~ 1.0)，正值向前，负值向后
        - intensity: 强度值 (0 ~ 1.0)，用于调节电机输出强度
        
        工作原理：
        1. 根据Y轴判断前后方向
        2. 根据X轴计算转向
        3. 根据intensity调节整体速度
        4. 通过差速公式计算左右电机速度
        
        :param x_axis: X轴方向 (-1.0 ~ 1.0)
        :param y_axis: Y轴方向 (-1.0 ~ 1.0)
        :param intensity: 强度值 (0 ~ 1.0)
        :return: None
        
        示例：
        track_car.apply_app_data(x_axis=0.5, y_axis=0.8, intensity=0.9)
        """
        # 将X、Y、强度值组合
        self._direction_x = max(-1.0, min(1.0, x_axis))
        self._direction_y = max(-1.0, min(1.0, y_axis))
        
        # 使用强度值来调节最终的速度幅度
        self._speed = max(abs(self._direction_x), abs(self._direction_y)) * intensity
        
        self.calculate_motor_control()
    
    def calculate_motor_control(self):
        """
        根据摇杆XY值计算左右电机的差速输出
        
        差速转向原理：
        - 车头始终朝向运动方向（前进或后退）
        - 右上/左上：车头朝前，通过左右履带差速实现斜向前进
        - 右下/左下：先原地调头180度，车头朝后，再通过差速实现斜向后退
        - 履带反转仅在调头时出现
        
        差速公式：
        - 基础速度 = |Y| （前后速度）
        - 转向修正 = X × turning_ratio （左右差速）
        - 左电机 = 基础速度 - 转向修正
        - 右电机 = 基础速度 + 转向修正
        
        :return: None
        """
        if self._speed < 0.05:  # 停止
            self._set_motor_output(0, 0, "stop")
            self._mode = "stop"
            return
        
        # 提取摇杆的X和Y分量
        x = self._direction_x  # X轴：向右为正，向左为负（-1.0 ~ 1.0）
        y = self._direction_y  # Y轴：向前为正，向后为负（-1.0 ~ 1.0）
        
        # 判断前进或后退方向
        if y >= 0:
            # 向前运动（包括右上、正上、左上）
            forward = True
            
            # 如果当前朝向是后退方向，需要先原地掉头
            if not self._forward_heading:
                self._perform_heading_change()
                return
            
            self._forward_heading = True
        else:
            # 向后运动（包括右下、正下、左下）
            forward = False
            
            # 如果当前朝向是前进方向，需要先原地掉头
            if self._forward_heading:
                self._perform_heading_change()
                return
            
            self._forward_heading = False
        
        # 使用差速转向公式计算电机速度
        # 基础速度 = Y轴的绝对值（前后速度）
        base_speed = abs(y)
        
        # 转向修正 = X轴 × 转向系数（左右差速）
        turn_correction = x * self._turning_speed_ratio
        
        # 差速公式：
        # 左电机 = 基础速度 - 转向修正
        # 右电机 = 基础速度 + 转向修正
        left_speed = base_speed - turn_correction
        right_speed = base_speed + turn_correction
        
        # 限制在-1.0~1.0范围内
        # 使用归一化处理，保持扭矩输出平衡
        max_speed = max(abs(left_speed), abs(right_speed))
        if max_speed > 1.0:
            left_speed = left_speed / max_speed
            right_speed = right_speed / max_speed
        
        # 确定运动模式
        if abs(x) < 0.1:
            mode = "forward" if forward else "backward"
        elif x > 0:
            mode = "turn_right" if forward else "turn_right_backward"
        else:
            mode = "turn_left" if forward else "turn_left_backward"
        
        self._set_motor_output(left_speed, right_speed, mode)
    
    def _perform_heading_change(self):
        """
        执行原地掉头动作
        让小车停止并进行180度旋转
        
        调头逻辑：
        - 如果目标方向是右下（x>0, y<0），则向右旋转180度
        - 如果目标方向是左下（x<0, y<0），则向左旋转180度
        - 如果目标方向是正下（x≈0, y<0），则默认向右旋转
        
        注意：当前实现基于计数器（50次调用），假设控制频率约20Hz，
        实际旋转时间约2.5秒。如需更精确控制，建议改为时间戳方式。
        
        :return: None
        """
        self._heading_change_counter += 1
        
        # 获取目标方向的X轴值，决定调头方向
        target_x = self._direction_x
        
        # 原地旋转：根据目标方向决定旋转方向
        if target_x >= 0:
            # 目标方向偏右或正中，向右旋转
            # 左电机正向，右电机反向
            rotation_speed = 0.7
            left_motor = rotation_speed
            right_motor = -rotation_speed
        else:
            # 目标方向偏左，向左旋转
            # 左电机反向，右电机正向
            rotation_speed = 0.7
            left_motor = -rotation_speed
            right_motor = rotation_speed
        
        # 调整旋转时间（可根据实际小车调整）
        # 当前假设控制频率为20Hz，50次 ≈ 2.5秒
        # 如需更精确，可记录开始时间并计算 elapsed_time
        if self._heading_change_counter < 50:
            # 正在旋转
            mode = "rotate_right" if target_x >= 0 else "rotate_left"
            self._set_motor_output(left_motor, right_motor, mode)
        else:
            # 旋转完成
            self._heading_change_counter = 0
            # 切换朝向标志
            self._forward_heading = not self._forward_heading
            self.calculate_motor_control()  # 重新计算，应用新的朝向
    
    def _set_motor_output(self, left_speed, right_speed, mode):
        """
        设置左右电机的输出
        
        :param left_speed: 左电机速度 (-1.0 ~ 1.0)
        :param right_speed: 右电机速度 (-1.0 ~ 1.0)
        :param mode: 运动模式
        :return: None
        """
        self._mode = mode
        
        if self.left_motor is not None:
            if left_speed > 0:
                self.left_motor.control(abs(left_speed), True, False)
            elif left_speed < 0:
                self.left_motor.control(abs(left_speed), False, True)
            else:
                self.left_motor.stop()
        
        if self.right_motor is not None:
            if right_speed > 0:
                self.right_motor.control(abs(right_speed), True, False)
            elif right_speed < 0:
                self.right_motor.control(abs(right_speed), False, True)
            else:
                self.right_motor.stop()
    
    def direct_control(self, x, y, turn_ratio=None):
        """
        直接通过XY轴控制小车运动（差速转向）
        
        控制原理：
        - X轴（-1.0 ~ 1.0）：控制转向，正值向右转，负值向左转
        - Y轴（-1.0 ~ 1.0）：控制前后，正值前进，负值后退
        
        差速公式：
        - 左电机速度 = |Y| - X × turn_ratio
        - 右电机速度 = |Y| + X × turn_ratio
        
        示例：
        - X=0, Y=0.8：直线前进
        - X=0.5, Y=0.8：向右转大圈前进
        - X=-0.5, Y=0.8：向左转大圈前进
        - X=1.0, Y=0：原地向右转
        
        :param x: X轴值（-1.0 ~ 1.0），正值向右，负值向左
        :param y: Y轴值（-1.0 ~ 1.0），正值向前，负值向后
        :param turn_ratio: 可选的转向系数 (0~1.0)，越大转弯越急
        :return: None
        """
        if turn_ratio is not None:
            self._turning_speed_ratio = max(0.0, min(1.0, turn_ratio))
        
        self._direction_x = max(-1.0, min(1.0, x))
        self._direction_y = max(-1.0, min(1.0, y))
        self._speed = math.sqrt(x**2 + y**2)
        
        self.calculate_motor_control()
    
    def move_forward(self, speed):
        """
        直线前进
        
        :param speed: 速度 (0 ~ 1.0)
        :return: None
        """
        self.direct_control(0, speed)
    
    def move_backward(self, speed):
        """
        直线后退
        
        :param speed: 速度 (0 ~ 1.0)
        :return: None
        """
        self.direct_control(0, -speed)
    
    def turn_left(self, speed, radius=1.0):
        """
        向左转弯
        
        :param speed: 前进速度 (0 ~ 1.0)
        :param radius: 转弯半径 (0 ~ 1.0)
                      0 = 原地旋转（最急转弯）
                      1.0 = 大半径转弯（最缓转弯）
        :return: None
        """
        self.direct_control(x=-speed * radius, y=speed, turn_ratio=1.0)
    
    def turn_right(self, speed, radius=1.0):
        """
        向右转弯
        
        :param speed: 前进速度 (0 ~ 1.0)
        :param radius: 转弯半径 (0 ~ 1.0)
                      0 = 原地旋转（最急转弯）
                      1.0 = 大半径转弯（最缓转弯）
        :return: None
        """
        self.direct_control(x=speed * radius, y=speed, turn_ratio=1.0)
    
    def rotate_in_place(self, speed, direction="left"):
        """
        原地旋转（360度旋转）
        
        :param speed: 旋转速度 (0 ~ 1.0)
        :param direction: 旋转方向 "left" 或 "right"
        :return: None
        """
        if direction == "left":
            self._set_motor_output(-speed, speed, "rotate_left")
        else:
            self._set_motor_output(speed, -speed, "rotate_right")
    
    def stop(self):
        """
        停止小车
        
        :return: None
        """
        self._set_motor_output(0, 0, "stop")
        self._direction_x = 0
        self._direction_y = 0
        self._speed = 0
    
    def get_mode(self):
        """
        获取当前运动模式
        
        :return: 运动模式字符串
        """
        return self._mode
    
    def get_heading(self):
        """
        获取当前车头朝向
        
        :return: "forward" 表示朝向前进方向，"backward" 表示朝向后退方向
        """
        return "forward" if self._forward_heading else "backward"
    
    def get_status(self):
        """
        获取小车的完整状态
        
        :return: 状态字典
        """
        left_status = self.left_motor.get_status() if self.left_motor else None
        right_status = self.right_motor.get_status() if self.right_motor else None
        
        return {
            'direction_x': self._direction_x,
            'direction_y': self._direction_y,
            'speed': self._speed,
            'mode': self._mode,
            'heading': self.get_heading(),
            'left_motor': left_status,
            'right_motor': right_status,
            'turning_ratio': self._turning_speed_ratio
        }
    
    def __str__(self):
        """字符串表示"""
        msg = "TrackCar [Mode:{} Heading:{} ".format(self._mode, self.get_heading())
        msg += "X:{:.2f} Y:{:.2f} ".format(self._direction_x, self._direction_y)
        msg += "Speed:{:.2f}]".format(self._speed)
        return msg


class TrackCarSimulator:
    """
    履带小车模拟器
    用于测试和调试小车控制逻辑（无需实际硬件）
    """
    
    def __init__(self):
        """初始化模拟器"""
        self.left_motor_speed = 0.0
        self.right_motor_speed = 0.0
        self.car_x = 0.0  # 小车X位置
        self.car_y = 0.0  # 小车Y位置
        self.car_angle = 0.0  # 小车方向角度
        self.history = []
    
    def simulate_motor(self, left_speed, right_speed, dt=0.1):
        """
        模拟电机运动对小车位置的影响
        
        :param left_speed: 左电机速度 (-1.0 ~ 1.0)
        :param right_speed: 右电机速度 (-1.0 ~ 1.0)
        :param dt: 时间步长
        :return: None
        """
        self.left_motor_speed = left_speed
        self.right_motor_speed = right_speed
        
        # 计算小车的前进方向和旋转
        avg_speed = (left_speed + right_speed) / 2.0
        speed_diff = right_speed - left_speed
        
        # 更新位置（简化模型）
        move_distance = avg_speed * dt
        self.car_x += move_distance * math.cos(self.car_angle)
        self.car_y += move_distance * math.sin(self.car_angle)
        
        # 更新角度（差速转向）
        self.car_angle += speed_diff * dt * 0.5
        
        # 记录历史
        self.history.append({
            'x': self.car_x,
            'y': self.car_y,
            'angle': self.car_angle,
            'left_speed': left_speed,
            'right_speed': right_speed
        })
    
    def get_position(self):
        """
        获取小车位置
        
        :return: (x, y, angle) 元组
        """
        return (self.car_x, self.car_y, self.car_angle)
    
    def reset(self):
        """重置模拟器"""
        self.car_x = 0.0
        self.car_y = 0.0
        self.car_angle = 0.0
        self.history = []
    
    def get_trajectory(self):
        """
        获取小车运动轨迹
        
        :return: 轨迹点列表
        """
        return [(h['x'], h['y']) for h in self.history]
