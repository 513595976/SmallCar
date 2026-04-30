from machine import Pin, PWM


class MotorController:
    """
    电机控制类 (ESP32适配版)
    输入：强度控制参数(0-1.0，来自APP摇杆)、正反转使能、校对参数（偏移补偿）
    输出：PWM单点、两个方向bool控制
    
    PWM计算公式：
    PWM = 强度 + 校对参数
    强度范围：0 ~ 1.0（摇杆强度值）
    校对参数范围：-1.0 ~ 1.0（偏移补偿值）
    最终PWM限制在0 ~ 1.0范围内
    """
    
    def __init__(self, pwm_pin_num=4, forward_pin_num=5, backward_pin_num=6, calibration=0.0, freq=1000):
        """
        初始化电机控制器 (ESP32硬件接口)
        
        :param pwm_pin_num: PWM输出引脚编号 (默认 4)
        :param forward_pin_num: 正转控制引脚编号 (默认 5)
        :param backward_pin_num: 反转控制引脚编号 (默认 6)
        :param calibration: 校对参数（偏移补偿值，默认0.0，范围-1.0~1.0）
        :param freq: PWM频率 (默认 1000Hz)
        
        强度值来源：APP虚拟摇杆的强度输出（0-1.0）
        """
        self.calibration = calibration
        self.freq = freq
        
        # 初始化 ESP32 硬件引脚
        try:
            # 初始化 PWM 引脚
            self.pwm_pin = PWM(Pin(pwm_pin_num))
            self.pwm_pin.freq(self.freq)
            self.pwm_pin.duty(0)  # 初始占空比为0
            
            # 初始化方向控制引脚
            self.forward_pin = Pin(forward_pin_num, Pin.OUT)
            self.backward_pin = Pin(backward_pin_num, Pin.OUT)
            
            # 初始状态设为低电平
            self.forward_pin.value(0)
            self.backward_pin.value(0)
            
        except Exception as e:
            print(f"硬件初始化错误: {e}")
            self.pwm_pin = None
            self.forward_pin = None
            self.backward_pin = None
        
        # 内部状态
        self._intensity = 0.0  # 0-1.0的强度值（来自APP摇杆）
        self._forward_enabled = False  # 正转使能
        self._backward_enabled = False  # 反转使能
        self._pwm_value = 0.0  # 当前PWM输出值 (0-1.0逻辑值)
    
    def control(self, intensity, forward=True, backward=False):
        """
        控制电机运行
        
        :param intensity: 强度值 (0-1.0)
        :param forward: 是否正转
        :param backward: 是否反转
        :return: None
        """
        if self.pwm_pin is None or self.forward_pin is None or self.backward_pin is None:
            return
        
        # 限制强度范围
        intensity = max(0.0, min(1.0, intensity))
        
        # 更新内部状态
        self._intensity = intensity
        self._forward_enabled = forward
        self._backward_enabled = backward
        
        # 计算实际PWM值（应用校对参数）
        raw_pwm = intensity + self.calibration
        self._pwm_value = max(0.0, min(1.0, raw_pwm))
        
        # 设置方向引脚
        self.forward_pin.value(1 if forward else 0)
        self.backward_pin.value(1 if backward else 0)
        
        # 设置PWM输出
        self._set_pwm_output(self._pwm_value)
    
    def stop(self):
        """
        停止电机
        
        :return: None
        """
        if self.pwm_pin is not None:
            self.pwm_pin.duty(0)
        if self.forward_pin is not None:
            self.forward_pin.value(0)
        if self.backward_pin is not None:
            self.backward_pin.value(0)
        
        self._intensity = 0.0
        self._forward_enabled = False
        self._backward_enabled = False
        self._pwm_value = 0.0
    
    def _set_pwm_output(self, value):
        """
        设置PWM输出值（ESP32硬件接口）
        
        :param value: PWM值0-1.0（对应0-100%占空比）
        :return: None
        """
        if self.pwm_pin is not None:
            try:
                # ESP32 MicroPython PWM duty 范围通常是 0-1023 (10位分辨率)
                # 将 0-1.0 转换为 0-1023
                duty_value = int(value * 1023)
                self.pwm_pin.duty(duty_value)
            except Exception as e:
                print(f"PWM输出错误: {e}")

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
    
    def get_status(self):
        """
        获取当前状态字典
        :return: 状态字典
        """
        return {
            'intensity': self._intensity,
            'calibration': self.calibration,
            'pwm_value': self._pwm_value,
            'forward_enabled': self._forward_enabled,
            'backward_enabled': self._backward_enabled
        }
    
    
    def __str__(self):
        return str(self.get_status())
