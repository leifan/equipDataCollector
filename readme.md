
# 安装说明

1、安装python3.7.3

2、安装需要的模块，模块文件requirements.txt
   执行命令 pip install -r requirements.txt
   
3、运行程序 run_mainApp.bat


# 通信协议 

接入设备有：
1、绿米系列产品，如温湿度，无线开关，主要用于查询无线开关状态
2、有毒气体： 乙醇、 臭氧
3、气压传感器(暂不支持)

主动上报条件：
1、状态和数据有变化
2、每5分钟一次
   comStatus  0: 通讯失败 1：通讯正常
     
设备数据：
1、采集有毒气体数据 （获取设备列表，重要参数 id 和 modbusAddr）
2、获取温湿度通讯状态（获取设备列表，重要参数devicedid 和 id，查询通讯状态）
 
上报数据格式：
'data': '[
{"equipCode": “youdu1”, "appId": 1001, "id": "1", "comStatus": 1, "value": 6.23},
{"equipCode":” youdu2”, "appId": 1001, "id": "2", "comStatus": 0, "value": 5.23},
{"equipCode":” wenshidu1”, "appId": 1001, "id": "3xxx1", "comStatus": 1, "temperature":374, "humidity":5815, "pressure":96190},
{"equipCode":” wenshidu2”, "appId": 1001, "id": "3xxx2", "comStatus": 0, "temperature":null, "humidity":null, "pressure":null},



# web登录接口

{
    "code": 200,
    "data": {
        "appId": "00001",
        "createTime": "2020-05-16 16:02:48",
        "creator": "商云辉",
        "realName": "采集器账号",
        "sessionId": "7eb65e6d3d8fcac5e3e3412f1de6eb27",
        "tel": "18729019999",
        "userAdmin": [
            {
                "addrInterface": "/natux-pcr-lab",
                "code": 11000,
                "permissionId": 11000,
                "permissionName": "DashBoard",
                "userId": 22
            },
            {
                "addrInterface": "/room_equip_history_select",
                "code": 11000,
                "permissionId": 11001,
                "permissionName": "某房间环境设备历史记录曲线图查询",
                "userId": 22
            },
            {
                "addrInterface": "/room_equip_data_select",
                "code": 11000,
                "permissionId": 11002,
                "permissionName": "房间环境设备数据查询",
                "userId": 22
            },
            {
                "addrInterface": "/instrument_type_count_select",
                "code": 11000,
                "permissionId": 11003,
                "permissionName": "仪器种类占比查询",
                "userId": 22
            },
            {
                "addrInterface": "/instrument_frequency_select",
                "code": 11000,
                "permissionId": 11004,
                "permissionName": "仪器试验次数查询",
                "userId": 22
            },
            {
                "addrInterface": "/instrument_reagent_select",
                "code": 11000,
                "permissionId": 11005,
                "permissionName": "仪器试剂消耗量查询",
                "userId": 22
            },
            {
                "addrInterface": "/sample_qualified_percent",
                "code": 11000,
                "permissionId": 11006,
                "permissionName": "单个物品的合格率",
                "userId": 22
            },
            {
                "addrInterface": "/sample_rlu_select",
                "code": 11000,
                "permissionId": 11007,
                "permissionName": "物品检测结果曲线图",
                "userId": 22
            },
            {
                "userId": 22
            },
            {
                "addrInterface": "/natux-pcr-lab",
                "code": 4000,
                "permissionId": 4000,
                "permissionName": "设备列表",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/environment/equip_list",
                "code": 4000,
                "permissionId": 4002,
                "permissionName": "查询设备",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/environment/add_equip",
                "code": 4000,
                "permissionId": 4003,
                "permissionName": "添加设备",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/environment/bind_equip",
                "code": 4000,
                "permissionId": 4004,
                "permissionName": "绑定设备编号",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/environment/update_equip",
                "code": 4000,
                "permissionId": 4005,
                "permissionName": "更新设备",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/environment/delete_equip",
                "code": 4000,
                "permissionId": 4006,
                "permissionName": "删除设备",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/environment/data_history_list",
                "code": 4000,
                "permissionId": 4007,
                "permissionName": "查询某个设备的数据历史记录",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/environment/synchronize_token",
                "code": 4000,
                "permissionId": 4008,
                "permissionName": "同步通行证",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/environment/switch_status",
                "code": 4000,
                "permissionId": 4009,
                "permissionName": "切换开关状态",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/environment/get_tempature_humidity_pressure",
                "code": 4000,
                "permissionId": 4010,
                "permissionName": "查看当前温湿度",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/environment/get_realtime_equip_list",
                "code": 4000,
                "permissionId": 4011,
                "permissionName": "查询实时网关下设备列表",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/environment/refreshToken",
                "code": 4000,
                "permissionId": 4012,
                "permissionName": "刷新通行证",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/environment/get_switch_status",
                "code": 4000,
                "permissionId": 4013,
                "permissionName": "查询某个开关的状态值",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/environment/equip_statistic",
                "code": 4000,
                "permissionId": 4016,
                "permissionName": "设备统计数据信息",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/environment/history/temperature_list",
                "code": 4000,
                "permissionId": 4017,
                "permissionName": "温度记录列表",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/environment/history/humidity_list",
                "code": 4000,
                "permissionId": 4018,
                "permissionName": "湿度记录列表",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/environment/history/pressure_list",
                "code": 4000,
                "permissionId": 4019,
                "permissionName": "气压记录列表",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/environment/history/switch_list",
                "code": 4000,
                "permissionId": 4020,
                "permissionName": "开关记录列表",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/environment/get_toxic_gas_equip",
                "code": 4000,
                "permissionId": 4021,
                "permissionName": "获取有毒气体设备接口",
                "userId": 22
            },
            {
                "addrInterface": "/natux-pcr-lab",
                "code": 13000,
                "permissionId": 13000,
                "permissionName": "故障报警",
                "userId": 22
            },
            {
                "addrInterface": "/warning_history_select",
                "code": 13000,
                "permissionId": 13001,
                "permissionName": "报警记录列表",
                "userId": 22
            },
            {
                "addrInterface": "/deal_statu_exchange",
                "code": 13000,
                "permissionId": 13002,
                "permissionName": "报警状态切换",
                "userId": 22
            },
            {
                "userId": 22
            },
            {
                "addrInterface": "/natux-pcr-lab",
                "code": 1000,
                "permissionId": 1000,
                "permissionName": "实验室人员管理",
                "userId": 22
            },
            {
                "addrInterface": "/user_save",
                "code": 1000,
                "permissionId": 1001,
                "permissionName": "添加",
                "userId": 22
            },
            {
                "addrInterface": "/user_update",
                "code": 1000,
                "permissionId": 1002,
                "permissionName": "编辑",
                "userId": 22
            },
            {
                "addrInterface": "/user_delete",
                "code": 1000,
                "permissionId": 1003,
                "permissionName": "删除",
                "userId": 22
            },
            {
                "addrInterface": "/user_select",
                "code": 1000,
                "permissionId": 1004,
                "permissionName": "查询",
                "userId": 22
            },
            {
                "addrInterface": "/user_reset_password",
                "code": 1000,
                "permissionId": 1005,
                "permissionName": "修改密码",
                "userId": 22
            },
            {
                "addrInterface": "/natux-pcr-lab",
                "code": 2000,
                "permissionId": 2000,
                "permissionName": "实验室权限管理",
                "userId": 22
            },
            {
                "addrInterface": "/admin_group_save",
                "code": 2000,
                "permissionId": 2001,
                "permissionName": "添加权限分组",
                "userId": 22
            },
            {
                "addrInterface": "/admin_group_select",
                "code": 2000,
                "permissionId": 2002,
                "permissionName": "查询权限分组",
                "userId": 22
            },
            {
                "addrInterface": "/admin_group_update",
                "code": 2000,
                "permissionId": 2003,
                "permissionName": "编辑权限分组",
                "userId": 22
            },
            {
                "addrInterface": "/admin_group_delete",
                "code": 2000,
                "permissionId": 2004,
                "permissionName": "删除权限分组",
                "userId": 22
            },
            {
                "addrInterface": "/admin_group_user_save",
                "code": 2000,
                "permissionId": 2005,
                "permissionName": "设置用户权限分组",
                "userId": 22
            },
            {
                "addrInterface": "/admin_permission_select",
                "code": 2000,
                "permissionId": 2006,
                "permissionName": "查询所有权限",
                "userId": 22
            },
            {
                "addrInterface": "/admin_group_permission_save",
                "code": 2000,
                "permissionId": 2007,
                "permissionName": "设置权限分组",
                "userId": 22
            },
            {
                "addrInterface": "/admin_user_group_select",
                "code": 2000,
                "permissionId": 2008,
                "permissionName": "查询用户权限分组",
                "userId": 22
            },
            {
                "addrInterface": "/admin_group_permission_select",
                "code": 2000,
                "permissionId": 2009,
                "permissionName": "查询分组权限",
                "userId": 22
            },
            {
                "addrInterface": "/natux-pcr-lab",
                "code": 3000,
                "permissionId": 3000,
                "permissionName": "部门管理",
                "userId": 22
            },
            {
                "addrInterface": "/dept_save",
                "code": 3000,
                "permissionId": 3001,
                "permissionName": "添加",
                "userId": 22
            },
            {
                "addrInterface": "/dept_select",
                "code": 3000,
                "permissionId": 3002,
                "permissionName": "查询",
                "userId": 22
            },
            {
                "addrInterface": "/dept_update",
                "code": 3000,
                "permissionId": 3003,
                "permissionName": "编辑",
                "userId": 22
            },
            {
                "addrInterface": "/dept_delete",
                "code": 3000,
                "permissionId": 3004,
                "permissionName": "删除",
                "userId": 22
            },
            {
                "addrInterface": "/natux-pcr-lab",
                "code": 16000,
                "permissionId": 16000,
                "permissionName": "考勤记录",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/attLog/attLog_list",
                "code": 16000,
                "permissionId": 16001,
                "permissionName": "考勤列表",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/attLog/attStatistics",
                "code": 16000,
                "permissionId": 16002,
                "permissionName": "考勤统计",
                "userId": 22
            },
            {
                "userId": 22
            },
            {
                "addrInterface": "/natux-pcr-lab",
                "code": 7000,
                "permissionId": 7000,
                "permissionName": "检测员管理",
                "userId": 22
            },
            {
                "addrInterface": "/inspector_save",
                "code": 7000,
                "permissionId": 7001,
                "permissionName": "添加",
                "userId": 22
            },
            {
                "addrInterface": "/inspector_select",
                "code": 7000,
                "permissionId": 7002,
                "permissionName": "查询",
                "userId": 22
            },
            {
                "addrInterface": "/natux-pcr-lab",
                "code": 8000,
                "permissionId": 8000,
                "permissionName": "洁净度管理",
                "userId": 22
            },
            {
                "addrInterface": "/history_data_select",
                "code": 8000,
                "permissionId": 8001,
                "permissionName": "查询洁净度数据",
                "userId": 22
            },
            {
                "addrInterface": "/sample_type_select",
                "code": 8000,
                "permissionId": 8002,
                "permissionName": "查询物品名称",
                "userId": 22
            },
            {
                "addrInterface": "/total_user_sample_count",
                "code": 8000,
                "permissionId": 8003,
                "permissionName": "查询建测量总数等信息",
                "userId": 22
            },
            {
                "addrInterface": "/daily_test_data_total_percent",
                "code": 8000,
                "permissionId": 8004,
                "permissionName": "检测率查询",
                "userId": 22
            },
            {
                "addrInterface": "/sample_type_total_count",
                "code": 8000,
                "permissionId": 8005,
                "permissionName": "各物品检测率占比",
                "userId": 22
            },
            {
                "addrInterface": "/daily_sample_total_count",
                "code": 8000,
                "permissionId": 8006,
                "permissionName": "单个检测物检测量和合格率曲线",
                "userId": 22
            },
            {
                "addrInterface": "/inspector_test_total",
                "code": 8000,
                "permissionId": 8007,
                "permissionName": "检测员检测量比例",
                "userId": 22
            },
            {
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/ipcDevice",
                "code": 10000,
                "permissionId": 10000,
                "permissionName": "摄像头管理",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/ipcDevice/ipc_list",
                "code": 10000,
                "permissionId": 10001,
                "permissionName": "查询",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/ipcDevice/add_ipc",
                "code": 10000,
                "permissionId": 10002,
                "permissionName": "添加",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/ipcDevice/update_ipc",
                "code": 10000,
                "permissionId": 10003,
                "permissionName": "编辑",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/ipcDevice/delete_ipc",
                "code": 10000,
                "permissionId": 10004,
                "permissionName": "删除",
                "userId": 22
            },
            {
                "addrInterface": "/natux-pcr-lab",
                "code": 6000,
                "permissionId": 6000,
                "permissionName": "仪器管理",
                "userId": 22
            },
            {
                "addrInterface": "/instrument_select",
                "code": 6000,
                "permissionId": 6001,
                "permissionName": "查询",
                "userId": 22
            },
            {
                "addrInterface": "/instrument_save",
                "code": 6000,
                "permissionId": 6002,
                "permissionName": "添加",
                "userId": 22
            },
            {
                "addrInterface": "/instrument_update",
                "code": 6000,
                "permissionId": 6003,
                "permissionName": "编辑",
                "userId": 22
            },
            {
                "addrInterface": "/instrument_delete",
                "code": 6000,
                "permissionId": 6004,
                "permissionName": "删除",
                "userId": 22
            },
            {
                "addrInterface": "/instrument_name_select",
                "code": 6000,
                "permissionId": 6005,
                "permissionName": "查询所有仪器名称",
                "userId": 22
            },
            {
                "addrInterface": "/instrument_brand_select",
                "code": 6000,
                "permissionId": 6006,
                "permissionName": "查询所有仪器品牌",
                "userId": 22
            },
            {
                "addrInterface": "/instrument_ts_select",
                "code": 6000,
                "permissionId": 6007,
                "permissionName": "查询所有仪器型号规格",
                "userId": 22
            },
            {
                "addrInterface": "/natux-pcr-lab",
                "code": 5000,
                "permissionId": 5000,
                "permissionName": "实验室房间管理",
                "userId": 22
            },
            {
                "addrInterface": "/lab_rooms_save",
                "code": 5000,
                "permissionId": 5001,
                "permissionName": "添加",
                "userId": 22
            },
            {
                "addrInterface": "/lab_rooms_select",
                "code": 5000,
                "permissionId": 5002,
                "permissionName": "查询",
                "userId": 22
            },
            {
                "addrInterface": "/lab_rooms_update",
                "code": 5000,
                "permissionId": 5003,
                "permissionName": "编辑",
                "userId": 22
            },
            {
                "addrInterface": "/lab_rooms_delete",
                "code": 5000,
                "permissionId": 5004,
                "permissionName": "删除",
                "userId": 22
            },
            {
                "addrInterface": "/natux-pcr-lab",
                "code": 15000,
                "permissionId": 15000,
                "permissionName": "试剂统计",
                "userId": 22
            },
            {
                "addrInterface": "/instrument_reagent_type_count_select",
                "code": 15000,
                "permissionId": 15001,
                "permissionName": "试剂消耗各种类数据查询",
                "userId": 22
            },
            {
                "addrInterface": "/reagent_history_select",
                "code": 15000,
                "permissionId": 15002,
                "permissionName": "试剂消耗记录查询",
                "userId": 22
            },
            {
                "addrInterface": "/reagent_everyday_data_select",
                "code": 15000,
                "permissionId": 15003,
                "permissionName": "试剂每天消耗量曲线图查询",
                "userId": 22
            },
            {
                "addrInterface": "/natux-pcr-lab",
                "code": 9000,
                "permissionId": 9000,
                "permissionName": "门禁管理",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/attDevice/attDevice_list",
                "code": 9000,
                "permissionId": 9001,
                "permissionName": "查询",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/attDevice/add_attDevice",
                "code": 9000,
                "permissionId": 9002,
                "permissionName": "添加",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/attDevice/update_attDevice",
                "code": 9000,
                "permissionId": 9003,
                "permissionName": "编辑",
                "userId": 22
            },
            {
                "addrInterface": "/pcr_lab/attDevice/delete_attDevice",
                "code": 9000,
                "permissionId": 9004,
                "permissionName": "删除",
                "userId": 22
            },
            {
                "addrInterface": "/natux-pcr-lab",
                "code": 14000,
                "permissionId": 14000,
                "permissionName": "空调控制中心",
                "userId": 22
            },
            {
                "addrInterface": "/get_ac_status",
                "code": 14000,
                "permissionId": 14001,
                "permissionName": "查询某个实验室房间内的空调状态",
                "userId": 22
            },
            {
                "addrInterface": "/send_ac_command",
                "code": 14000,
                "permissionId": 14002,
                "permissionName": "下发空调指令",
                "userId": 22
            }
        ],
        "userId": 22,
        "userName": "youduqiti@00001"
    },
    "desc": "成功"
}

# 获取设备列表：
{
    "code": 200,
    "data": {
        "list": [
            {
                "createTime": 1590951785000,
                "createTimePlain": "2020-06-01 03:03:05",
                "creator": "王",
                "deviceId": "lumi.158d0004845db6",
                "effect": "",
                "equipBrand": "绿米",
                "equipCode": "001",
                "equipName": "门口开关",
                "equipStatus": 0,
                "equipType": 6,
                "frequency": 10,
                "id": 1,
                "joinType": 1,
                "threshold": 1.00
            },
            {
                "createTime": 1590951785000,
                "createTimePlain": "2020-06-01 03:03:05",
                "creator": "王",
                "deviceId": "lumi.158d0004845db6",
                "effect": "",
                "equipBrand": "绿米",
                "equipCode": "002",
                "equipName": "门口开关2",
                "equipStatus": 0,
                "equipType": 6,
                "frequency": 10,
                "id": 2,
                "joinType": 1,
                "threshold": 1.00
            },
            {
                "createTime": 1590744972000,
                "createTimePlain": "2020-05-29 17:36:12",
                "creator": "王",
                "deviceId": "lumi.158d00044d3c12",
                "effect": "[1,2,3]",
                "equipBrand": "绿米",
                "equipCode": "003",
                "equipName": "冰箱温湿度传感器",
                "equipStatus": 0,
                "equipType": 1,
                "frequency": 10,
                "id": 3,
                "joinType": 1,
                "threshold": 1.00
            },
            {
                "createTime": 1590951785000,
                "createTimePlain": "2020-06-01 03:03:05",
                "creator": "王",
                "deviceId": "lumi.158d000392613e",
                "effect": "",
                "equipBrand": "绿米",
                "equipCode": "004",
                "equipName": "插座",
                "equipStatus": 0,
                "equipType": 7,
                "frequency": 10,
                "id": 4,
                "joinType": 1,
                "threshold": 1.00
            },
            {
                "createTime": 1590951785000,
                "createTimePlain": "2020-06-01 03:03:05",
                "creator": "王",
                "deviceId": "",
                "effect": "",
                "equipBrand": "其他",
                "equipCode": "005",
                "equipName": "有毒气体臭氧",
                "equipStatus": 0,
                "equipType": 4,
                "frequency": 10,
                "id": 5,
                "joinType": 2,
                "threshold": 1.00
            },
            {
                "createTime": 1590951785000,
                "createTimePlain": "2020-06-01 03:03:05",
                "creator": "王",
                "deviceId": "",
                "effect": "",
                "equipBrand": "其他",
                "equipCode": "006",
                "equipName": "有毒气体乙醇",
                "equipStatus": 0,
                "equipType": 5,
                "frequency": 10,
                "id": 6,
                "joinType": 2,
                "threshold": 1.00
            },
            {
                "createTime": 1590951785000,
                "createTimePlain": "2020-06-01 03:03:05",
                "creator": "王",
                "deviceId": "",
                "effect": "",
                "equipBrand": "其他",
                "equipCode": "007",
                "equipName": "有毒气体臭氧",
                "equipStatus": 0,
                "equipType": 4,
                "frequency": 10,
                "id": 7,
                "joinType": 2,
                "threshold": 1.00
            }
        ]
    },
    "desc": "成功"
}