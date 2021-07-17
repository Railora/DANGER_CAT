"""Make / Download Telegram Sticker Packs without installing Third Party applications
Available Commands:
.steal [Optional Emoji]
.getsticker"""
import asyncio
import datetime
import math
import os
import zipfile
from collections import defaultdict
from io import BytesIO

from PIL import Image
from telethon.errors import MessageNotModifiedError
from telethon.errors.rpcerrorlist import StickersetInvalidError
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import (
    DocumentAttributeSticker,
    InputStickerSetShortName,
    MessageMediaPhoto,
)

from userbot import catub

from . import ALIVE_NAME

DEFAULTUSER = str(ALIVE_NAME) if ALIVE_NAME else "Cat"
FILLED_UP_DADDY = "Invalid pack selected."

plugin_category = "fun"


@catub.cat_cmd(
    pattern="steal(?:\s|$)([\s\S]*)",
    command=("steal", plugin_category),
    info={
        "header": "To kang a sticker.",
        "description": "Kang's the sticker/image to the specified pack and uses the emoji('s) you picked",
        "usage": "{tr}kang [emoji('s)] [number]",
    },
)
async def _(event):
    if event.fwd_from:
        return
    if not event.is_reply:
        await event.edit(
            "Reply to a photo to add to my personal sticker pack.**( ఠ ͟ʖ ఠ)**"
        )
        return
    reply_message = await event.get_reply_message()
    sticker_emoji = "🔥"
    input_str = event.pattern_match.group(1)
    if input_str:
        sticker_emoji = input_str

    user = await bot.get_me()
    if not user.first_name:
        user.first_name = user.id
    if not user.username:
        user.username = user.id
    pack = 1
    userid = event.sender_id
    packname = f"{user.first_name}'s @{user.username} Vol.{pack}"
    if userid == 1118936839:
        packshortname = f"Sarath_Survivor{userid}"
    else:
        packshortname = f"{user.username}_{pack}_{user.id}"
    await event.edit(
        "`Look dat way,it's a gurl!\n`Meanwhile, lemme kang this stcker over hehe`"
    )

    is_a_s = is_it_animated_sticker(reply_message)
    file_ext_ns_ion = "Survivor_Sticker.png"
    file = await borg.download_file(reply_message.media)
    uploaded_sticker = None
    if is_a_s:
        file_ext_ns_ion = "AnimatedSticker.tgs"
        uploaded_sticker = await borg.upload_file(file, file_name=file_ext_ns_ion)
        packname = f"{user.first_name}'s Animated {pack}"
        if userid == 1118936839:
            packshortname = f"Survivor_Animated"
        else:
            packshortname = (
                f"{user.username}_animated_{pack}_{user.id}"  # format: Uni_Borg_userid
            )
    elif not is_message_image(reply_message):
        await event.edit("Invalid message type")
        return
    else:
        with BytesIO(file) as mem_file, BytesIO() as sticker:
            resize_image(mem_file, sticker)
            sticker.seek(0)
            uploaded_sticker = await borg.upload_file(
                sticker, file_name=file_ext_ns_ion
            )

    async with borg.conversation("@Stickers") as bot_conv:
        now = datetime.datetime.now()
        dt = now + datetime.timedelta(minutes=1)
        if not await stickerset_exists(bot_conv, packshortname):
            await event.edit("`Brewing a new pack! ヽ(´▽｀)ノ`")
            await silently_send_message(bot_conv, "/cancel")
            if is_a_s:
                response = await silently_send_message(bot_conv, "/newanimated")
            else:
                response = await silently_send_message(bot_conv, "/newpack")
            if "Yay!" not in response.text:
                await event.edit(f"**FAILED**! @Stickers replied: {response.text}")
                return
            response = await silently_send_message(bot_conv, packname)
            if not response.text.startswith("Alright!"):
                if "unacceptable" in response.text:
                    packname = f"{user.id}'s @{user.username} Vol.{pack}"
                    response = await silently_send_message(bot_conv, packname)
                else:
                    await event.edit(f"**FAILED**! @Stickers replied: {response.text}")
            w = await bot_conv.send_file(
                file=uploaded_sticker, allow_cache=False, force_document=True
            )
            response = await bot_conv.get_response()
            if "Sorry" in response.text:
                await event.edit(f"**FAILED**! @Stickers replied: {response.text}")
                return
            await silently_send_message(bot_conv, sticker_emoji)
            await silently_send_message(bot_conv, "/publish")
            response = await silently_send_message(bot_conv, f"<{packname}>")
            await silently_send_message(bot_conv, "/skip")
            response = await silently_send_message(bot_conv, packshortname)
            if response.text == "Sorry, this short name is already taken.":
                await event.edit(f"**FAILED**! @Stickers replied: {response.text}")
                return
            elif response.text == "Sorry, this short name is unacceptable.":
                packshortname = f"pack_{pack}_sticker_{user.id}"
                await silently_send_message(bot_conv, packshortname)
        else:
            await silently_send_message(bot_conv, "/cancel")
            await silently_send_message(bot_conv, "/addsticker")
            await silently_send_message(bot_conv, packshortname)
            await bot_conv.send_file(
                file=uploaded_sticker, allow_cache=False, force_document=True
            )
            response = await bot_conv.get_response()
            if response.text == FILLED_UP_DADDY:
                while response.text == FILLED_UP_DADDY:
                    pack += 1
                    prevv = int(pack) - 1
                    packname = f"{user.first_name}'s @{user.username} Vol.{pack}"
                    packshortname = f"{user.username}_{pack}_{user.id}"
                    if not await stickerset_exists(bot_conv, packshortname):
                        await event.edit(
                            "**Pack No. **"
                            + str(prevv)
                            + "** full! Making a new Pack, Vol. **"
                            + str(pack)
                        )
                        if is_a_s:
                            response = await silently_send_message(
                                bot_conv, "/newanimated"
                            )
                        else:
                            response = await silently_send_message(bot_conv, "/newpack")
                        if "Yay!" not in response.text:
                            await event.edit(
                                f"**FAILED**! @Stickers replied: {response.text}"
                            )
                            return
                        response = await silently_send_message(bot_conv, packname)
                        if not response.text.startswith("Alright!"):
                            if "unacceptable" in response.text:
                                packname = f"{user.id}'s @{user.username} Vol.{pack}"
                                response = await silently_send_message(
                                    bot_conv, packname
                                )
                            else:
                                await event.edit(
                                    f"**FAILED**! @Stickers replied: {response.text}"
                                )
                        w = await bot_conv.send_file(
                            file=uploaded_sticker,
                            allow_cache=False,
                            force_document=True,
                        )
                        response = await bot_conv.get_response()
                        if "Sorry" in response.text:
                            await event.edit(
                                f"**FAILED**! @Stickers replied: {response.text}"
                            )
                            return
                        await silently_send_message(bot_conv, sticker_emoji)
                        await silently_send_message(bot_conv, "/publish")
                        response = await silently_send_message(
                            bot_conv, f"<{packname}>"
                        )
                        await silently_send_message(bot_conv, "/skip")
                        response = await silently_send_message(bot_conv, packshortname)
                        if response.text == "Sorry, this short name is already taken.":
                            await event.edit(
                                f"**FAILED**! @Stickers replied: {response.text}"
                            )
                            return
                        elif response.text == "Sorry, this short name is unacceptable.":
                            packshortname = f"pack_{pack}_sticker_{user.id}"
                            await silently_send_message(bot_conv, packshortname)
                    else:
                        await event.edit(
                            "Pack No. "
                            + str(prevv)
                            + " full! Switching to Vol. "
                            + str(pack)
                        )
                        await silently_send_message(bot_conv, "/addsticker")
                        await silently_send_message(bot_conv, packshortname)
                        await bot_conv.send_file(
                            file=uploaded_sticker,
                            allow_cache=False,
                            force_document=True,
                        )
                        response = await bot_conv.get_response()
                        if "Sorry" in response.text:
                            await event.edit(
                                f"**FAILED**! @Stickers replied: {response.text}"
                            )
                            return
                        await silently_send_message(bot_conv, sticker_emoji)
                        await silently_send_message(bot_conv, "/done")
            else:
                if "Sorry" in response.text:
                    await event.edit(f"**FAILED**! @Stickers replied: {response.text}")
                    return
                await silently_send_message(bot_conv, response)
                await silently_send_message(bot_conv, sticker_emoji)
                await silently_send_message(bot_conv, "/done")

    await event.edit(
        f"**Kanged!** `This sticker has been stolen to` [⚡Here⚡](t.me/addstickers/{packshortname}), `pack` {pack}"
        f" `by` {DEFAULTUSER}\n`Sticker Emoji` {sticker_emoji}"
    )


@catub.cat_cmd(pattern="getsticker ?([\s\S]*)", command=("getsticker", plugin_category))
async def _(event):
    if event.fwd_from:
        return
    event.pattern_match.group(1)
    if not os.path.isdir(Config.TMP_DOWNLOAD_DIRECTORY):
        os.makedirs(Config.TMP_DOWNLOAD_DIRECTORY)
    if event.reply_to_msg_id:
        reply_message = await event.get_reply_message()
        # https://gist.github.com/udf/e4e3dbb2e831c8b580d8fddd312714f7
        if not reply_message.sticker:
            return
        sticker = reply_message.sticker
        sticker_attrib = find_instance(sticker.attributes, DocumentAttributeSticker)
        if not sticker_attrib.stickerset:
            await event.reply("This sticker is not part of a pack")
            return
        is_a_s = is_it_animated_sticker(reply_message)
        file_ext_ns_ion = "webp"
        file_caption = "By CatUserbot"
        if is_a_s:
            file_ext_ns_ion = "tgs"
            file_caption = "Forward the ZIP file to @AnimatedStickersRoBot to get lottIE JSON containing the vector information."
        sticker_set = await borg(GetStickerSetRequest(sticker_attrib.stickerset))
        pack_file = os.path.join(
            Config.TMP_DOWNLOAD_DIRECTORY, sticker_set.set.short_name, "pack.txt"
        )
        if os.path.isfile(pack_file):
            os.remove(pack_file)
        # Sticker emojis are retrieved as a mapping of
        # <emoji>: <list of document ids that have this emoji>
        # So we need to build a mapping of <document id>: <list of emoji>
        # Thanks, Durov
        emojis = defaultdict(str)
        for pack in sticker_set.packs:
            for document_id in pack.documents:
                emojis[document_id] += pack.emoticon

        async def download(sticker, emojis, path, file):
            await borg.download_media(sticker, file=os.path.join(path, file))
            with open(pack_file, "a") as f:
                f.write(f"{{'image_file': '{file}','emojis':{emojis[sticker.id]}}},")

        pending_tasks = [
            asyncio.ensure_future(
                download(
                    document,
                    emojis,
                    Config.TMP_DOWNLOAD_DIRECTORY + sticker_set.set.short_name,
                    f"{i:03d}.{file_ext_ns_ion}",
                )
            )
            for i, document in enumerate(sticker_set.documents)
        ]
        await event.edit(
            f"Downloading {sticker_set.set.count} sticker(s) to .{Config.TMP_DOWNLOAD_DIRECTORY}{sticker_set.set.short_name}..."
        )
        num_tasks = len(pending_tasks)
        while 1:
            done, pending_tasks = await asyncio.wait(
                pending_tasks, timeout=2.5, return_when=asyncio.FIRST_COMPLETED
            )
            try:
                await event.edit(
                    f"Downloaded {num_tasks - len(pending_tasks)}/{sticker_set.set.count}"
                )
            except MessageNotModifiedError:
                pass
            if not pending_tasks:
                break
        await event.edit("Downloading to my local completed")
        # https://gist.github.com/udf/e4e3dbb2e831c8b580d8fddd312714f7
        directory_name = Config.TMP_DOWNLOAD_DIRECTORY + sticker_set.set.short_name
        zipf = zipfile.ZipFile(directory_name + ".zip", "w", zipfile.ZIP_DEFLATED)
        zipdir(directory_name, zipf)
        zipf.close()
        await borg.send_file(
            event.chat_id,
            directory_name + ".zip",
            caption=file_caption,
            force_document=True,
            allow_cache=False,
            reply_to=event.message.id,
            progress_callback=progress,
        )
        try:
            os.remove(directory_name + ".zip")
            os.remove(directory_name)
        except:
            pass
        await event.edit("task Completed")
        await asyncio.sleep(3)
        await event.delete()
    else:
        await event.edit("TODO: Not Implemented")


# Helpers


def is_it_animated_sticker(message):
    try:
        if message.media and message.media.document:
            mime_type = message.media.document.mime_type
            if "tgsticker" in mime_type:
                return True
            else:
                return False
        else:
            return False
    except:
        return False


def is_message_image(message):
    if message.media:
        if isinstance(message.media, MessageMediaPhoto):
            return True
        if message.media.document:
            if message.media.document.mime_type.split("/")[0] == "image":
                return True
        return False
    return False


async def silently_send_message(conv, text):
    await conv.send_message(text)
    response = await conv.get_response()
    await conv.mark_read(message=response)
    return response


async def stickerset_exists(conv, setname):
    try:
        await borg(GetStickerSetRequest(InputStickerSetShortName(setname)))
        response = await silently_send_message(conv, "/addsticker")
        if response.text == "Invalid pack selected.":
            await silently_send_message(conv, "/cancel")
            return False
        await silently_send_message(conv, "/cancel")
        return True
    except StickersetInvalidError:
        return False


def resize_image(image, save_locaton):
    """Copyright Rhyse Simpson:
    https://github.com/skittles9823/SkittBot/blob/master/tg_bot/modules/stickers.py
    """
    im = Image.open(image)
    maxsize = (512, 512)
    if (im.width and im.height) < 512:
        size1 = im.width
        size2 = im.height
        if im.width > im.height:
            scale = 512 / size1
            size1new = 512
            size2new = size2 * scale
        else:
            scale = 512 / size2
            size1new = size1 * scale
            size2new = 512
        size1new = math.floor(size1new)
        size2new = math.floor(size2new)
        sizenew = (size1new, size2new)
        im = im.resize(sizenew)
    else:
        im.thumbnail(maxsize)
    im.save(save_locaton, "PNG")


def progress(current, total):
    logger.info(
        "Uploaded: {} of {}\nCompleted {}".format(
            current, total, (current / total) * 100
        )
    )


def find_instance(items, class_or_tuple):
    for item in items:
        if isinstance(item, class_or_tuple):
            return item
    return None


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))
            os.remove(os.path.join(root, file))
