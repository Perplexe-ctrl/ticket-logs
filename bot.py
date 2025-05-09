import discord
from discord.ext import commands, tasks
from itertools import cycle
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
import logging
import random
from discord import app_commands

# ЛОГИ
logging.basicConfig(
    filename='bot.log',
    level=logging.ERROR,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

invite_cache = {}

class RematchBot(commands.Bot):
    async def setup_hook(self):
        guild = discord.Object(id=1279116363482271795)

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True
intents.voice_states = True
intents.presences = True

bot = commands.Bot(command_prefix='*', help_command=None, intents=intents)

VOICE_CHANNEL_ID = 1356026013078786108
WELCOME_CHANNEL_ID = 1351542350593261588

VOICE_CHANNEL_IDS = [
    1350120081429889126, 1357378273906000044, 1350448152959913985,
    1357362914964537584, 1354508372807782522, 1359242708404797470, 1360302283622977576,
    1362542814172287067, 1362501619098321158, 1361414534765609082, 1359481653894058107,
    1351961742862717041, 1364258739976147156, 1364545782279307284, 1364549049432146022,
    1364551410183831572, 1364598402972782706, 1364915091463602196, 1365012332383830327,
    1365046397614952510, 1365294575698317464, 1365379068475998330, 1365753451048468622,
    1365775949869875293, 1366065531324727368, 1368197162567073823, 1368299467157012533,
    1368560528049311895, 1368697560193044591
]
HIDDEN_FROM_ROLE_ID = 1279120472776249364
ALWAYS_VISIBLE_ROLE_ID = 1279116678998786121

@tasks.loop(seconds=10)
async def update_voice_channel_visibility():
    guild = bot.get_guild(1279116363482271795)
    if not guild:
        return

    for channel_id in VOICE_CHANNEL_IDS:
        channel = guild.get_channel(channel_id)
        if not channel or not isinstance(channel, discord.VoiceChannel):
            continue

        members = channel.members
        visible_to_always = any(
            ALWAYS_VISIBLE_ROLE_ID in [role.id for role in m.roles]
            for m in members
        )

        overwrite = channel.overwrites_for(guild.get_role(HIDDEN_FROM_ROLE_ID))

        if members or visible_to_always:
            if overwrite.view_channel is False:
                overwrite.view_channel = True
                await channel.set_permissions(guild.get_role(HIDDEN_FROM_ROLE_ID), overwrite=overwrite)
                print(f"🔓 Открыл {channel.name}")
        else:
            if overwrite.view_channel is not False:
                overwrite.view_channel = False
                await channel.set_permissions(guild.get_role(HIDDEN_FROM_ROLE_ID), overwrite=overwrite)
                print(f"🔒 Спрятал {channel.name}")


STATUS_LIST = cycle([
    "❤️ t.me/rematch_cis",
    "🧡 discord.gg/rematch-cis",
    "💛 vk.com/rematch_cis",
    "💚 tiktok.com/@rematchcis",
    "🩵 youtube.com/@rachillbl",
])

@tasks.loop(seconds=15)
async def update_status():
    current_status = next(STATUS_LIST)
    await bot.change_presence(activity=discord.CustomActivity(name=current_status), status=discord.Status.online)

@tasks.loop(seconds=30)
async def update_voice_channel_name():
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if not channel or not isinstance(channel, discord.VoiceChannel):
        print("❌ Голосовой канал не найден или не является голосовым.")
        return

    member_count = len([m for m in channel.guild.members if not m.bot])
    new_name = f"⚽・Рематчеры: {member_count}"

    try:
        await channel.edit(name=new_name)
        print(f"✅ Название обновлено: {new_name}")
    except Exception as e:
        print(f"❌ Ошибка при обновлении канала: {e}")

@bot.event
async def on_invite_create(invite):
    invite_cache[invite.guild.id] = await invite.guild.invites()

def create_custom_embed(title, description, color=discord.Color.blurple(),
                        image_url=None, thumbnail_url=None, footer_text=None, footer_icon_url=None,
                        author_name=None, author_icon_url=None):
    embed = discord.Embed(title=title, description=description, color=color)
    if author_name:
        embed.set_author(name=author_name, icon_url=author_icon_url)
    if image_url:
        embed.set_image(url=image_url)
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    if footer_text:
        embed.set_footer(text=footer_text, icon_url=footer_icon_url)
    return embed

@bot.command(name="сервер")
async def server_info(ctx):
    guild = ctx.guild
    statuses = {
        discord.Status.online: 0,
        discord.Status.idle: 0,
        discord.Status.dnd: 0,
        discord.Status.offline: 0
    }

    for member in guild.members:
        if member.bot:
            continue
        status = member.status
        if status in statuses:
            statuses[status] += 1

    humans = len([m for m in guild.members if not m.bot])
    bots = len([m for m in guild.members if m.bot])
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    forum_channels = len([c for c in guild.channels if isinstance(c, discord.ForumChannel)])
    stage_channels = len([c for c in guild.channels if isinstance(c, discord.StageChannel)])
    announcement_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel) and c.is_news()])

    embed = discord.Embed(
        title=f"Информация о сервере {guild.name}",
        color=discord.Color.orange(),
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

    embed.add_field(name="Участники:", value=f"<a:BOOBA:1352014883004092497> Всего: {guild.member_count}\n <:98094pepe:1352015686142001214> Людей: {humans}\n<:1646discordboten:1354499349828210958> Ботов: {bots}", inline=True)
    embed.add_field(
        name="По статусам:",
        value=(
            f"<:6951_Online:1355178933875638565> В сети: {statuses[discord.Status.online]}\n"
            f"<:7152_Idle:1355178936555798711> Неактивен: {statuses[discord.Status.idle]}\n"
            f"<:Offline:1355178939240419378> Не беспокой: {statuses[discord.Status.dnd]}\n"
            f"⚫ Не в сети: {statuses[discord.Status.offline]}"
        ),
        inline=True
    )
    embed.add_field(
        name="Каналы:",
        value=(
            f"<:1245sapo:1352015635990843563> Всего: {len(guild.channels)}\n"
            f"<a:chatting:1366873357974241363> Текстовых: {text_channels}\n"
            f"<a:6623_Bell:1355178909645148333> Объявлений: {announcement_channels}\n"
            f"<:59130pepemute:1352015646300442715> Голосовых: {voice_channels}\n"
            f"<:63011pepesip:1352016601469419621> Форумов: {forum_channels}\n"
            f"<:basedge:1366873360910254093> Трибун: {stage_channels}"
        ),
        inline=True
    )
    embed.add_field(name="<:pepeKingSip:1366873400341037187> Владелец:", value=guild.owner.mention, inline=True)
    embed.add_field(name="<:3446blurplecertifiedmoderator:1354499353326387221> Уровень проверки:", value=str(guild.verification_level).capitalize(), inline=True)
    created = guild.created_at.strftime("%d %B %Y г.")
    delta = datetime.now(timezone.utc) - guild.created_at
    embed.add_field(name="<:72453pepecoffee:1354501891719172216> Дата создания:", value=f"{created}\n{delta.days // 30} месяцев назад", inline=True)
    embed.set_image(url="https://i.postimg.cc/TP36dy6w/08af50a5d5b4903c.gif")
    embed.set_footer(text=f"ID: {guild.id} • Звено: #224 (Dixie)")

    await ctx.send(embed=embed)




WELCOME_MESSAGES = [
    'Добро пожаловать в REMATCH CIS',
    'Добро пожаловать в место, где поражение — лишь повод к реваншу!',
    'Легенды рождаются здесь. Добро пожаловать на REMATCH CIS',
    'Одна искра — и мир охвачен пламенем. Привет!',
    'Ты выбрал не просто сервер. Ты выбрал путь.',
    'Пепел битв ещё не остыл. Входи.',
    'Привет! Чат не кусается. Обычно.',
    'Добро пожаловать! Надеемся, у тебя есть мемы.',
    'Ты пришёл с миром? Или с багами?',
    'Осторожно, тут обитают токсики… Шутка! Или нет.',
    'Тут все проигрывали… кроме тебя. Пока.',
    'Новенький! Надеюсь, ты умеешь проигрывать красиво.',
    'Привет! Надеюсь, у тебя есть микрофон и чувство юмора.',
    'Ура! Новый друг в REMATCH!',
    'Добро пожаловать! Чувствуй себя как дома.',
    'Приятно познакомиться! Пиши, не стесняйся.',
    'Хэй! Рад тебя видеть тут!',
    'Привет-привет! Рассказывай, как попал к нам?',
    'REMATCH + ты = 🔥',
    'Эй! Рад, что ты с нами!',
    'Ну наконец-то! Мы тебя ждали!',
    'REMATCH стал лучше с твоим приходом!',
    'Легенда присоединилась!',
    'Тот, о ком слагали песни, присоединился!',
    'Новый участник — новая история.',
    'Даже сервер почувствовал твоё прибытие.',
    'REMATCH CIS — теперь ты его часть.',
    'Добро пожаловать, чемпион будущих матчей!'
]

class WelcomeButtons(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(label="Правила", url="https://discord.com/channels/1279116363482271795/1279118080181665934", emoji=discord.PartialEmoji(name="animated_emoji", id=1351993005997031576, animated=True)))
        self.add_item(discord.ui.Button(label="Навигатор", url="https://discord.com/channels/1279116363482271795/1279119360782237832", emoji=discord.PartialEmoji(name="animated_emoji", id=1355179047839072446, animated=True)))
        self.add_item(discord.ui.Button(label="Новости Игры", url="https://discord.com/channels/1279116363482271795/1279118238655058001", emoji=discord.PartialEmoji(name="animated_emoji", id=1355178909645148333, animated=True)))

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if not channel:
        print("❌ Приветственный канал не найден.")
        return

    quote = random.choice(WELCOME_MESSAGES)
    avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
    color = discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    profile_url = f"https://discord.com/users/{member.id}"

    embed = discord.Embed(color=color)
    embed.set_author(name=f"{member.display_name} | {quote}", url=profile_url, icon_url=avatar_url)
    embed.set_image(url="https://i.postimg.cc/qRJc0Xby/391eb3a7701f6aae.png")
    embed.set_footer(text=datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M"))
    await channel.send(content=member.mention, embed=embed, view=WelcomeButtons())
    print(f"✅ Приветствие отправлено для {member.display_name}")


@bot.event
async def on_ready():
    print(f"🟢 Бот {bot.user} успешно запущен.")

    extensions = [
        "cogs.audit",
        "cogs.moderation",
        "cogs.translater",
        "cogs.invites",
        "cogs.status",
        "cogs.giveaway",
        "cogs.auto_publish",
        "cogs.levels",
        "cogs.autothread",
        "cogs.help",
        "cogs.fun",
        "cogs.twitch",
        "cogs.tickets"
    ]

    for ext in extensions:
        try:
            await bot.load_extension(ext)
            print(f"✅ Загружен Cog: {ext}")
        except Exception as e:
            print(f"❌ Ошибка при загрузке Cog {ext}: {e}")

    if not update_status.is_running():
        update_status.start()
    if not update_voice_channel_name.is_running():
        update_voice_channel_name.start()

    if not update_voice_channel_visibility.is_running():
        update_voice_channel_visibility.start()


if not TOKEN:
    print("❌ Токен не найден! Проверь .env файл.")
else:
    bot.run(TOKEN)
