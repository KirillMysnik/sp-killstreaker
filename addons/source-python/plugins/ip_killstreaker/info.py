from cvars.public import PublicConVar
from plugins.info import PluginInfo


info = PluginInfo()
info.name = "iPlayer's Killstreaker"
info.basename = 'ip_killstreaker'
info.author = 'Kirill "iPlayer" Mysnik'
info.version = '1.0'
info.variable = 'ipk_version'
info.convar = PublicConVar(
    info.variable, info.version, "{} version".format(info.name))

info.url = "https://github.com/KirillMysnik/sp-killstreaker"
