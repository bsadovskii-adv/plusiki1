# -*- coding: utf-8 -*-

from services.bindings import get_binding_by_telegram_id


def get_or_restore_internal_id(context, telegram_id: int) -> int | None:
    """
    Возвращает internal user_id для telegram_id.

    1. Сначала пробует взять из context.user_data (кэш)
    2. Если нет — восстанавливает из БД (telegram_bindings)
    3. Если привязки нет — возвращает None
    """

    internal_id = context.user_data.get("internal_id")
    if internal_id is not None:
        return internal_id

    internal_id = get_binding_by_telegram_id(telegram_id)
    if internal_id is not None:
        context.user_data["internal_id"] = internal_id
        return internal_id

    return None
