import configparser


def General_Setting_Read():
    ''' Read Default Settings from the Setting.ini File  '''
    # instantiate
    Setting_File = 'setting.ini'
    config = configparser.ConfigParser()
    config.read(Setting_File, encoding='utf-8')
    "Read dynamic data from Setting.ini file"
    Mode = config.get('General Settings', 'Mode')
    safety_mode = config.get('General Settings', 'safety_mode')
    send_fd_file = config.get('General Settings', 'send_fd_file')
    adjust_acc = config.get('General Settings', 'adjust_acc')
    adjust_blake = config.get('General Settings', 'adjust_blake')
    adjust_str = config.get('General Settings', 'adjust_str')
    adjust_autoblake = config.get('General Settings', 'adjust_autoblake')
    control_time = config.get('General Settings', 'control_time')
    joycon_acc = config.get('General Settings', 'joycon_acc')
    joycon_str = config.get('General Settings', 'joycon_str')
    checkIP = config.get('General Settings', 'checkIP')
    checkPort = config.get('General Settings', 'checkPort')
    return Mode, safety_mode, send_fd_file, send_fd_file, adjust_acc, adjust_blake, adjust_str, adjust_autoblake,control_time,joycon_acc,joycon_str,checkIP,checkPort

def Setting_File_Read():
    ''' Read Default Settings from the Setting.ini File  '''
    # instantiate
    Setting_File = 'setting.ini'
    config = configparser.ConfigParser()
    config.read(Setting_File, encoding='utf-8')
    "Read dynamic data from Setting.ini file"
    IPaddress = config.get('Remote Control Settings', 'IPaddress')
    Port = config.get('Remote Control Settings', 'Port')
    Time_Out = config.get('Remote Control Settings', 'Time_Out')
    return IPaddress, Port, Time_Out

def TCP_Setting_Read():
    ''' Read Default Settings from the Setting.ini File  '''
    # instantiate
    Setting_File = 'setting.ini'
    config = configparser.ConfigParser()
    config.read(Setting_File, encoding='utf-8')
    "Read dynamic data from Setting.ini file"
    IPaddress = config.get('TCP Settings', 'IPaddress')
    Port = config.get('TCP Settings', 'Port')
    Time_Out = config.get('TCP Settings', 'Time_Out')
    return IPaddress, Port, Time_Out


if __name__ == '__main__':
    IPaddress, Port, Time_Out = Setting_File_Read()
    print("IPaddress = ",IPaddress)
    print("Port = ",Port)
    print("Timeout = ",Time_Out)

    print(type(Port))
    a = int(Port)*2
    print(a)
    print(type(a))
