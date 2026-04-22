class MotorController:
    """
    电机控制类
    输入：强度控制参数(0-1.0，来自APP摇杆)、正反转使能、校对参数（偏移补偿）
    输出：PWM单点、两个方向bool控制
    
    PWM计算公式：
    PWM = 强度 + 校对参数
    强度范围：0 ~ 1.0（摇杆强度值）
    校对参数范围：-1.0 ~ 1.0（偏移补偿值）
    最终PWM限制在0 ~ 1.0范围内
    """
    
    def __init__(self, pwm_pin=None, forward_pin=None, backward_pin=None, calibration=0.0):
        """
        初始化电机控制器
        
        :param pwm_pin: PWM输出引脚对象
        :param forward_pin: 正转控制引脚对象
        :param backward_pin: 反转控制引脚对象
        :param calibration: 校对参数（偏移补偿值，默认0.0，范围-1.0~1.0）
        
        强度值来源：APP虚拟摇杆的强度输出（0-1.0）
        """
        self.pwm_pin = pwm_pin
        self.forward_pin = forward_pin
        self.backward_pin = backward_pin
        self.calibration = calibration
        
        # 内部状态
        self._intensity = 0.0  # 0-1.0的强度值（来自APP摇杆）
        self._forward_enabled = False  # 正转使能
        self._backward_enabled = False  # 反转使能
        self._pwm_value = 0.0  # 当前PWM输出值
        
    def set_intensity(self, intensity):
        """
        设置强度值（来自APP摇杆）
        
        :param intensity: 强度值0-1.0
        :return: None
        """
        self._intensity = max(0.0, min(1.0, intensity))
        self.update_output()
    
    def get_intensity(self):
        """
        获取当前强度值
        
        :return: 当前强度值(0-1.0)
        """
        return self._intensity
    
    def set_calibration(self, calibration):
        """
        设置校对参数（偏移补偿值）
        
        :param calibration: 校对偏移值（-1.0~1.0），会直接加到频率值上
        :return: None
        """
        self.calibration = calibration
        self.update_output()
    
    def get_calibration(self):
        """
        获取校对参数
        
        :return: 当前校对系数
        """
        return self.calibration
    
    def enable_forward(self):
        """
        使能正转
        禁用反转，启动正转输出
        
        :return: None
        """
        self._forward_enabled = True
        self._backward_enabled = False
        self.update_output()
    
    def enable_backward(self):
        """
        使能反转
        禁用正转，启动反转输出
        
        :return: None
        """
        self._backward_enabled = True
        self._forward_enabled = False
        self.update_output()
    
    def stop(self):
        """
        停止电机
        禁用正转和反转，PWM输出为0
        
        :return: None
        """
        self._forward_enabled = False
        self._backward_enabled = False
        self.update_output()
    
    def get_direction_status(self):
        """
        获取当前方向状态
        
        :return: 元组(forward_bool, backward_bool)
        """
        return (self._forward_enabled, self._backward_enabled)
    
    def update_output(self):
        """
        更新PWM和方向输出
        基于强度、校对参数和方向使能计算输出
        
        :return: None
        """
        # 如果电机停止，PWM设为0
        if not self._forward_enabled and not self._backward_enabled:
            self._pwm_value = 0.0
        else:
            # 计算实际PWM值：强度 + 校对参数（偏移补偿）
            self._pwm_value = self._intensity + self.calibration
            # 限制在0-1.0范围内
            self._pwm_value = max(0.0, min(1.0, self._pwm_value))
        
        # 设置PWM输出
        self._set_pwm_output(self._pwm_value)
        
        # 设置方向输出（两个bool控制）
        self._set_direction_output(self._forward_enabled, self._backward_enabled)
    
    def _set_pwm_output(self, value):
        """
        设置PWM输出值（硬件接口）
        
        :param value: PWM值0-1.0（对应0-100%占空比）
        :return: None
        """
        if self.pwm_pin is not None:
            # 将0-1.0的值转换为硬件支持的范围
            # 例如对于PWM频率，可能需要转换为0-255或0-65535
            pwm_hardware_value = int(value * 255)  # 假设8位PWM
            try:
                # 实际硬件调用
                self.pwm_pin.duty(pwm_hardware_value)
            except Exception as e:
                print(f"PWM输出错误: {e}")
    
    def _set_direction_output(self, forward, backward):
        """
        设置方向输出（两个bool值）
        
        :param forward: 正转控制bool
        :param backward: 反转控制bool
        :return: None
        """
        if self.forward_pin is not None and self.backward_pin is not None:
            try:
                # 设置正转控制引脚
                self.forward_pin.value(1 if forward else 0)
                # 设置反转控制引脚
                self.backward_pin.value(1 if backward else 0)
            except Exception as e:
                print(f"方向输出错误: {e}")
    
    def control(self, intensity, forward_enabled, backward_enabled, calibration=None):
        """
        综合控制函数
        一次性设置所有参数并输出
        
        :param intensity: 强度参数(0-1.0，来自APP摇杆)
        :param forward_enabled: 正转使能bool
        :param backward_enabled: 反转使能bool
        :param calibration: 可选的校对参数
        :return: None
        """
        if calibration is not None:
            self.set_calibration(calibration)
        
        self._intensity = max(0.0, min(1.0, intensity))
        self._forward_enabled = forward_enabled
        self._backward_enabled = backward_enabled
        
        self.update_output()
    
    def control_from_app(self, intensity, direction_forward=True, calibration=None):
        """
        从APP数据直接控制电机
        根据APP摇杆的强度值和方向控制电机
        
        :param intensity: 强度值(0-1.0)，来自APP摇杆幅度
        :param direction_forward: 方向bool，True为正转，False为反转
        :param calibration: 可选的校对参数
        :return: None
        
        示例：
        motor.control_from_app(intensity=0.8, direction_forward=True)
        """
        if calibration is not None:
            self.set_calibration(calibration)
        
        self.control(
            intensity=intensity,
            forward_enabled=direction_forward,
            backward_enabled=not direction_forward,
            calibration=None
        )
    
    def apply_joystick_data(self, x_axis, y_axis, intensity):
        """
        应用APP虚拟摇杆数据到电机
        将APP摇杆的XY轴和强度值转换为电机控制
        
        原理：
        - Y轴：正值前进，负值后退 → 方向
        - 强度：0-1.0 → 电机强度
        - X轴：用于转向判断（在差速小车中使用）
        
        :param x_axis: X轴值 (-1.0 ~ 1.0)
        :param y_axis: Y轴值 (-1.0 ~ 1.0)
        :param intensity: 强度值 (0 ~ 1.0)
        :return: None
        
        示例用法：
        motor.apply_joystick_data(x_axis=0.0, y_axis=0.8, intensity=0.75)
        """
        # 判断前后方向：Y轴正值为前进
        direction_forward = y_axis >= 0
        
        # 使用强度值和校对参数计算最终PWM
        self.control(
            intensity=intensity,
            forward_enabled=direction_forward,
            backward_enabled=not direction_forward,
            calibration=None
        )
    
    def get_motor_output(self):
        """
        获取电机的完整输出信息
        包含PWM值、方向状态等
        
        :return: 字典，包含输出信息
        
        示例：
        output = motor.get_motor_output()
        # output = {
        #     'pwm': 0.8,
        #     'direction': 'forward',  # 'forward', 'backward', 'stop'
        #     'intensity': 0.8,
        #     'calibration': 0.0
        # }
        """
        status = self.get_status()
        
        if not status['forward_enabled'] and not status['backward_enabled']:
            direction = 'stop'
        elif status['forward_enabled']:
            direction = 'forward'
        else:
            direction = 'backward'
        
        return {
            'pwm': status['pwm_value'],
            'direction': direction,
            'intensity': status['intensity'],
            'calibration': status['calibration']
        }
    
    
    def __str__(self):
        """字符串表示"""
        status = self.get_status()
        direction = "停止"
        if status['forward_enabled']:
            direction = "正转"
        elif status['backward_enabled']:
            direction = "反转"
        
        return (f"电机控制器 [方向: {direction}, "
                f"强度: {status['intensity']:.2f}, "
                f"PWM: {status['pwm_value']:.2f}, "
                f"校对: {status['calibration']:.2f}]")
