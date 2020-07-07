import asyncio
import random

from mirai import Mirai, MessageChain, Member, Permission, Plain, At

from plugins.common.commons import read_json, write_json, print_msg
from plugins.common.decorators import commands
from plugins.guild.manage import calculate_points

groups_config_path = 'config/manage_groups.json'


async def handle_group_msg(app: Mirai, member: Member, message: MessageChain):
    manage_groups = read_json(groups_config_path)

    await calculate_points(member)

    plains = message.getAllofComponent(Plain)
    if len(plains) == 0:
        return

    msg = ''
    for plain in plains:
        msg += plain.toString().strip() + ' '
    msg = msg.strip()
    if msg == '':
        return

    if '开启凯露' == msg:
        if member.permission == Permission.Member:
            return await app.sendGroupMessage(member.group.id, [Plain(text='无权限使用此命令，请联系会长或管理')])
        if member.group.id not in manage_groups:
            manage_groups.append(member.group.id)
            write_json(groups_config_path, manage_groups)
            return await app.sendGroupMessage(member.group.id, [Plain(text='真是没办法呢，接下来将由我凯露大人监督你们会战，快感谢我吧~')])
        else:
            return await app.sendGroupMessage(member.group.id, [Plain(text='当前已为开启状态')])
    elif '关闭凯露' == msg:
        if member.permission == Permission.Member:
            return await app.sendGroupMessage(member.group.id, [Plain(text='无权限使用此命令，请联系会长或管理')])
        if member.group.id in manage_groups:
            manage_groups.remove(member.group.id)
            write_json(groups_config_path, manage_groups)
            return await app.sendGroupMessage(member.group.id, [Plain(text='太好了！终于不用再照顾你们了！只是。。。')])
        else:
            return await app.sendGroupMessage(member.group.id, [Plain(text='当前已为关闭状态')])

    if member.group.id not in manage_groups:
        return

    await asyncio.sleep(random.random())

    print_msg(msg=msg)
    sp = msg.split(maxsplit=1)
    if len(sp) > 1:
        cmd, *args = sp
        arg = ''.join(args)
    else:
        cmd = sp[0]
        arg = ''
    at: At = message.getFirstComponent(At)
    if at is not None and at.target != app.qq:
        arg = str(at.target) + ' ' + arg
    arg = arg.strip()
    print_msg(cmd=cmd)
    print_msg(arg=arg)
    handler = commands.get(cmd)
    print_msg(handler=handler)

    if handler:
        return await handler(app, member, arg)
