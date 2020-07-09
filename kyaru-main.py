import yaml
from mirai import Mirai, Member, MessageChain, Plain

import gl
from plugin import load_plugins
import plugins

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
        plugins_set = load_plugins(reload=True)
        return await app.sendGroupMessage(member.group.id, [Plain(text='本次更新' + str(len(plugins_set)) + '个插件')])

    await plugins.group_msg.handle_group_msg(app, member, message)


if __name__ == "__main__":
    plugin_set = load_plugins()
    print('初始化插件数：' + str(len(plugin_set)))
    bot.run()
