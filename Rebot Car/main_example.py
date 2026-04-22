from motor_controller import MotorController
from virtual_joystick import VirtualJoystick, JoystickDataBuffer
from track_car_controller import TrackCarController, TrackCarSimulator

# 创建电机控制器实例
# 参数：PWM引脚、正转引脚、反转引脚、校对参数（偏移补偿值）
motor = MotorController(
    pwm_pin=None,  # 实际使用时替换为真实的PWM引脚
    forward_pin=None,  # 实际使用时替换为真实的正转引脚
    backward_pin=None,  # 实际使用时替换为真实的反转引脚
    calibration=0.0  # 校对参数：偏移补偿值（-1.0~1.0）
)

# 创建左右电机（用于履带小车）
left_motor = MotorController(
    pwm_pin=None,
    forward_pin=None,
    backward_pin=None,
    calibration=0.0
)

right_motor = MotorController(
    pwm_pin=None,
    forward_pin=None,
    backward_pin=None,
    calibration=0.0
)

# 创建履带小车控制器
track_car = TrackCarController(left_motor=left_motor, right_motor=right_motor)

# 创建虚拟摇杆实例
joystick = VirtualJoystick()
joystick_buffer = JoystickDataBuffer(buffer_size=5)

# 创建模拟器（用于测试）
simulator = TrackCarSimulator()

def main():
    print("Welcome to RT-Thread MicroPython!")
    print("电机控制 + 虚拟摇杆系统启动...\n")
    
    # 电机控制示例
    print("=" * 50)
    print("电机控制示例")
    print("=" * 50)
    
    # 示例1：正转，强度50%
    print("示例1：正转，强度50%")
    motor.set_intensity(0.5)
    motor.enable_forward()
    print(motor)
    print()
    
    # 示例2：反转，强度70%
    print("示例2：反转，强度70%")
    motor.set_intensity(0.7)
    motor.enable_backward()
    print(motor)
    print()
    
    # 示例3：使用校对参数
    print("示例3：使用偏移补偿校对参数")
    motor.set_calibration(0.2)  # +20%的偏移补偿
    motor.set_intensity(0.6)
    motor.enable_forward()
    print(motor)
    print()
    
    # 示例4：综合控制
    print("示例4：综合控制函数")
    motor.control(intensity=0.8, forward_enabled=True, backward_enabled=False, calibration=0.1)
    print(motor)
    print()
    
    # 示例5：停止电机
    print("示例5：停止电机")
    motor.stop()
    print(motor)
    print()
    
    # 获取电机状态
    print("电机状态：")
    status = motor.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # APP控制示例
    print("\n" + "=" * 50)
    print("APP摇杆数据转换电机控制示例")
    print("=" * 50)
    print()
    
    # 示例1：直接从APP强度值控制
    print("示例1：从APP摇杆强度值控制电机")
    print("-" * 50)
    app_intensity = 0.75
    motor.control_from_app(intensity=app_intensity, direction_forward=True)
    print(f"APP强度值: {app_intensity}")
    print(f"{motor}")
    output = motor.get_motor_output()
    print(f"电机输出: {output}")
    print()
    
    # 示例2：应用APP摇杆的XY轴和强度值
    print("示例2：应用APP摇杆XY轴数据")
    print("-" * 50)
    app_x = 0.0
    app_y = 0.8
    app_intensity = 0.8
    motor.apply_joystick_data(x_axis=app_x, y_axis=app_y, intensity=app_intensity)
    print(f"APP摇杆: X={app_x}, Y={app_y}, 强度={app_intensity}")
    print(f"{motor}")
    print(f"说明: Y轴正值({app_y})表示前进，电机正转")
    print()
    
    # 示例3：APP摇杆后退
    print("示例3：APP摇杆后退")
    print("-" * 50)
    app_x = 0.0
    app_y = -0.6
    app_intensity = 0.6
    motor.apply_joystick_data(x_axis=app_x, y_axis=app_y, intensity=app_intensity)
    print(f"APP摇杆: X={app_x}, Y={app_y}, 强度={app_intensity}")
    print(f"{motor}")
    print(f"说明: Y轴负值({app_y})表示后退，电机反转")
    print()
    
    # 示例4：APP摇杆停止
    print("示例4：APP摇杆停止")
    print("-" * 50)
    motor.apply_joystick_data(x_axis=0.0, y_axis=0.0, intensity=0.0)
    print(f"APP摇杆: X=0.0, Y=0.0, 强度=0.0")
    print(f"{motor}")
    print()
    
    # 示例5：多个APP数据帧的连续控制
    print("示例5：APP摇杆连续输入模拟")
    print("-" * 50)
    app_data_sequence = [
        {'x': 0.0, 'y': 0.8, 'intensity': 0.8, 'desc': '前进'},
        {'x': 0.0, 'y': 0.5, 'intensity': 0.5, 'desc': '减速前进'},
        {'x': 0.0, 'y': 0.0, 'intensity': 0.0, 'desc': '停止'},
        {'x': 0.0, 'y': -0.8, 'intensity': 0.8, 'desc': '后退'},
        {'x': 0.0, 'y': 0.0, 'intensity': 0.0, 'desc': '停止'},
    ]
    
    for i, frame in enumerate(app_data_sequence):
        motor.apply_joystick_data(
            x_axis=frame['x'],
            y_axis=frame['y'],
            intensity=frame['intensity']
        )
        output = motor.get_motor_output()
        print(f"  帧{i+1}: {frame['desc']:10} → {output['direction']:10} PWM:{output['pwm']:.2f}")
    
    # 履带小车控制示例
    print("\n" + "=" * 50)
    print("履带小车差速转向控制示例")
    print("=" * 50)
    print("差速转向公式：")
    print("  左电机 = |Y| - X × 转向系数")
    print("  右电机 = |Y| + X × 转向系数")
    print("小车设置：车头向X正方向\n")
    
    # 示例1：直线前进
    print("示例1：直线前进 (X=0, Y=0.8)")
    print("-" * 50)
    track_car.direct_control(x=0.0, y=0.8)
    print(f"摇杆输入: X=0.0, Y=0.8")
    print(f"{track_car}")
    left_status = left_motor.get_status()
    right_status = right_motor.get_status()
    print(f"  左电机: {left_status['pwm_value']:.2f} 正转")
    print(f"  右电机: {right_status['pwm_value']:.2f} 正转")
    print(f"  说明: 两电机等速，直线前进")
    print()
    
    # 示例2：向右前方转大圈
    print("示例2：向右前方转大圈 (X=0.5, Y=0.8)")
    print("-" * 50)
    track_car.direct_control(x=0.5, y=0.8, turn_ratio=1.0)
    print(f"摇杆输入: X=0.5, Y=0.8")
    print(f"{track_car}")
    left_status = left_motor.get_status()
    right_status = right_motor.get_status()
    print(f"  左电机: {left_status['pwm_value']:.2f} 正转")
    print(f"  右电机: {right_status['pwm_value']:.2f} 正转")
    print(f"  计算: 左=0.8-0.5=0.3, 右=0.8+0.5=1.3→归一化后→左=0.23, 右=1.0")
    print(f"  说明: 左电机速度快，右电机速度慢，向右转弯")
    print()
    
    # 示例3：向左前方转大圈
    print("示例3：向左前方转大圈 (X=-0.5, Y=0.8)")
    print("-" * 50)
    track_car.direct_control(x=-0.5, y=0.8, turn_ratio=1.0)
    print(f"摇杆输入: X=-0.5, Y=0.8")
    print(f"{track_car}")
    left_status = left_motor.get_status()
    right_status = right_motor.get_status()
    print(f"  左电机: {left_status['pwm_value']:.2f} 正转")
    print(f"  右电机: {right_status['pwm_value']:.2f} 正转")
    print(f"  计算: 左=0.8-(-0.5)=1.3, 右=0.8+(-0.5)=0.3→归一化后→左=1.0, 右=0.23")
    print(f"  说明: 右电机速度快，左电机速度慢，向左转弯")
    print()
    
    # 示例4：急转弯（调整转向系数）
    print("示例4：急转弯 (X=0.6, Y=0.8, turn_ratio=1.5)")
    print("-" * 50)
    track_car.direct_control(x=0.6, y=0.8, turn_ratio=1.5)
    print(f"摇杆输入: X=0.6, Y=0.8, 转向系数=1.5")
    print(f"{track_car}")
    left_status = left_motor.get_status()
    right_status = right_motor.get_status()
    print(f"  左电机: {left_status['pwm_value']:.2f}")
    print(f"  右电机: {right_status['pwm_value']:.2f}")
    print(f"  计算: 左=0.8-0.6×1.5=0.2, 右=0.8+0.6×1.5=1.7→归一化")
    print(f"  说明: 转向系数越大，转弯越急")
    print()
    
    # 示例5：原地旋转
    print("示例5：原地旋转 (X=1.0, Y=0)")
    print("-" * 50)
    track_car.rotate_in_place(speed=0.8, direction="right")
    print(f"{track_car}")
    left_status = left_motor.get_status()
    right_status = right_motor.get_status()
    print(f"  左电机: 反转 速度{left_status['pwm_value']:.2f}")
    print(f"  右电机: 正转 速度{right_status['pwm_value']:.2f}")
    print(f"  说明: 左右电机反向旋转，实现原地旋转")
    print()
    
    # 示例6：停止
    print("示例6：停止小车")
    print("-" * 50)
    track_car.stop()
    print(f"{track_car}")
    print()
    
    # 虚拟摇杆示例
    print("\n" + "=" * 50)
    print("虚拟摇杆示例")
    print("=" * 50)
    
    # 示例5：虚拟摇杆与电机联动
    print("示例5：虚拟摇杆与电机联动")
    print("-" * 50)
    
    # 从APP获取摇杆数据
    app_data_list = [
        (0.5, 0.0, 0.5),   # 向右移动
        (0.7, 0.0, 0.7),   # 继续向右
        (-0.5, 0.0, 0.5),  # 向左移动
        (-0.8, 0.0, 0.8),  # 继续向左
        (0.0, 0.0, 0.0),   # 中间停止
    ]
    
    for i, (x, y, intensity) in enumerate(app_data_list):
        print(f"数据帧 {i+1}:")
        joystick.update_from_app(x, y, intensity)
        joystick_buffer.add_sample(joystick)
        
        # 根据摇杆数据控制电机
        if joystick.is_centered():
            motor.stop()
            direction_text = "停止"
        elif joystick.get_x() > 0:
            motor.control(frequency=joystick.calculate_magnitude(), 
                         forward_enabled=True, backward_enabled=False)
            direction_text = "正转"
        else:
            motor.control(frequency=joystick.calculate_magnitude(), 
                         forward_enabled=False, backward_enabled=True)
            direction_text = "反转"
        
        print(f"  摇杆: {joystick}")
        print(f"  电机: {direction_text}, 频率: {joystick.calculate_magnitude():.2f}")
        print()
    
    # 显示平滑后的数据
    print("缓冲区平均值（平滑处理）:")
    avg = joystick_buffer.get_average()
    print(f"  平均X: {avg['x']:.2f}")
    print(f"  平均Y: {avg['y']:.2f}")
    print(f"  平均强度: {avg['intensity']:.2f}")
    
    # 获取完整状态
    print("\n摇杆完整状态:")
    status = joystick.get_status()
    for key, value in status.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    # 小车与摇杆联动示例
    print("\n" + "=" * 50)
    print("小车与虚拟摇杆联动示例")
    print("=" * 50)
    print("差速转向原理演示\n")
    
    test_cases = [
        {
            'name': '直线前进',
            'x': 0.0, 'y': 0.8,
            'description': '摇杆向前，两电机等速'
        },
        {
            'name': '向右转大圈',
            'x': 0.4, 'y': 0.8,
            'description': '摇杆向右前方，差速转向右'
        },
        {
            'name': '急速右转',
            'x': 0.8, 'y': 0.8,
            'description': '摇杆更向右，转弯更急'
        },
        {
            'name': '向左转大圈',
            'x': -0.4, 'y': 0.8,
            'description': '摇杆向左前方，差速转向左'
        },
        {
            'name': '极速左转',
            'x': -0.8, 'y': 0.8,
            'description': '摇杆更向左，转弯更急'
        },
        {
            'name': '停止',
            'x': 0.0, 'y': 0.0,
            'description': '摇杆中间，小车停止'
        }
    ]
    
    for i, case in enumerate(test_cases):
        print(f"测试 {i+1}: {case['name']}")
        print(f"  输入: (X={case['x']:>4.1f}, Y={case['y']:>4.1f})")
        print(f"  说明: {case['description']}")
        joystick.update_from_app(case['x'], case['y'], 0.0)
        track_car.update_from_joystick(joystick)
        print(f"  小车: {track_car}")
        
        left_status = left_motor.get_status()
        right_status = right_motor.get_status()
        print(f"    左电机: {left_status['pwm_value']:>5.2f} {'正' if left_status['forward_enabled'] else '反'}")
        print(f"    右电机: {right_status['pwm_value']:>5.2f} {'正' if right_status['forward_enabled'] else '反'}")
        print()

if __name__ == '__main__':
    main()