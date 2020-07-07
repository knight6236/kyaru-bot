import yaml
from mirai import Mirai, MessageChain, Member, Plain

import gl
from plugin import load_plugins
from plugins.group_msg import handle_group_msg

f = open('config/bot.yaml', encoding="utf-8")
cfg = yaml.load(f, Loader=yaml.FullLoader)

bot = Mirai(f"{cfg['host']}?authKey={cfg['authKey']}&qq={cfg['qq']}", websocket={cfg['enableWebsocket']})

gl.init()
gl.setK('bot', bot)


@bot.receiver("GroupMessage")
async def event_gm(app: Mirai, member: Member, message: MessageChain):
    plains = message.getAllofComponent(Plain)
    if len(plains) == 0:
        return

    msg = ''
    for plain in plains:
        msg += plain.toString().strip() + ' '
    msg = msg.strip()
    if msg == '':
        return

    if member.id == 623697643 and '更新插件' == msg:
        plugin_set = load_plugins(reload=True)
        print(len(plugin_set))
        if plugin_set:
            return await app.sendGroupMessage(member.group.id, [Plain(text='更新插件成功！')])
        else:
            return await app.sendGroupMessage(member.group.id, [Plain(text='更新插件失败！')])

    await handle_group_msg(app, member, message)


if __name__ == "__main__":
    plugin_set = load_plugins()
    print(len(plugin_set))
    bot.run()
