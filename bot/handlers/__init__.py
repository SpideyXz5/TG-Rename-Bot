from bot.handlers import (
    start,
    thumbnail,
    rename,
    settings_menu,
    settings_forcesub,
    settings_shortener,
    settings_rename,
    settings_admin,
    stats,
)

# Order matters: settings/admin routers first so FSM-state text handlers for
# admin input flows take priority over the generic file/photo handlers.
all_routers = [
    settings_menu.router,
    settings_forcesub.router,
    settings_shortener.router,
    settings_rename.router,
    settings_admin.router,
    stats.router,
    start.router,
    thumbnail.router,
    rename.router,
]
