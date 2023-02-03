from telegram.ext import Updater, CommandHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import random

# --- Глобальные значения --- #
game_state = False  # true - сейчас идет, false - нет
registration_state = False  # true - сейчас идет, false - нет
players = dict()  # key: ID игрока, значение: объект класса игрок
quantity = 0
used = []
roles = dict()  # Key: роль, значение: ID игрока
mafioso_list = []
reg_message_id = None
game_chat_id = None
last_message_id = dict()  # Key : ID игрока, value: id последнего сообщения

# --- Переменные --- #
BOT_TOKEN = "6061928919:AAHvyBy3C30z4CIwZdCG0HRrhivX_nYoTSw"
REGISTRATION_TIME = 60  # Секунды
REQUIRED_PLAYERS = 1
LEADERS_INNOCENTS = ['Детектив.']
SPECIAL_INNOCENTS = ['Доктор', 'Шлюха']
SPECIAL_MAFIOSI = ['Крестный отец']
OTHERS = ['Маньяк']
'''
    Это словарь, ключи которого — количество игроков, значения — количество ролей:
     каждое значение представляет собой строку, каждая из цифр в которой представляет количество символов каждого типа соответственно:
         1. Лидеры невиновных. Случайным образом выбраны из LEADERS_INNOCENTS.
         2. Простые невиновные
         3. Особые невиновные. Выбрано случайным образом из SPECIAL_INNOCENTS
         4. Простой мафиози
         5. Специальные мафиози. Случайно выбрано из SPECIAL_MAFIOSI
         6. Личности, типа маньяка. Случайно выбрано из OTHERS
'''
QUANTITY_OF_ROLES = {1: '0 0 0 1 0 0', 2: '1 0 0 1 0 0', 3: '1 1 0 1 0 0', 4: '1 1 0 2 0 0', 5: '1 2 0 2 0 0',
                     6: '1 3 0 2 0 0', 7: '1 2 1 3 0 0', 8: '1 3 1 2 1 0', 9: '1 3 1 3 1 0', 10: '1 3 1 3 1 1',
                     11: '1 5 1 2 1 1', 12: '1 5 2 2 1 1', 13: '1 6 2 2 1 1', 14: '1 6 2 3 1 1', 15: '1 7 2 3 1 1',
                     16: '1 7 2 4 1 1'}
ROLES_PRIORITY = ['Шлюха', 'Доктор', 'Тварь из бестиария (мафия)', 'Детектив', 'Маньяк', 'Крестный отец', 'Мирный житель']
ROLE_GREETING = {
    "Детектив": '\n'.join(["Ты - детектив Сунь Хуй в чай и вынь сухим. Твоя цель спасти мирный город от жестоких и кровожадных мафиози.",
                            "Ночью ты можешь проверить чью-то карту или убить кого-то.",
                            "Удачи, Детектив, спаси мир гомеSSSов от тварей из бестиария."]),
    "Доктор": '\n'.join(["Мир не захватила неизвестная болезнь, а всего лишь пара тварей из бестиария вырвалась на свободу и ты - единственный, кто может спасти всех.",
                         "Твоя способность - вколоть противоядие одному гомеSSSу за ночь. ",
                         "Удачи, Доктор, и Бога нет!"]),
    "Шлюха": '\n'.join(["Ты - проститутка местного разлива",
                             "Твоя цель остаться в живых и помогать гомеsssам.",
                             "Твоя особая способность - вывести из строя одного игрока на один раунд в течение ночи.",
                             "Удачи в этом непростом  деле."]),
    "Крестный отец": '\n'.join(["Ты - крестный отец Дон Корлеоне; к тебе приходили в день свадьбы твоей дочери и просили о помощи, но делали это без уважения, не предлагали дружбу, даже не думали обратиться к тебе - Крестный, а лишь прихоидили и просили убивать за деньги. Тебе это все надоело и ты создал монстров.",
                            "Твоя цель уничтожить гомеsssов и помочь тварям из бестирария.",
                            "Твоя особая способность - отключить одного игрока в качестве избирателя..",
                            "Удачи, Крестный отец, никогда не показывай посторонним, что у тебя на уме. Никогда не раскрывай перед чужими свои карты."]),
    "Маньяк": '\n'.join(["Ты - маньяк, сбежавший из лаборатории крестного отца.",
                         "Ты можешь убить одного игрока за ночь.",
                         "Удачи, Маньяк, и да прибудет с тобой сила."]),
    "ГомеSSS": '\n'.join(["Ты = Гомеsss. Существо дня, а ночью ты спишь, тут без вариантов.",
                           "Твоя цель - уничтожить тварей из бестиария в нашем мире.",
                           "Удачи, ГомеSSS, и да востаржествует мир без гномиков, гомиков, нефоров и прочих."]),
    "Тварь из бестиария": '\n'.join(["Ты - тварь из бестиария. Твоя способность - убить одного игрока за ночь.",
                          "Однако, помни, что сотрудничество с другими тварями имеет для Вас решающее значение.",
                          "Желаю удачи, тварь!"])}

updater = Updater(token=BOT_TOKEN)
dispatcher = updater.dispatcher


class Player:
    def __init__(self, user):
        self.ID = user.id
        self.name = user.first_name + (' ' + user.last_name if user.last_name else '')
        self.nick = user.username
        self.card = None
        self.is_alive = True
        self.is_abilities_active = True
        self.can_be_killed = True
        self.able_to_vote = True
        self.able_to_discuss = True
        self.chat_id = None


def distribute_roles():
    global roles
    global players
    global QUANTITY_OF_ROLES
    global LEADERS_INNOCENTS
    global SPECIAL_MAFIOSI
    global SPECIAL_INNOCENTS
    global OTHERS
    global quantity
    global mafioso_list

    print('Распределение ролей...')

    roles_q = list(map(int, QUANTITY_OF_ROLES[quantity].split(' ')))

    leaders_innocents = random.sample(LEADERS_INNOCENTS, roles_q[0])
    special_innocents = random.sample(SPECIAL_INNOCENTS, roles_q[2])
    special_mafiosi = random.sample(SPECIAL_MAFIOSI, roles_q[4])
    others = random.sample(OTHERS, roles_q[5])

    rand_players = [i.ID for i in players.values()]
    random.shuffle(rand_players)

    ind = 0
    for i in range(len(leaders_innocents)):
        players[rand_players[ind]].card = leaders_innocents[i].capitalize()
        roles[leaders_innocents[i].capitalize()] = rand_players[ind]
        ind += 1

    for i in range(len(special_innocents)):
        players[rand_players[ind]].card = special_innocents[i].capitalize()
        roles[special_innocents[i].capitalize()] = rand_players[ind]
        ind += 1

    for i in range(len(special_mafiosi)):
        players[rand_players[ind]].card = special_mafiosi[i].capitalize()
        roles[special_mafiosi[i].capitalize()] = rand_players[ind]
        ind += 1

    for i in range(len(others)):
        players[rand_players[ind]].card = others[i].capitalize()
        roles[others[i].capitalize()] = rand_players[ind]
        ind += 1

    roles['ГомеSSS'] = []
    for i in range(roles_q[1]):
        players[rand_players[ind]].card = 'ГомеSSS'
        roles['ГомеSSS'].append(rand_players[ind])
        ind += 1

    roles['Тварь из бестиария'] = []
    for i in range(roles_q[3]):
        players[rand_players[ind]].card = 'Тварь из бестиария'
        roles['Тварь из бестиария'].append(rand_players[ind])
        mafioso_list.append(
            '[' + players[rand_players[ind]].name + ']' + '(tg://user?id=' + str(rand_players[ind]) + ')')
        ind += 1

        print('Распределение ролей завершено: ')
        for key, value in roles.items():
            if key == 'Тварь из бестиария':
                print('Тварь из бестиария: {}'.format(', '.join([players[i].name for i in value])))
            elif key == 'ГомеSSS':
                print('ГомеSSS: {}'.format(', '.join([players[i].name for i in value])))
            else:
                print(key + ': ' + players[value].name)

  # Эти ifs предназначены для отладки, т.к. ситуация без мафиози/невиновных запрещена правилами
    if not roles['Тварь из бестиария']:
        del roles['Тварь из бестиария']

    if not roles['ГомеSSS']:
        del roles['ГомеSSS']


def send_roles(bot):
    global roles
    global mafioso_list
    global players
    global ROLE_GREETING
    global last_message_id

    print('Отправка ролей...')

    for role, player in roles.items():
        if role == 'Тварь из бестиария':
            for pl in player:
                bot.send_message(chat_id=pl, text=ROLE_GREETING[role])
                if len(mafioso_list) > 1:
                    bot.send_message(chat_id=pl, text='Остальные мафии: \n{}'.format(
                        '\n'.join(i for i in mafioso_list if not (str(pl) in i))),
                                     parse_mode='Markdown')
                last_message_id[pl] += 1
        elif role == 'ГомеSSS':
            for pl in player:
                bot.send_message(chat_id=pl, text=ROLE_GREETING[role])
                last_message_id[pl] += 1
        else:
            bot.send_message(chat_id=player, text=ROLE_GREETING[role])
            last_message_id[player] += 1

    print('Роли разосланы успешно.')


# Ролевые функции
# ВАЖНО: имя функционирует как роль, в нижнем регистре
def detective(bot):
    global roles
    global players

    print('Детектив вышел в ночную смену.')

    check_or_shoot = InlineKeyboardMarkup(
        [[InlineKeyboardButton('Убийство', callback_data='detective_shoot'),
          InlineKeyboardButton('CПроверить карту', callback_data='detective_check')]])

    bot.send_message(chat_id=roles['Детектив'], text='Ты чувствуешь себя пацифистом сегодня?',
                     reply_markup=check_or_shoot)
    last_message_id[roles['Детектив']] += 1


def mafioso(bot):
    global roles
    global players
    global mafioso_list

    print('Твари из бестиария вышли на охоту.')

    shoot_voting = []
    for role, _id in roles.items():
        if role == 'ГомеSSS':
            for inn in _id:
                shoot_voting.append([InlineKeyboardButton(players[inn].name, callback_data='maf_kill:{}'.format(inn))])
        elif role != 'Mafioso':
            shoot_voting.append([InlineKeyboardButton(players[_id].name, callback_data='maf_kill:{}'.format(_id))])

    for i in roles['Тварь из бестиария']:
        bot.send_message(chat_id=i, text='Выбирай цель правильно.',
                         reply_markup=InlineKeyboardMarkup(shoot_voting))
        last_message_id[i] += 1


def innocent():
    print('ГомеSSSы ещё спят как котёночки!')


# Main
def game(bot, chat_id):
    global game_state
    global players
    global roles
    global ROLES_PRIORITY

    game_state = True
    print('Рыба, карась - игра началась!')
    bot.send_message(chat_id=chat_id, text='Игра запущена. И пусть победит сильнейший.')

    distribute_roles()
    send_roles(bot)

    ordered_roles = sorted(roles.keys(),
                           key=lambda x: ROLES_PRIORITY.index(x.lower()))

    for i in ordered_roles:
        exec(i.lower() + '(bot)')  # функции для каждой роли называются так же, как и сами роли


# Игра начинается с /game
def registration_command(bot, update):
    global game_state
    global quantity
    global registration_state
    global players
    global reg_message_id
    global game_chat_id

    if not (game_state or registration_state):
        bot.send_message(chat_id=update.message.chat_id, text='И пусть шансы всегда будут в вашу пользу')
        registration_state = True

        keyboard = [[InlineKeyboardButton('Регистрация', url="https://t.me/goodgoosebot?start=Register")]]
        msg_markup = InlineKeyboardMarkup(keyboard)

        reg_message_id = update.message.message_id + 2
        game_chat_id = update.message.chat_id
        bot.send_message(chat_id=update.message.chat_id, text='*Регистрация началась!*',
                         parse_mode="Markdown", reply_markup=msg_markup)

        bot.pin_chat_message(chat_id=update.message.chat_id, message_id=reg_message_id, disable_notification=True)
    else:
        bot.send_message(chat_id=update.message.chat_id, text='В настоящее время работает')


# On '/stop'
def stop_command(bot, update):
    global game_state
    global registration_state
    global quantity
    global players
    global mafioso_list
    global roles
    global reg_message_id
    global registration_state

    if game_state or registration_state:
        bot.send_message(chat_id=update.message.chat_id, text='¡Sí, señor!')

        if registration_state:
            bot.delete_message(chat_id=update.message.chat_id, message_id=reg_message_id)
            bot.delete_message(chat_id=update.message.chat_id, message_id=reg_message_id - 1)

        game_state = False
        registration_state = False

        quantity = 0
        players.clear()
        roles.clear()
        used.clear()
        mafioso_list.clear()

        bot.send_message(chat_id=update.message.chat_id, text='Игра успешно прервана.')
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Нет активных игр для остановки')


# On '/start'
def reg_player_command(bot, update):
    global registration_state
    global quantity
    global reg_message_id
    global game_chat_id
    global last_message_id

    if registration_state:
        new_user = Player(update.message.from_user)

        if new_user.ID in used:
            bot.send_message(chat_id=update.message.chat_id,
                             text='Ты уже зарегистрирован, ожидай других игроков.')
            return

        players[new_user.ID] = new_user
        quantity += 1

        print('Player {}: {}, {}'.format(quantity, new_user.name, new_user.ID))

        last_message_id[new_user.ID] = update.message.message_id
        used.append(new_user.ID)

        keyboard = [[InlineKeyboardButton('Зарегистрироваться!', url="https://t.me/goodgoosebot?start=Register")]]
        msg_markup = InlineKeyboardMarkup(keyboard)

        bot.edit_message_text(chat_id=game_chat_id, message_id=reg_message_id,
                              text='Registration is active!\n\n*Registered players:* \n{}\n\nTotal: *{}*'.format(
                                  ', '.join(
                                      ['[' + i.name + ']' + '(tg://user?id=' + str(i.ID) + ')' for _, i in
                                       players.items()]),
                                  str(quantity)), parse_mode="Markdown", reply_markup=msg_markup)
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text='Регистрация еще не начата. Введи /game, чтобы запустить регистрацию.')


# On '/begin_game'
def begin_game_command(bot, update):
    global quantity
    global registration_state
    global game_state
    global REQUIRED_PLAYERS
    global reg_message_id

    if game_state:
        bot.send_message(chat_id=update.message.chat_id, text='Игра уже запущена!')
        return

    if registration_state:
        if quantity >= REQUIRED_PLAYERS:
            bot.send_message(chat_id=update.message.chat_id,
                             text='Регистрация окончена. Запускаем игру...')
            registration_state = False

            bot.delete_message(chat_id=update.message.chat_id, message_id=reg_message_id)
            bot.delete_message(chat_id=update.message.chat_id, message_id=reg_message_id - 1)

            game(bot, update.message.chat_id)
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text='\n'.join(['Слишком мало игроков.',
                                             'Количество зарегистрированных игроков: {}'.format(quantity),
                                             'Минимум игроков {}.'.format(REQUIRED_PLAYERS)]))
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Введи /game, чтобы начать регистрацию.')


game_command_handler = CommandHandler('game', registration_command)
stop_command_handler = CommandHandler('stop', stop_command)
reg_command_handler = CommandHandler('start', reg_player_command)
start_command_handler = CommandHandler('begin_game', begin_game_command)

dispatcher.add_handler(game_command_handler)
dispatcher.add_handler(stop_command_handler)
dispatcher.add_handler(reg_command_handler)
dispatcher.add_handler(start_command_handler)

updater.start_polling(clean=True)
