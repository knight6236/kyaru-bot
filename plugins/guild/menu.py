from plugins.common.commons import reply_group


async def menu(app, member):
    msg = '公会管理相关命令：管理菜单\n'
    msg += "公会战相关命令: 会战菜单\n"
    msg += "公会战作业相关命令: 作业菜单\n"
    msg += "定时提醒任务相关命令: 任务菜单"
    await reply_group(app, member.group.id, msg)


async def manage_menu(app, member):
    msg = '创建公会：创建公会 公会名-不加就默认群名（需要管理权限）\n'
    msg += "设置服务器: 设置服务器 jp（需要管理权限, 参数为[cn,tw,jp]，默认cn）\n"
    msg += "开启/关闭成员入会: 开启公会/关闭公会（需要管理权限）\n"
    msg += "清空公会信息: 重置公会（需要管理权限）\n"
    msg += "入会/退会: 加入公会/退出公会（退会说明：退会 协助退会的QQ号，协助退会需要管理权限，不加的话就是自己退会）\n"
    msg += "查询公会信息: 公会信息\n"
    msg += "查询活跃度: 我的活跃度/排名"
    return await reply_group(app, member.group.id, msg)


async def battle_menu(app, member):
    msg = '开启会战: 开启会战/会战开始（需要管理权限）\n'
    msg += '关闭会战: 关闭会战/会战结束（需要管理权限）\n'
    msg += '预约boss: 预约1 伤害（纯数字，默认单位是w，不要加，命令和数字间有空格；尾刀/补偿刀在数字后面加*）\n'
    msg += "预约下一轮boss: 预约下轮\n"
    msg += "取消预约: 取消1\n"
    msg += "取消下一轮预约: 取消下轮\n"
    msg += "查询进度/预约/boss当前状态: 老几了/预约情况/预约状态\n"
    msg += "开启/关闭先预约再出刀: 开启预约出刀/关闭预约出刀（需要管理权限）\n"
    msg += "开启/关闭先预约再报刀: 开启预约报刀/关闭预约报刀（需要管理权限）\n"
    msg += "报刀: 报刀 QQ 伤害（纯数字，默认单位是w，不要加，命令和数字间有空格）(加QQ就是代刀)\n"
    msg += "修改出刀记录: 修改记录 QQ 记录id 伤害（QQ是要修改的人 记录id通过查询获得)（需要管理权限）\n"
    msg += "删除出刀记录: 删除记录 QQ 记录id（QQ是要删除的人 记录id通过查询获得)（需要管理权限）\n"
    msg += "申请出刀: 申请出刀/出刀\n"
    msg += "取消出刀: 取消出刀\n"
    msg += "查询出刀: 查刀/出刀情况\n"
    msg += "查询当天出刀统计: 出刀记录 QQ/日期（需要管理权限，不带QQ是查全部，带QQ是查个人）\n"
    msg += "导出当天出刀统计: 导出记录（需要管理权限）复制返回的统计信息到csv文件里，然后用excel打开即可\n"
    msg += "查询自己的出刀统计: 我的出刀记录\n"
    msg += "清空自己的出刀记录: 清空我的记录\n"
    msg += "清空当天的出刀记录: 清空记录 QQ/日期 (需要管理权限，未指定就是清空当天的全部记录)\n"
    msg += "清空全部的历史出刀记录: 清空全部记录(需要管理权限，一般会战结束后或开始前使用，会战期间慎用)\n"
    msg += "设置boss实际剩余血量: 更新老一/更1 血量（纯数字，默认单位是w，不要加，命令和数字间有空格）\n"
    msg += "boss死亡后: 老1了\n"
    msg += "上树: 上树/挂树\n"
    msg += "查询挂树情况: 树上情况/树上状态/查树\n"
    msg += "切换阶段: 二阶了\n"
    msg += "修改圈数: 修改圈 数字"
    return await reply_group(app, member.group.id, msg)


async def task_menu(app, member):
    msg = "记录作业: 导入作业 1-1 狼克剑圣猫拳511 700\n"
    msg += "查询作业: 查询作业 1-1（可选，不加是查询全部）\n"
    msg += "查询当前boss作业: 当前作业"
    return await reply_group(app, member.group.id, msg)


async def job_menu(app, member):
    # msg = "预订任务: 添加任务 x月x号x点x分和姬塔一起洗澡\n"
    msg = "预订任务: 添加任务 x月x号x点x分和凯露一起洗澡\n"
    msg += "取消任务: 删除任务 任务id（查询获得）\n"
    msg += "查询任务: 我的任务"
    return await reply_group(app, member.group.id, msg)
