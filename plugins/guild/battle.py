import asyncio
from pprint import pprint

from mirai import Permission, Member, Mirai

from plugins.common.commons import *
from plugins.common.constants import *
from plugins.guild.manage import is_guild_member, read_guild, write_guild

boss_data = [[]]


def init():
    global boss_data
    boss_data = read_json('data/boss_data.json')


init()


def write_battle(groupId, g_data):
    write_json('data/battle/' + str(groupId) + '.json', g_data)


def read_battle(groupId):
    g_data: dict = read_guild(groupId)
    try:
        b_data: dict = read_json('data/battle/' + str(groupId) + '.json')
        # if 'cache_boss' not in b_data:
        #     b_data['cache_boss'] = boss_data[g_data['server']][b_data['current_stage'] - 1][
        #         b_data['current_boss'] - 1].copy()
        # if 'current_boss_data' not in b_data:
        #     b_data['current_boss_data'] = boss_data[g_data['server']][b_data['current_stage'] - 1].copy()
        # if 'battling_members' not in b_data:
        #     b_data['battling_members'] = {}
        # if 'report_after_order' not in b_data:
        #     b_data['report_after_order'] = '关闭'
        # if 'apply_after_order' not in b_data:
        #     b_data['apply_after_order'] = '关闭'
        return b_data
    except FileNotFoundError:
        g_data: dict = read_guild(groupId)
        return {'battle_state': '关闭', 'report_after_order': '关闭', 'apply_after_order': '关闭', 'current_stage': 1,
                'current_boss': 1, 'current_loop': 1, 'battling_members': {}, 'tree_members': {},
                'cache_boss': boss_data[g_data['server']][0][0].copy(),
                'current_boss_data': boss_data[g_data['server']][0].copy()}


async def start_battle(app, member: Member, arg):
    if not await is_guild_member(app, member):
        return
    if member.permission == Permission.Member:
        return await reply_group(app, member.group.id, '无权限使用此命令，请联系会长或管理')
    g_data: dict = read_guild(member.group.id)
    if 'server' not in g_data:
        g_data['server'] = 'cn'
        write_guild(member.group.id, g_data)
    guild_data = {'battle_state': '开启', 'report_after_order': '关闭', 'apply_after_order': '关闭', 'current_stage': 1,
                  'current_boss': 1, 'current_loop': 1, 'battling_members': {}, 'tree_members': {},
                  'cache_boss': boss_data[g_data['server']][0][0].copy(),
                  'current_boss_data': boss_data[g_data['server']][0].copy()}
    write_battle(member.group.id, guild_data)
    return await reply_group(app, member.group.id, '会战已开启')


async def end_battle(app, member, arg):
    if not await is_guild_member(app, member):
        return
    if member.permission == Permission.Member:
        return await reply_group(app, member.group.id, '无权限使用此命令，请联系会长或管理')
    guild_data = read_battle(member.group.id)
    guild_data['battle_state'] = '关闭'
    write_battle(member.group.id, guild_data)
    return await reply_group(app, member.group.id, '会战已关闭')


async def is_battle(app, member):
    if not await is_guild_member(app, member):
        return False
    guild_data = read_battle(member.group.id)
    if guild_data['battle_state'] == '关闭':
        await reply_group(app, member.group.id, '会战功能还未开启，请联系会长或管理')
        return False
    return True


async def exchange_stage(app, member, index):
    if not await is_battle(app, member):
        return
    g_data: dict = read_guild(member.group.id)
    if g_data['server'] != 'jp':
        return await reply_group(app, member.group.id, '非日服，不用换阶')
    guild_data = read_battle(member.group.id)
    current_loop = guild_data['current_loop']
    if guild_data['current_stage'] == index:
        return await reply_group(app, member.group.id, '已进入 ' + str(index) + ' 阶段，不需要切换')
    elif guild_data['current_boss'] != 5:
        return await reply_group(app, member.group.id, '当前boss不是老5，不能切换到下一阶段')
    elif current_loop not in [3, 10, 34]:
        return await reply_group(app, member.group.id, '当前圈数未达到换阶标准，请确认后再使用')
    elif guild_data['current_stage'] == index - 1:
        g_data: dict = read_guild(member.group.id)
        guild_data['current_stage'] = index
        if index == 2:
            guild_data['current_loop'] = 3
        elif index == 3:
            guild_data['current_loop'] = 10
        elif index == 4:
            guild_data['current_loop'] = 34
        guild_data['current_boss_data'] = boss_data[g_data['server']][index - 1]
        # pprint(guild_data['current_boss_data'])
        # write_battle(member.group.id, guild_data)
        # await reply_group(app, member.group.id, '进入 ' + str(index) + ' 阶段')
        await asyncio.sleep(random.randint(1, 3))
        await boss_dead(app, member, 1, guild_data, True, False)
    else:
        return await reply_group(app, member.group.id,
                                 '当前阶段为第 ' + str(guild_data['current_stage']) + ' 阶段, 不能进入 ' + str(index) + ' 阶段')


async def order_boss(app, member, arg: str, index):
    if not await is_battle(app, member):
        return
    guild_data = read_battle(member.group.id)
    boss = guild_data['current_boss_data'][index - 1]
    killers = boss['killers'].copy()
    killer = {'name': member.memberName, 'hp': 0, 'tail': 0}
    if check_dmg(arg):
        if arg.endswith('*'):
            killer['tail'] = 1
            arg = arg[:len(arg) - 1]
        killer['hp'] = float(arg)
        if index == guild_data['current_boss']:
            if str(member.id) in killers:
                return await reply_group(app, member.group.id, '你已经预约过【本轮】老 ' + str(index) + ' 了', [member.id])
            if boss['pre_hp'] == 0 and float(arg) > 0:
                return await reply_group(app, member.group.id, '老 ' + str(index) + ' 已被预约完，无法再预约', [member.id])
            else:
                if float(arg) > boss['real_hp']:
                    return await reply_group(app, member.group.id,
                                             '预约血量超过【本轮】老 ' + str(index) + ' 实际剩余血量(' + str(
                                                 round(boss['real_hp'], 4)) + '), 请重新预约',
                                             [member.id])
                if float(arg) <= boss['pre_hp']:
                    boss['pre_hp'] = round(boss['pre_hp'] - float(arg), 4)
                    killers[str(member.id)] = killer
                    boss['killers'] = killers
                    write_battle(member.group.id, guild_data)
                    return await reply_group(app, member.group.id, '【本轮】老 ' + str(index) + ' 预约成功', [member.id])
                else:
                    return await reply_group(app, member.group.id,
                                             '预约血量超过【本轮】老 ' + str(index) + ' 剩余预约血量(' + str(
                                                 round(boss['pre_hp'], 4)) + '), 请重新预约',
                                             [member.id])
        else:
            if str(member.id) in killers:
                return await reply_group(app, member.group.id, '你已经预约过老 ' + str(index) + ' 了', [member.id])
            if boss['pre_hp'] == 0 and float(arg) > 0:
                return await reply_group(app, member.group.id, '老 ' + str(index) + ' 已被预约完，无法再预约', [member.id])
            else:
                if float(arg) <= boss['pre_hp']:
                    boss['pre_hp'] = round(boss['pre_hp'] - float(arg), 4)
                    killers[str(member.id)] = killer
                    boss['killers'] = killers
                    write_battle(member.group.id, guild_data)
                    return await reply_group(app, member.group.id, '老 ' + str(index) + ' 预约成功', [member.id])
                else:
                    return await reply_group(app, member.group.id,
                                             '预约血量超过老 ' + str(index) + ' 剩余预约血量(' + str(
                                                 round(boss['pre_hp'], 4)) + '), 请重新预约',
                                             [member.id])
    else:
        return await reply_group(app, member.group.id, ILLEGAL_ERR, [member.id])


async def order_next_boss(app, member, arg):
    if not await is_battle(app, member):
        return
    guild_data = read_battle(member.group.id)
    current_boss = guild_data['current_boss']
    cache_boss = guild_data['cache_boss']
    cache_killers = cache_boss['killers'].copy()
    killer = {'name': member.memberName, 'hp': 0, 'tail': 0}
    if check_dmg(arg):
        if arg.endswith('*'):
            killer['tail'] = 1
            arg = arg[:len(arg) - 1]
        killer['hp'] = float(arg)
        if str(member.id) in cache_killers:
            return await reply_group(app, member.group.id, '你已经预约过【下一轮】老 ' + str(current_boss) + ' 了', [member.id])
        if cache_boss['pre_hp'] == 0 and float(arg) > 0:
            return await reply_group(app, member.group.id, '【下一轮】老 ' + str(current_boss) + ' 已被预约完，无法再预约', [member.id])
        if float(arg) <= cache_boss['pre_hp']:
            cache_boss['pre_hp'] = round(cache_boss['pre_hp'] - float(arg), 4)
            cache_killers[str(member.id)] = killer
            cache_boss['killers'] = cache_killers
            write_battle(member.group.id, guild_data)
            return await reply_group(app, member.group.id, '【下一轮】老 ' + str(current_boss) + ' 预约成功', [member.id])
        else:
            return await reply_group(app, member.group.id,
                                     '预约血量超过【下一轮】老 ' + str(current_boss) + ' 剩余预约血量(' + str(
                                         round(cache_boss['pre_hp'], 4)) + '), 请重新预约', [member.id])
    else:
        return await reply_group(app, member.group.id, ILLEGAL_ERR, [member.id])


async def cancel_boss(app, member, index, reply=True, report=True, g_data={}):
    if not await is_battle(app, member):
        return
    guild_data = read_battle(member.group.id)
    if g_data:
        guild_data = g_data
    boss = guild_data['current_boss_data'][index - 1]
    killers = boss['killers']
    # pprint(killers)
    if index == guild_data['current_boss']:
        if str(member.id) not in killers and reply:
            return await reply_group(app, member.group.id, '你还没预约老 ' + str(index), [member.id])
        if str(member.id) in killers:
            preKiller = killers[str(member.id)]
            if report:
                boss['pre_hp'] = round(boss['pre_hp'] + float(preKiller['hp']), 4)
            del killers[str(member.id)]
            # pprint(guild_data)
            write_battle(member.group.id, guild_data)
            if reply:
                return await reply_group(app, member.group.id, '【本轮】老 ' + str(index) + ' 取消成功', [member.id])
    else:
        if str(member.id) not in killers and reply:
            return await reply_group(app, member.group.id, '你还没预约老 ' + str(index), [member.id])
        preKiller = killers[str(member.id)]
        boss['pre_hp'] = round(boss['pre_hp'] + float(preKiller['hp']), 4)
        del killers[str(member.id)]
        write_battle(member.group.id, guild_data)
        if reply:
            return await reply_group(app, member.group.id, '老 ' + str(index) + ' 取消成功', [member.id])


async def cancel_next_boss(app, member):
    if not await is_battle(app, member):
        return
    guild_data = read_battle(member.group.id)
    current_boss = guild_data['current_boss']
    cache_boss = guild_data['cache_boss']
    cache_killers = cache_boss['killers']
    if str(member.id) not in cache_killers:
        return await reply_group(app, member.group.id, '你还没预约【下一轮】老 ' + str(current_boss), [member.id])
    if str(member.id) in cache_killers:
        preKiller = cache_killers[str(member.id)]
        cache_boss['pre_hp'] = round(cache_boss['pre_hp'] + float(preKiller['hp']), 4)
        del cache_killers[str(member.id)]
        write_battle(member.group.id, guild_data)
        return await reply_group(app, member.group.id, '【下一轮】老 ' + str(current_boss) + ' 取消成功', [member.id])


async def boss_dead(app, member: Member, index, s_data={}, next_stage=False, next=True):
    if not await is_battle(app, member):
        return
    if s_data:
        guild_data = s_data
    else:
        guild_data = read_battle(member.group.id)
    current_boss = guild_data['current_boss']
    current_loop = guild_data['current_loop']
    g_data: dict = read_guild(member.group.id)
    if index == 1 and next:
        if g_data['server'] == 'jp':
            if current_loop in [3, 10, 34] and current_boss == 5:
                await reply_group(app, member.group.id,
                                  str(guild_data['current_stage']) + '阶段已完成，即将进入' + str(
                                      guild_data['current_stage'] + 1) + '阶段')
                stage = 1
                if current_loop == 3:
                    stage = 2
                elif current_loop == 10:
                    stage = 3
                elif current_loop == 34:
                    stage = 4
                await exchange_stage(app, member, stage)
                return
    if current_boss == index:
        return await reply_group(app, member.group.id, '目前的boss就是老 ' + str(current_boss))
    elif (member.permission != Permission.Member and (
            (index != 1 and index > current_boss) or (index == 1 and current_boss == 5))) or (
            (current_boss != 5 and current_boss == index - 1) or (current_boss == 5 and index == 1) or next_stage):
        # 初始化下一个boss的数据
        current = guild_data['current_boss_data'][current_boss - 1]
        if (not next_stage and guild_data['current_stage'] > 1) or g_data['server'] != 'jp':
            cache_boss: dict = guild_data['cache_boss'].copy()
            cache_boss['real_hp'] = cache_boss['all_hp']
            current.update(cache_boss)

        # 初始化cache_boss的数据
        guild_data['cache_boss'] = boss_data[read_guild(member.group.id)['server']][guild_data['current_stage'] - 1][
            index - 1].copy()

        # await down_tree(app, member, guild_data)
        tree_members = guild_data['tree_members'].keys()
        if len(tree_members) > 0:
            await reply_group(app, member.group.id, 'boss已死亡', map(int, tree_members))
            guild_data['tree_members'].clear()
            await asyncio.sleep(random.randint(1, 3))

        if current_boss == 5 and index == 1:
            guild_data['current_loop'] += 1
        guild_data['current_boss'] = index
        guild_data['battling_members'] = {}
        write_battle(member.group.id, guild_data)

        boss = guild_data['current_boss_data'][index - 1]
        killers = boss['killers']
        members = []
        if g_data['server'] == 'jp':
            msg = '当前为第 ' + str(guild_data['current_stage']) + ' 阶 - 第 ' + str(
                guild_data['current_loop']) + ' 圈 - 老 ' + str(
                index) + '\n'
        else:
            msg = '当前为第 ' + str(guild_data['current_loop']) + ' 圈 - 老 ' + str(index) + '\n'
        if len(killers) > 0:
            rank_list = sort_dmg(killers)
            for rank in rank_list:
                members.append(int(rank[0]))
                msg += rank[1] + ' ' + str(rank[2])
                if rank[3] == 1:
                    msg += ' 是尾刀/补偿刀'
                msg += ', '
            msg += '请遵守尾刀和大刀优先的原则，按顺序出刀'
        return await reply_group(app, member.group.id, msg, members)
    else:
        return await reply_group(app, member.group.id, '当前boss为老 ' + str(current_boss) + ', 不能跳到老 ' + str(index))


async def reset_boss(app, member, index):
    if not await is_battle(app, member):
        return
    guild_data = read_battle(member.group.id)
    if not re.match(r'[1-5]', index):
        return await reply_group(app, member.group.id, '只能重置1-5')
    current = guild_data['current_boss_data'][int(index) - 1]
    current['pre_hp'] = current['real_hp'] = current['all_hp']
    current['killers'] = {}
    write_battle(member.group.id, guild_data)
    await reply_group(app, member.group.id, '重置老 ' + str(index) + ' 成功')


async def stage_info(app, member):
    if not await is_battle(app, member):
        return
    guild_data = read_battle(member.group.id)
    current_stage = guild_data['current_stage']
    current_boss = guild_data['current_boss']
    current_loop = guild_data['current_loop']
    msg = '当前为第 ' + str(current_stage) + ' 阶 - 第 ' + str(current_loop) + ' 圈\n\n'
    boss_list: list = guild_data['current_boss_data']
    # pprint(boss_list)
    boss_list.insert(current_boss - 1, guild_data['cache_boss'])
    for i, boss in enumerate(boss_list):
        tmp = ''
        index = i + 1
        if current_boss == i:
            index = i
            tmp += '【正在进行中】 -> '
        elif current_boss < i:
            index = i
        killers = boss['killers']
        if current_boss == i + 1:
            tmp += '预约下一轮老 ' + str(index) + ' 的有 ' + str(len(killers)) + " 个人,"
        else:
            tmp += '预约老 ' + str(index) + ' 的有 ' + str(len(killers)) + " 个人,"
        if len(killers) > 0:
            tmp += " 分别是："
            for key in killers.keys():
                killer = killers[key]
                # k_name = strQ2B(killer['name']).split('(', maxsplit=1)[0]
                k_name = killer['name']
                tmp += k_name + ' ' + str(killer['hp']) + '、'
        pre_hp = 0
        if boss['pre_hp'] > 0:
            pre_hp = round(boss['pre_hp'], 4)
        msg += tmp[:len(tmp) - 1] + ", 预约剩余血量：" + str(pre_hp) + ", 实际剩余血量：" + str(round(boss['real_hp'], 4)) + '\n\n'
    return await reply_group(app, member.group.id, msg, [member.id])


async def set_apply_after_order(app, member: Member, state):
    if not await is_battle(app, member):
        return
    if member.permission == Permission.Member:
        return await reply_group(app, member.group, '无权限使用此命令，请联系会长或管理')
    guild_data = read_battle(member.group.id)
    apply_after_order = guild_data['apply_after_order']
    if apply_after_order != state:
        guild_data['apply_after_order'] = state
        write_battle(member.group.id, guild_data)
        return await reply_group(app, member.group, '出刀前先预约 ' + state + ' 成功')
    else:
        return await reply_group(app, member.group, '出刀前先预约已 ' + state + ' 不用再设置')


async def apply_battle(app, member: Member):
    if not await is_battle(app, member):
        return
    guild_data = read_battle(member.group.id)
    current_stage = guild_data['current_stage']
    current_boss = guild_data['current_boss']
    current_loop = guild_data['current_loop']
    current_boss_data = guild_data['current_boss_data'][current_boss - 1]
    killers = current_boss_data['killers']
    if guild_data['apply_after_order'] == '开启' and str(member.id) not in killers:
        return await reply_group(app, member.group.id, '你还未预约当前boss【老' + str(current_boss) + '】，请先预约再申请出刀，或联系管理关闭申请前预约')

    msg = '当前为第 ' + str(current_stage) + ' 阶 - 第 ' + str(current_loop) + ' 圈 - 老 ' + str(current_boss) + '\n'
    msg += "实际剩余血量：" + str(round(current_boss_data['real_hp'], 4)) + "\n"

    battling_members = guild_data['battling_members']
    if len(battling_members) == 0:
        msg += '无人出刀、'
    else:
        if str(member.id) in battling_members:
            return await reply_group(app, member.group.id, '已申请过出刀了，不用重复申请')
        msg += '现有 ' + str(len(battling_members)) + ' 个在出刀，分别是：'
        # flag = guild_data['apply_after_order'] == '开启' and str(member.id) in killers
        for battling_member in battling_members:
            msg += battling_members[battling_member]
            if battling_member in killers:
                msg += ' ' + str(round(killers[battling_member]['hp'], 4))
            msg += '、'
    msg = msg[:len(msg) - 1] + '\n申请出刀成功'
    battling_members[str(member.id)] = member.memberName
    write_battle(member.group.id, guild_data)
    return await reply_group(app, member.group.id, msg, [member.id])


async def cancel_battle(app, member: Member, reply=True, g_data={}):
    if not await is_battle(app, member):
        return
    guild_data = read_battle(member.group.id)
    if not reply:
        guild_data = g_data
    battling_members = guild_data['battling_members']
    if len(battling_members) == 0 or (str(member.id) not in battling_members):
        return await reply_group(app, member.group.id, '你还未申请过出刀')
    del battling_members[str(member.id)]
    write_battle(member.group.id, guild_data)
    if reply:
        return await reply_group(app, member.group.id, '取消出刀成功', [member.id])


async def battle_info(app, member: Member):
    if not await is_battle(app, member):
        return
    guild_data = read_battle(member.group.id)
    current_stage = guild_data['current_stage']
    current_boss = guild_data['current_boss']
    current_loop = guild_data['current_loop']
    current_boss_data = guild_data['current_boss_data'][current_boss - 1]

    msg = '当前为第 ' + str(current_stage) + ' 阶 - 第 ' + str(current_loop) + ' 圈 - 老 ' + str(current_boss) + '\n'
    msg += "实际剩余血量：" + str(round(current_boss_data['real_hp'], 4)) + "\n"

    battling_members = guild_data['battling_members']
    if len(battling_members) == 0:
        msg += '无人出刀、'
    else:
        msg += '现有 ' + str(len(battling_members)) + ' 个在出刀，分别是：'
        for battling_member in battling_members:
            msg += battling_members[battling_member] + '、'
    msg = msg[:len(msg) - 1]
    return await reply_group(app, member.group.id, msg, [member.id])


async def set_report_after_order(app, member: Member, state):
    if not await is_battle(app, member):
        return
    if member.permission == Permission.Member:
        return await reply_group(app, member.group, '无权限使用此命令，请联系会长或管理')
    guild_data = read_battle(member.group.id)
    report_after_order = guild_data['report_after_order']
    if report_after_order != state:
        guild_data['report_after_order'] = state
        write_battle(member.group.id, guild_data)
        return await reply_group(app, member.group, '报刀前先预约 ' + state + ' 成功')
    else:
        return await reply_group(app, member.group, '报刀前先预约已 ' + state + ' 不用再设置')


async def report_dmg(app, member, arg: str):
    if not await is_battle(app, member):
        return
    guild_data = read_battle(member.group.id)
    current_boss = guild_data['current_boss']
    boss = guild_data['current_boss_data'][current_boss - 1]
    killers = boss['killers']

    if guild_data['report_after_order'] == '开启' and str(member.id) not in killers:
        return await reply_group(app, member.group, '请先预约再报刀，或者联系管理关闭报刀前预约')

    sp = arg.split(' ', maxsplit=1)
    if len(sp) == 1:
        memberId = str(member.id)
        dmg = sp[0]
    elif len(sp) == 2:
        if not re.match(r'[1-9][0-9]{4,}', sp[0]):
            return await reply_group(app, member.group.id, ILLEGAL_ERR, [member.id])
        g_data: dict = read_guild(member.group.id)
        members = g_data['members']
        if sp[0] not in members.keys():
            return await reply_group(app, member.group.id, sp[0] + '还未入会')
        memberId = sp[0]
        dmg = sp[1]
    if check_dmg(dmg):
        record = {"id": "0", "boss": current_boss, "dmg": 0, "tail": 0}
        if dmg.endswith('*'):
            dmg = dmg[:len(dmg) - 1]
            record['tail'] = 1
        record['dmg'] = float(dmg)

        if float(dmg) > boss['real_hp']:
            return await reply_group(app, member.group.id, '无效数据，伤害不会比剩余血量高, 实际剩余血量：' + str(round(boss['real_hp'], 4)),
                                     [member.id])

        # 记录出刀数据
        g_data: dict = read_guild(member.group.id)
        members = g_data['members']
        current_member = members[memberId]
        records = {}
        if 'records' in current_member:
            records = current_member['records']
        else:
            current_member['records'] = {}
        current_date = current_date_str()
        current_arr = []
        if current_date in records:
            current_arr = records[current_date]

        normal_count = 0
        tail_count = 0
        for ca in current_arr:
            if ca['tail'] == 0:
                normal_count += 1
            elif ca['tail'] == 1:
                tail_count += 1
        if normal_count >= 3 and record['tail'] == 0:
            return await reply_group(app, member.group.id, '每日完整刀不能大于3刀，请重新报刀，或联系管理调整出刀记录', [member.id])
        if tail_count >= 6 and record['tail'] == 1:
            return await reply_group(app, member.group.id, '每日尾刀和补偿刀不能大于6刀，请重新报刀，或联系管理调整出刀记录', [member.id])

        c_count: int = 1
        for m_id in members:
            m_info = members[m_id]
            if 'records' in m_info:
                m_rs = m_info['records']
                if current_date in m_rs:
                    c_arr = m_rs[current_date]
                    c_count += len(c_arr)
        today = datetime.datetime.now().strftime("%m%d")
        current_id = today + '{:0>3s}'.format(str(c_count))
        print_msg(current_id=current_id)
        record['id'] = current_id
        current_arr.append(record)
        records[current_date] = current_arr
        current_member['records'] = records
        write_guild(member.group.id, g_data)

        # print_msg(memberId=memberId, killers=killers)
        if memberId in killers:
            await cancel_boss(app, member, current_boss, False, False, guild_data)

        battling_members = guild_data['battling_members']
        # pprint(battling_members)
        if memberId in battling_members:
            await cancel_battle(app, member, False, guild_data)

        boss['real_hp'] = round(boss['real_hp'] - float(dmg), 4)
        write_battle(member.group.id, guild_data)

        await reply_group(app, member.group.id,
                          '报刀成功, 老' + str(current_boss) + '实际剩余血量：' + str(round(boss['real_hp'], 4)),
                          [member.id])
    else:
        return await reply_group(app, member.group.id, ILLEGAL_ERR, [member.id])


async def urge_knife(app: Mirai, member: Member, arg: str):
    if not await is_battle(app, member):
        return
    if member.permission == Permission.Member:
        return reply_group(app, member, '权限不够，只有会长或管理能使用', [member.id])
    g_data: dict = read_guild(member.group.id)
    members = g_data['members']
    urge_members: list = []
    current_date = current_date_str()
    group_members: list = await app.memberList(member.group.id)
    members_list = []
    for m in group_members:
        members_list.append(m.id)
    for id in members:
        current_member = members[id]
        count = 0
        if 'records' in current_member:
            records = current_member['records']
            if current_date in records:
                current_arr = records[current_date]
                for ca in current_arr:
                    if ca['tail'] == 0:
                        count += 1
        if count == 0 and int(id) in members_list:
            urge_members.append(id)
    print_msg(len=len(urge_members), urge_members=urge_members)
    if len(urge_members):
        for i in range(0, len(urge_members) // 10 + 1):
            start = i * 10
            end = (i + 1) * 10
            if end > len(urge_members):
                end = len(urge_members)
            await reply_group(app, member.group.id, '今天还一刀没出，搞快点！', map(int, urge_members[start:end]))
            await asyncio.sleep(random.random())
        return
    else:
        return await reply_group(app, member.group.id, '会内成员今天均已出过刀')


async def sl(app: Mirai, member: Member, arg: str, my=False):
    if not await is_battle(app, member):
        return
    g_data: dict = read_guild(member.group.id)
    members = g_data['members']
    memberId = str(member.id)
    if len(arg) > 0:
        if member.permission == Permission.Member:
            return await reply_group(app, member.group.id, '无权限使用此命令，请联系会长或管理', [member.id])
        if not re.match(r'[1-9][0-9]{4,}', arg):
            return await reply_group(app, member.group.id, 'QQ格式不正确', [member.id])
        if arg not in members:
            return await reply_group(app, member.group.id, arg + '不在公会里', [member.id])
        memberId = arg
    member_info = members[memberId]
    if 'sl' not in member_info:
        member_info['sl'] = []
    sl_list: list = member_info['sl']
    current_date = current_date_str()
    if current_date in sl_list:
        return await reply_group(app, member.group.id, member_info['name'] + '今天已经sl过了')
    else:
        if my:
            return await reply_group(app, member.group.id, member_info['name'] + '今天还未sl')
    sl_list.append(current_date)
    write_guild(member.group.id, g_data)
    return await reply_group(app, member.group.id, '已记录' + member_info['name'] + '今天的sl')


async def cancel_sl(app: Mirai, member: Member, arg: str):
    if not await is_battle(app, member):
        return
    g_data: dict = read_guild(member.group.id)
    members = g_data['members']
    memberId = str(member.id)
    if len(arg) > 0:
        if member.permission == Permission.Member:
            return await reply_group(app, member.group.id, '无权限使用此命令，请联系会长或管理', [member.id])
        if not re.match(r'[1-9][0-9]{4,}', arg):
            return await reply_group(app, member.group.id, 'QQ格式不正确', [member.id])
        if arg not in members:
            return await reply_group(app, member.group.id, arg + '不在公会里', [member.id])
        memberId = arg
    member_info = members[memberId]
    if 'sl' not in member_info:
        member_info['sl'] = []
    sl_list: list = member_info['sl']
    current_date = current_date_str()
    if current_date not in sl_list:
        return await reply_group(app, member.group.id, member_info['name'] + '今天还未sl')
    sl_list.remove(current_date)
    write_guild(member.group.id, g_data)
    return await reply_group(app, member.group.id, '已取消' + member_info['name'] + '今天的sl')


async def my_dmg_records(app: Mirai, member: Member, args: str):
    if not await is_battle(app, member):
        return
    g_data: dict = read_guild(member.group.id)
    members = g_data['members']
    current_date = current_date_str()
    if len(args) > 0:
        member_info = members[args]
        msg = members[args]['name'] + '(' + args + ') ' + current_date + ' 出刀记录如下：\n'
    else:
        member_info = members[str(member.id)]
        msg = member_info['name'] + ' ' + current_date + ' 出刀记录如下：\n'
    if 'records' not in member_info:
        msg += ' 已出 0/3 刀，竟然还一刀都未出，赶紧摸轴去[○･｀Д´･ ○]\n'
    else:
        records = member_info['records']
        if current_date in records:
            record_arr = records[current_date]
            normal_list = []
            tail_list = []
            for record in record_arr:
                item = ''
                if 'id' in record:
                    item = record['id'] + '\t'
                item += '老' + str(record['boss']) + '\t' + str(record['dmg'])
                # item += str(record['dmg'])
                if record['tail'] == 0:
                    normal_list.append(item)
                elif record['tail'] == 1:
                    tail_list.append(item)
            msg += ' 已出 ' + str(len(normal_list)) + '/3 刀'
            if len(normal_list) > 0:
                msg += '\n完整刀\n\t' + '\n\t'.join(normal_list)
            if len(tail_list) > 0:
                msg += '\n补偿刀/尾刀\n\t' + '\n\t'.join(tail_list)
            if len(normal_list) == 3:
                msg += '\n今天有好好努力出刀呢！辛苦啦 (≧∇≦)ﾉ'
            elif len(normal_list) == 0:
                msg += '\n竟然还一刀都未出，赶紧摸轴去[○･｀Д´･ ○]'
        else:
            msg += ' 已出 0/3 刀，竟然还一刀都未出，赶紧摸轴去[○･｀Д´･ ○]\n'

    return await reply_group(app, member.group.id, msg, [member.id])


async def modify_current_dmg_records(app: Mirai, member: Member, args: str):
    if not await is_battle(app, member):
        return
    if member.permission == Permission.Member:
        return await reply_group(app, member.group.id, '无权限使用此命令，请联系会长或管理', [member.id])
    sp = args.split(' ', maxsplit=2)
    if len(sp) < 3:
        return await reply_group(app, member.group.id, '参数不足，请按照【修改记录 QQ 记录id 伤害】的格式重新输入', [member.id])
    if not re.match(r'[1-9][0-9]{4,}', sp[0]):
        return await reply_group(app, member.group.id, 'QQ格式不正确', [member.id])
    if not re.match(r'[0-9]{7}', sp[1]):
        return await reply_group(app, member.group.id, '记录id格式不正确', [member.id])
    g_data: dict = read_guild(member.group.id)
    members = g_data['members']
    current_date = current_date_str()
    if sp[0] not in members:
        return await reply_group(app, member.group.id, sp[0] + '不在公会里', [member.id])
    records = members[sp[0]]['records']
    # print(records)
    if current_date not in records:
        return await reply_group(app, member.group.id, sp[0] + ' ' + current_date + ' 无出刀记录', [member.id])
    current_records = records[current_date]
    flag = True
    for record in current_records:
        if sp[1] == record['id']:
            flag = False
            if check_dmg(sp[2]):
                if sp[2].endswith('*'):
                    record['dmg'] = round(float(sp[2][:len(sp[2]) - 1]), 4)
                    record['tail'] = 1
                else:
                    record['dmg'] = round(float(sp[2]), 4)
                    record['tail'] = 0
            else:
                return await reply_group(app, member.group.id, '伤害值不合法，请重新输入', [member.id])
    if flag:
        return await reply_group(app, member.group.id, sp[1] + '不在记录里，请确认后再修改', [member.id])
    write_guild(member.group.id, g_data)
    return await reply_group(app, member.group.id, '已将' + sp[0] + '的伤害修改为' + sp[2], [member.id])


async def delete_current_dmg_records(app: Mirai, member: Member, args: str):
    if not await is_battle(app, member):
        return
    if member.permission == Permission.Member:
        return await reply_group(app, member.group.id, '无权限使用此命令，请联系会长或管理', [member.id])
    sp = args.split(' ', maxsplit=1)
    if len(sp) < 2:
        return await reply_group(app, member.group.id, '参数不足，请按照【删除记录 QQ 记录id】的格式重新输入', [member.id])
    if not re.match(r'[1-9][0-9]{4,}', sp[0]):
        return await reply_group(app, member.group.id, 'QQ格式不正确', [member.id])
    if not re.match(r'[0-9]{7}', sp[1]):
        return await reply_group(app, member.group.id, '记录id格式不正确', [member.id])
    g_data: dict = read_guild(member.group.id)
    members = g_data['members']
    current_date = current_date_str()
    if sp[0] not in members:
        return await reply_group(app, member.group.id, sp[0] + '不在公会里', [member.id])
    records = members[sp[0]]['records']
    # print(records)
    if current_date not in records:
        return await reply_group(app, member.group.id, sp[0] + ' ' + current_date + ' 无出刀记录', [member.id])
    current_records = records[current_date]
    flag = True
    for record in current_records:
        if sp[1] == record['id']:
            flag = False
            current_records.remove(record)
    if flag:
        return await reply_group(app, member.group.id, sp[1] + '不在记录里，请确认后再删除', [member.id])
    write_guild(member.group.id, g_data)
    return await reply_group(app, member.group.id, '已将' + sp[0] + '的' + sp[1] + '伤害记录删除', [member.id])


async def export_current_dmg_records(app: Mirai, member: Member, args: str):
    if not await is_battle(app, member):
        return
    if member.permission == Permission.Member:
        return await reply_group(app, member.group.id, '无权限使用此命令，请联系会长或管理', [member.id])
    g_data: dict = read_guild(member.group.id)
    members = g_data['members']
    current_date = current_date_str()
    if len(args) > 0:
        if isVaildDate(args):
            l = args.split('-')
            current_date = '{}-{:0>2s}-{:0>2s}'.format(l[0], l[1], l[2])
        else:
            return await reply_group(app, member.group.id, '格式不合法')
    tmp = '昵称,QQ,已出刀数,合计伤害,完整刀,,,,,,补偿刀/尾刀,,,,,,,,,,,\n'
    count = 0
    for key in members.keys():
        member_info = members[key]
        tmp += member_info['name'] + ',' + key + ','
        if 'records' not in member_info:
            tmp += '0,0,,,,,,,,,,,,,,,,,,,,\n'
        else:
            records = member_info['records']
            if current_date in records:
                record_arr = records[current_date]
                normal_list = []
                tail_list = []
                total_dmg = 0
                for record in record_arr:
                    total_dmg = round(total_dmg + float(record['dmg']), 4)
                    if record['tail'] == 0:
                        count += 1
                        normal_list.append('老' + str(record['boss']) + ',' + str(record['dmg']) + ',')
                        # normal_list.append(str(record['dmg']) + ',')
                    elif record['tail'] == 1:
                        tail_list.append('老' + str(record['boss']) + ',' + str(record['dmg']) + ',')
                        # tail_list.append(str(record['dmg']) + ',')
                tmp += str(len(normal_list)) + ',' + str(total_dmg) + ','
                for i in range(0, 3):
                    if i < len(normal_list):
                        tmp += normal_list[i]
                    else:
                        tmp += ','
                for i in range(0, 6):
                    if i < len(tail_list):
                        tmp += tail_list[i]
                    else:
                        tmp += ','
                tmp += '\n'
            else:
                tmp += '0,0,,,,,,,,,,,,,,,,,,,,\n'
    msg = '公会当前共有 ' + str(len(members)) + ' 个人, ' + current_date + ' 已出刀数 【' + str(count) + '/' + str(
        len(members) * 3) + '】，详情如下：\n'
    msg += tmp
    return await reply_group(app, member.group.id, msg, [member.id])


async def current_dmg_records(app: Mirai, member: Member, args: str):
    if not await is_battle(app, member):
        return
    if member.permission == Permission.Member:
        return await reply_group(app, member.group.id, '无权限使用此命令，请联系会长或管理', [member.id])
    g_data: dict = read_guild(member.group.id)
    members = g_data['members']
    current_date = current_date_str()
    if len(args) > 0:
        if re.match(r'[1-9][0-9]{4,}', args):
            if args in members.keys():
                return await my_dmg_records(app, member, args)
            else:
                return await reply_group(app, member.group.id, args + '还未入会')
        elif isVaildDate(args):
            l = args.split('-')
            current_date = '{}-{:0>2s}-{:0>2s}'.format(l[0], l[1], l[2])
        else:
            return await reply_group(app, member.group.id, '格式不合法')
    tmp = ''
    count = 0
    for key in members.keys():
        member_info = members[key]
        tmp += member_info['name'] + ' '
        if 'records' not in member_info:
            tmp += ' 已出 0/3 刀，合计伤害 0\n'
        else:
            records = member_info['records']
            # print_msg(current_date=current_date)
            if current_date in records:
                record_arr = records[current_date]
                normal_list = []
                tail_list = []
                total_dmg = 0
                for record in record_arr:
                    total_dmg = round(total_dmg + float(record['dmg']), 4)
                    if record['tail'] == 0:
                        count += 1
                        normal_list.append('老' + str(record['boss']) + ' ' + str(record['dmg']))
                        # normal_list.append(str(record['dmg']))
                    elif record['tail'] == 1:
                        tail_list.append('老' + str(record['boss']) + ' ' + str(record['dmg']))
                        # tail_list.append(str(record['dmg']))
                tmp += ' 已出 ' + str(len(normal_list)) + '/3 刀，合计伤害 ' + str(total_dmg) + '\n'
                if len(normal_list) > 0:
                    tmp += '\t完整刀【' + '、'.join(normal_list) + '】 '
                if len(tail_list) > 0:
                    tmp += '\t尾刀/补偿刀【' + '、'.join(tail_list) + '】 '
                tmp += '\n'
            else:
                tmp += ' 已出 0/3 刀，合计伤害 0\n'
    msg = '公会当前共有 ' + str(len(members)) + ' 个人, ' + current_date + ' 已出刀数 【' + str(count) + '/' + str(
        len(members) * 3) + '】，详情如下：\n'
    msg += tmp
    return await reply_group(app, member.group.id, msg, [member.id])


async def all_dmg_records(app: Mirai, member: Member, args: str):
    if not await is_battle(app, member):
        return
    if member.permission == Permission.Member:
        return await reply_group(app, member.group.id, '无权限使用此命令，请联系会长或管理', [member.id])
    g_data: dict = read_guild(member.group.id)
    members = g_data['members']
    msg = '公会当前共有 ' + str(len(members)) + ' 个人, 出刀记录如下：\n'
    for key in members.keys():
        member_info = members[key]
        msg += member_info['name'] + ' '
        if 'records' not in member_info:
            msg += ' 已出 0/3 刀，合计伤害 0\n'
        else:
            records = member_info['records']
            if len(records) == 0:
                msg += ' 已出 0/3 刀，合计伤害 0\n'
            for date_str in records:
                record_arr = records[date_str]
                normal_list = []
                tail_list = []
                total_dmg = 0
                for record in record_arr:
                    total_dmg = round(total_dmg + float(record['dmg']), 4)
                    if record['tail'] == 0:
                        normal_list.append('老' + str(record['boss']) + ' ' + str(record['dmg']))
                        # normal_list.append(str(record['dmg']))
                    elif record['tail'] == 1:
                        tail_list.append('老' + str(record['boss']) + ' ' + str(record['dmg']))
                        # tail_list.append(str(record['dmg']))
                msg += ' 已出 ' + str(len(normal_list)) + '/3 刀，合计伤害 ' + str(total_dmg) + '\n'
                if len(normal_list) > 0:
                    msg += '\t完整刀【' + '、'.join(normal_list) + '】 '
                if len(tail_list) > 0:
                    msg += '\t尾刀/补偿刀【' + '、'.join(tail_list) + '】 '
                msg += '\n'
    return await reply_group(app, member.group.id, msg, [member.id])


async def clear_my_dmg_records(app: Mirai, member: Member, args: str):
    if not await is_battle(app, member):
        return
    g_data: dict = read_guild(member.group.id)
    members = g_data['members']
    current_date = current_date_str()
    if len(args) > 0:
        member_info = members[args]
        msg = members[args]['name'] + '(' + args + ') ' + current_date
    else:
        member_info = members[str(member.id)]
        msg = member_info['name'] + ' ' + current_date
    if 'records' not in member_info:
        msg += ' 还没有出刀记录\n'
    else:
        records = member_info['records']
        if current_date in records:
            record_arr = records[current_date]
            record_arr.clear()
            write_guild(member.group.id, g_data)
        msg += ' 出刀记录已清除\n'
    return await reply_group(app, member.group.id, msg, [member.id])


async def clear_current_dmg_records(app: Mirai, member: Member, args: str):
    if not await is_battle(app, member):
        return
    if member.permission == Permission.Member:
        return await reply_group(app, member.group.id, '无权限使用此命令，请联系会长或管理', [member.id])
    g_data: dict = read_guild(member.group.id)
    members = g_data['members']
    current_date = current_date_str()
    if len(args) > 0:
        if re.match(r'[1-9][0-9]{4,}', args):
            if args in members.keys():
                return await clear_my_dmg_records(app, member, args)
            else:
                return await reply_group(app, member.group.id, args + '还未入会')
        elif isVaildDate(args):
            l = args.split('-')
            current_date = '{}-{:0>2s}-{:0>2s}'.format(l[0], l[1], l[2])
        else:
            return await reply_group(app, member.group.id, '格式不合法')
    tmp = ''
    count = 0
    for key in members.keys():
        member_info = members[key]
        tmp += member_info['name'] + ' '
        if 'records' in member_info:
            records = member_info['records']
            if current_date in records:
                record_arr = records[current_date]
                record_arr.clear()
                count += 1
    write_guild(member.group.id, g_data)
    msg = '本次一共清除了 ' + current_date + ' ' + str(count) + ' 人的出刀记录'
    return await reply_group(app, member.group.id, msg, [member.id])


async def clear_all_dmg_records(app: Mirai, member: Member, args: str):
    if not await is_battle(app, member):
        return
    if member.permission == Permission.Member:
        return await reply_group(app, member.group.id, '无权限使用此命令，请联系会长或管理', [member.id])
    g_data: dict = read_guild(member.group.id)
    members = g_data['members']
    for key in members.keys():
        member_info = members[key]
        if 'records' in member_info:
            records: dict = member_info['records']
            records.clear()
    write_guild(member.group.id, g_data)
    msg = '本次已清除全部历史出刀记录'
    return await reply_group(app, member.group.id, msg, [member.id])


async def update_hp(app, member, arg, index):
    if not await is_battle(app, member):
        return
    guild_data = read_battle(member.group.id)
    boss = guild_data['current_boss_data'][index - 1]
    if check_dmg(arg):
        if arg.endswith('*'):
            arg = arg[:len(arg) - 1]
        if float(arg) > boss['all_hp']:
            return await reply_group(app, member.group.id, '老 ' + str(index) + ' 血量不能超过总血量' + str(boss['all_hp']))
        boss['real_hp'] = float(arg)
        write_battle(member.group.id, guild_data)
        return await reply_group(app, member.group.id, '老 ' + str(index) + ' 血量更新成功')
    else:
        return await reply_group(app, member.group.id, ILLEGAL_ERR, [member.id])


async def update_loop(app, member, arg):
    if not await is_battle(app, member):
        return
    guild_data = read_battle(member.group.id)
    if check_dmg(arg):
        if arg.endswith('*'):
            arg = arg[:len(arg) - 1]
        guild_data['current_loop'] = int(arg)
        write_battle(member.group.id, guild_data)
        return await reply_group(app, member.group.id, '修改圈数成功')
    else:
        return await reply_group(app, member.group.id, ILLEGAL_ERR, [member.id])


async def up_tree(app, member):
    if not await is_battle(app, member):
        return
    guild_data = read_battle(member.group.id)
    if str(member.id) in guild_data['tree_members']:
        return await reply_group(app, member.group.id, '不要重复上树', [member.id])
    guild_data['tree_members'][str(member.id)] = member.memberName
    write_battle(member.group.id, guild_data)
    return await reply_group(app, member.group.id, '上树成功', [member.id])


async def down_tree(app, member, guild_data):
    # if not await is_battle(app, member):
    #     return
    # guild_data = read_battle(member.group.id)
    members = guild_data['tree_members'].keys()
    if len(members) == 0:
        return await reply_group(app, member.group.id, '树上无人')
    await reply_group(app, member.group.id, 'boss已死亡', map(int, members))
    guild_data['tree_members'].clear()
    # pprint(guild_data)
    # write_battle(member.group.id, guild_data)
    # return


async def tree_info(app, member):
    if not await is_battle(app, member):
        return
    guild_data = read_battle(member.group.id)
    members = guild_data['tree_members'].values()
    if len(members) == 0:
        return await reply_group(app, member.group.id, '树上无人')
    msg = '树上有 ' + str(len(members)) + ' 个人，分别是：'
    for name in members:
        msg += name + '、'
    msg = msg[:len(msg) - 1]
    return await reply_group(app, member.group.id, msg)
