import os
import re

from mirai import Mirai, Member, Permission

from plugins.common.commons import write_json, read_json, reply_group
from plugins.common.constants import ILLEGAL_ERR


def get_all_guilds():
    guild_files = os.listdir('data/guild')
    guild_list = []
    for guild_file in guild_files:
        guild_name = guild_file.split('.json')[0]
        guild_list.append(int(guild_name))
    return guild_list


def write_guild(groupId, data):
    write_json('data/guild/' + str(groupId) + '.json', data)


def read_guild(groupId):
    try:
        return read_json('data/guild/' + str(groupId) + '.json')
    except FileNotFoundError:
        return {}


async def create_guild(app: Mirai, member: Member, args: str):
    if member.permission == Permission.Member:
        return await reply_group(app, member.group.id, '无权限使用此命令，请联系会长或管理', [member.id])
    if member.group.id in get_all_guilds():
        return await reply_group(app, member.group.id, '本群公会已存在，不用重复创建', [member.id])
    guild_name = member.group.name
    server = 'cn'
    if args != '':
        sp = args.split(' ', maxsplit=1)
        if len(sp) == 1:
            if sp[0] in ['cn', 'tw', 'jp']:
                server = sp[0]
            else:
                guild_name = sp[0]
        elif len(sp) == 2:
            if sp[0] not in ['cn', 'tw', 'jp']:
                return await reply_group(app, member.group.id, "服务器参数只能为['cn','tw','jp']", [member.id])
            server = sp[0]
            guild_name = sp[1]
    m_data = {'guild_name': guild_name, 'server': server, 'state': '关闭',
              'members': {str(member.id): {'name': member.memberName, 'points': 0, 'records': {}, 'sl': []}}}
    write_guild(member.group.id, m_data)
    return await reply_group(app, member.group.id, '公会创建成功, 请执行【开启公会】招收成员吧', [member.id])


async def set_server(app: Mirai, member: Member, args: str):
    if member.permission == Permission.Member:
        return await reply_group(app, member.group.id, '无权限使用此命令，请联系会长或管理', [member.id])
    g_data: dict = read_guild(member.group.id)
    if args not in ['cn', 'tw', 'jp']:
        return await reply_group(app, member.group.id, "服务器参数只能为['cn','tw','jp']", [member.id])
    if 'server' not in g_data:
        g_data['server'] = 'cn'
    if g_data['server'] == args:
        return await reply_group(app, member.group.id, "当前服务器已设置为" + args + ", 不用切换", [member.id])
    g_data['server'] = args
    write_guild(member.group.id, g_data)
    return await reply_group(app, member.group.id, '服务器成功设置为' + args, [member.id])


async def reset_guild(app: Mirai, member: Member, args: str):
    if member.permission == Permission.Member:
        return await reply_group(app, member.group.id, '无权限使用此命令，请联系会长或管理', [member.id])
    g_data: dict = read_guild(member.group.id)
    if 'server' not in g_data:
        g_data['server'] = 'cn'
    g_data['members'].clear()
    write_guild(member.group.id, g_data)
    return await reply_group(app, member.group.id, '公会已重置，请重新开始招收成员', [member.id])


async def exchange_guild_state(app: Mirai, member: Member, state: str, args: str):
    if member.permission == Permission.Member:
        return await reply_group(app, member.group.id, '无权限使用此命令，请联系会长或管理', [member.id])
    if member.group.id not in get_all_guilds():
        return await reply_group(app, member.group.id, '还未创建公会，请联系会长或管理', [member.id])
    g_data: dict = read_guild(member.group.id)
    if g_data['state'] == state:
        return await reply_group(app, member.group.id, '公会已是' + state + '状态', [member.id])
    if 'server' not in g_data:
        g_data['server'] = 'cn'
    g_data['state'] = state
    write_guild(member.group.id, g_data)
    return await reply_group(app, member.group.id, '公会' + state + '成功', [member.id])


async def join_guild(app: Mirai, member: Member, args: str):
    if member.group.id not in get_all_guilds():
        return await reply_group(app, member.group.id, '还未创建公会，请联系会长或管理')
    g_data: dict = read_guild(member.group.id)
    members: dict = g_data['members']
    if g_data['state'] == '关闭':
        return await reply_group(app, member.group.id, '公会是关闭状态，请联系会长或管理', [member.id])
    if str(member.id) in members.keys():
        return await reply_group(app, member.group.id, '你已经在公会里，不用重复入会', [member.id])
    if member.group.id != 1035953551 and len(members.keys()) >= 30:
        return await reply_group(app, member.group.id, '公会已满，请联系会长或管理', [member.id])
    members[str(member.id)] = {'name': member.memberName, 'points': 0, 'records': {}, 'sl': []}
    write_guild(member.group.id, g_data)
    return await reply_group(app, member.group.id, '入会成功', [member.id])


async def exit_guild(app: Mirai, member: Member, args: str):
    if member.group.id not in get_all_guilds():
        return await reply_group(app, member.group.id, '还未创建公会，请联系会长或管理')
    g_data: dict = read_guild(member.group.id)
    members: dict = g_data['members']
    if g_data['state'] == '关闭':
        return await reply_group(app, member.group.id, '公会是关闭状态，请联系会长或管理', [member.id])
    if args == '':
        if str(member.id) not in members.keys():
            return await reply_group(app, member.group.id, '你不在公会里，不用退出', [member.id])
        del members[str(member.id)]
    else:
        if member.permission == Permission.Member:
            return await reply_group(app, member.group.id, '无权限使用此命令，请联系会长或管理', [member.id])
        if not re.match(r'[1-9][0-9]{4,}', args):
            return await reply_group(app, member.group.id, ILLEGAL_ERR, [member.id])
        if args not in members.keys():
            return await reply_group(app, member.group.id, args + '不在公会里，不用退出', [member.id])
        del members[args]
    write_guild(member.group.id, g_data)
    return await reply_group(app, member.group.id, '退会成功', [member.id])


async def query_guild_state(app: Mirai, member: Member, args: str):
    if member.permission == Permission.Member:
        return await reply_group(app, member.group.id, '无权限使用此命令，请联系会长或管理', [member.id])
    if member.group.id not in get_all_guilds():
        return await reply_group(app, member.group.id, '还未创建公会，请联系会长或管理', [member.id])
    g_data: dict = read_guild(member.group.id)
    if 'server' not in g_data:
        g_data['server'] = 'cn'
    members = g_data['members']
    msg = '公会名为：' + g_data['guild_name'] + '\n'
    msg += '服务器为：' + g_data['server'] + '\n'
    msg += '公会当前状态为：' + g_data['state'] + '\n'
    msg += '公会当前共有 ' + str(len(members)) + ' 个人, 成员列表如下：\n'
    for key in members.keys():
        msg += key + '\t' + members[key]['name'] + '\t活跃度为：' + str(members[key]['points']) + '\n'
    return await reply_group(app, member.group.id, msg, [member.id])


async def calculate_points(member: Member):
    if member.group.id not in get_all_guilds():
        return
    g_data: dict = read_guild(member.group.id)
    members: dict = g_data['members']
    if str(member.id) not in members.keys():
        return
    current = members[str(member.id)]
    current['points'] += 1
    write_guild(member.group.id, g_data)


async def query_points(app: Mirai, member: Member):
    if member.group.id not in get_all_guilds():
        return await reply_group(app, member.group.id, '还未创建公会，请联系会长或管理')
    g_data: dict = read_guild(member.group.id)
    members: dict = g_data['members']
    if str(member.id) not in members.keys():
        return await reply_group(app, member.group.id, '你不在公会里，没有记录', [member.id])
    p: dict = {}
    for g_k in members.keys():
        p[g_k] = members[g_k]['points']
    rank_list = sorted(p.items(), key=lambda x: x[1], reverse=True)
    rank = 0
    for index, value in enumerate(rank_list):
        if value[0] == str(member.id):
            rank = index + 1
            break
    return await reply_group(app, member.group.id,
                             '你当前的活跃度为:' + str(members[str(member.id)]['points']) + ', 排名为:' + str(rank),
                             [member.id])


async def create_alt(app: Mirai, member: Member, args: str):
    if member.group.id not in get_all_guilds():
        return await reply_group(app, member.group.id, '还未创建公会，请联系会长或管理')
    g_data: dict = read_guild(member.group.id)
    members: dict = g_data['members']
    count = 0
    for id in members.keys():
        current_id: str = str(member.id)
        if current_id in id:
            count += 1
    if count == 0:
        return await reply_group(app, member.group.id, '大号还未入会，请先大号入会', [member.id])
    alt_id = str(member.id) + str(count)
    if len(args) > 0:
        if not re.match(r'[1-9][0-9]{4,}', args):
            return await reply_group(app, member.group.id, 'QQ格式不正确', [member.id])
        if args in members.keys():
            return await reply_group(app, member.group.id, args + '已经存在，请重新输入', [member.id])
        alt_id = args
    members[alt_id] = {'name': member.memberName + str(count), 'points': 0, 'records': {}, 'sl': []}
    write_guild(member.group.id, g_data)
    return await reply_group(app, member.group.id, '创建小号' + args + ' 并入会成功', [member.id])


async def is_guild_member(app: Mirai, member: Member):
    if member.group.id not in get_all_guilds():
        await reply_group(app, member.group.id, '还未创建公会，请联系会长或管理')
        return False
    g_data: dict = read_guild(member.group.id)
    members: dict = g_data['members']
    if str(member.id) not in members.keys() and member.id != 623697643:
        await reply_group(app, member.group.id, '你不在公会里，不能使用会战相关命令，请联系会长或管理', [member.id])
        return False
    else:
        return True
