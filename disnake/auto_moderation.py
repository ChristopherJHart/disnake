"""
The MIT License (MIT)

Copyright (c) 2021-present Disnake Development

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

from datetime import timedelta
from typing import (
    TYPE_CHECKING,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Optional,
    Sequence,
    Type,
    Union,
    cast,
)

from .enums import (
    AutoModActionType,
    AutoModEventType,
    AutoModTriggerType,
    enum_if_int,
    try_enum,
    try_enum_to_int,
)
from .flags import AutoModKeywordPresets
from .utils import MISSING, _get_as_snowflake

if TYPE_CHECKING:
    from typing_extensions import Self

    from .abc import Snowflake
    from .guild import Guild, GuildChannel
    from .member import Member
    from .message import Message
    from .role import Role
    from .threads import Thread
    from .types.auto_moderation import (
        AutoModAction as AutoModActionPayload,
        AutoModActionExecutionEvent as AutoModActionExecutionEventPayload,
        AutoModActionMetadata,
        AutoModBlockMessageActionMetadata,
        AutoModPresetType,
        AutoModRule as AutoModRulePayload,
        AutoModSendAlertActionMetadata,
        AutoModTimeoutActionMetadata,
        AutoModTriggerMetadata as AutoModTriggerMetadataPayload,
        EditAutoModRule as EditAutoModRulePayload,
    )

__all__ = (
    "AutoModAction",
    "AutoModBlockMessageAction",
    "AutoModSendAlertAction",
    "AutoModTimeoutAction",
    "AutoModTriggerMetadata",
    "AutoModRule",
    "AutoModActionExecution",
)


def _automod_action_factory(data: AutoModActionPayload) -> AutoModAction:
    action_map: Dict[int, Type[AutoModAction]] = {
        AutoModActionType.block_message.value: AutoModBlockMessageAction,
        AutoModActionType.send_alert_message.value: AutoModSendAlertAction,
        AutoModActionType.timeout.value: AutoModTimeoutAction,
    }
    tp = action_map.get(data["type"], AutoModAction)
    return tp._from_dict(data)


class AutoModAction:
    """
    A base class for auto moderation actions.

    This class is not meant to be instantiated by the user.
    The user-constructible subclasses are:

    - :class:`AutoModBlockMessageAction`
    - :class:`AutoModSendAlertAction`
    - :class:`AutoModTimeoutAction`

    .. versionadded:: 2.6

    Attributes
    ----------
    type: :class:`AutoModActionType`
        The action type.
    """

    __slots__ = ("type", "_metadata")

    def __init__(
        self,
        *,
        type: AutoModActionType,
    ):
        self.type: AutoModActionType = enum_if_int(AutoModActionType, type)
        self._metadata: AutoModActionMetadata = {}

    def __repr__(self) -> str:
        return f"<{type(self).__name__} type={self.type!r}>"

    @classmethod
    def _from_dict(cls, data: AutoModActionPayload) -> Self:
        self = cls.__new__(cls)

        self.type = try_enum(AutoModActionType, data["type"])
        self._metadata = data.get("metadata", {})

        return self

    def to_dict(self) -> AutoModActionPayload:
        return {
            "type": self.type.value,
            "metadata": self._metadata,
        }


class AutoModBlockMessageAction(AutoModAction):
    """
    Represents an auto moderation action that blocks content from being sent.

    .. versionadded:: 2.6

    Attributes
    ----------
    type: :class:`AutoModActionType`
        The action type.
        Always set to :attr:`~AutoModActionType.block_message`.
    """

    __slots__ = ()

    _metadata: AutoModBlockMessageActionMetadata

    def __init__(self):
        super().__init__(type=AutoModActionType.block_message)

    def __repr__(self) -> str:
        return f"<{type(self).__name__}>"


class AutoModSendAlertAction(AutoModAction):
    """
    Represents an auto moderation action that sends an alert to a channel.

    .. versionadded:: 2.6

    Attributes
    ----------
    type: :class:`AutoModActionType`
        The action type.
        Always set to :attr:`~AutoModActionType.send_alert_message`.
    """

    __slots__ = ()

    _metadata: AutoModSendAlertActionMetadata

    def __init__(self, channel: Snowflake):
        super().__init__(type=AutoModActionType.send_alert_message)

        self._metadata["channel_id"] = channel.id

    @property
    def channel_id(self) -> int:
        """:class:`int`: The channel ID to send an alert in when the rule is triggered."""
        return int(self._metadata["channel_id"])

    def __repr__(self) -> str:
        return f"<{type(self).__name__} channel_id={self.channel_id!r}>"


class AutoModTimeoutAction(AutoModAction):
    """
    Represents an auto moderation action that times out the user.

    .. versionadded:: 2.6

    Attributes
    ----------
    type: :class:`AutoModActionType`
        The action type.
        Always set to :attr:`~AutoModActionType.timeout`.
    """

    __slots__ = ()

    _metadata: AutoModTimeoutActionMetadata

    def __init__(self, duration: Union[int, timedelta]):
        super().__init__(type=AutoModActionType.timeout)

        if isinstance(duration, timedelta):
            duration = int(duration.total_seconds())
        self._metadata["duration_seconds"] = duration

    @property
    def duration(self) -> int:
        """:class:`int`: The duration (in seconds) for which to timeout
        the user when the rule is triggered."""
        return int(self._metadata["duration_seconds"])

    def __repr__(self) -> str:
        return f"<{type(self).__name__} duration={self.duration!r}>"


# TODO: perhaps this should just be a typeddict instead?
class AutoModTriggerMetadata:
    """
    Metadata for an auto moderation trigger.

    .. versionadded:: 2.6

    Attributes
    ----------
    keywords: Optional[Sequence[:class:`str`]]
        The list of keywords to check for. Used with :attr:`AutoModTriggerType.keyword`.

        See `api docs <https://discord.com/developers/docs/resources/auto-moderation#auto-moderation-rule-object-keyword-matching-strategies>`__
        for details about how keyword matching works.

    presets: Optional[:class:`AutoModKeywordPresets`]
        The keyword presets. Used with :attr:`AutoModTriggerType.keyword_preset`.

    exempt_keywords: Optional[Sequence[:class:`str`]]
        The keywords that should be exempt from a preset. Used with :attr:`AutoModTriggerType.keyword_preset`.
    """

    __slots__ = ("keywords", "presets", "exempt_keywords")

    # TODO: add overloads - can we always require exactly one parameter here, or is it
    #       required to be able to construct this class without any parameters?
    def __init__(
        self,
        *,
        keywords: Optional[Sequence[str]] = None,
        presets: Optional[AutoModKeywordPresets] = None,
        exempt_keywords: Optional[Sequence[str]] = None,
    ):
        self.keywords: Optional[Sequence[str]] = keywords
        self.presets: Optional[AutoModKeywordPresets] = presets
        self.exempt_keywords: Optional[Sequence[str]] = exempt_keywords

    @classmethod
    def _from_dict(cls, data: AutoModTriggerMetadataPayload) -> Self:
        if (presets_data := data.get("presets")) is not None:
            presets = AutoModKeywordPresets._from_values(presets_data)
        else:
            presets = None

        return cls(
            keywords=data.get("keyword_filter"),
            presets=presets,
            exempt_keywords=data.get("allow_list"),
        )

    def to_dict(self) -> AutoModTriggerMetadataPayload:
        data: AutoModTriggerMetadataPayload = {}
        if self.keywords is not None:
            data["keyword_filter"] = list(self.keywords)
        if self.presets is not None:
            values: List[int] = self.presets.values
            data["presets"] = cast("List[AutoModPresetType]", values)
        if self.exempt_keywords is not None:
            data["allow_list"] = list(self.exempt_keywords)
        return data

    def __repr__(self) -> str:
        s = f"<{type(self).__name__}"
        if self.keywords is not None:
            s += f" keywords={self.keywords!r}"
        if self.presets is not None:
            s += f" presets={self.presets!r}"
        if self.exempt_keywords is not None:
            s += f" exempt_keywords={self.exempt_keywords!r}"
        return f"{s}>"


class AutoModRule:
    """
    Represents an auto moderation rule.

    .. versionadded:: 2.6

    Attributes
    ----------
    id: :class:`int`
        The rule ID.
    name: :class:`str`
        The rule name.
    enabled: :class:`bool`
        Whether this rule is enabled.
    guild: :class:`Guild`
        The guild of the rule.
    creator_id: :class:`int`
        The rule creator's ID. See also :attr:`.creator`.
    event_type: :class:`AutoModEventType`
        The event type this rule is applied to.
    trigger_type: :class:`AutoModTriggerType`
        The type of trigger that determines whether this rule's actions should run for a specific event.
    trigger_metadata: :class:`AutoModTriggerMetadata`
        Additional metadata associated with this rule's :attr:`.trigger_type`.
    exempt_role_ids: FrozenSet[:class:`int`]
        The role IDs that are exempt from this rule.
    exempt_channel_ids: FrozenSet[:class:`int`]
        The channel IDs that are exempt from this rule.
    """

    __slots__ = (
        "id",
        "name",
        "enabled",
        "guild",
        "creator_id",
        "event_type",
        "trigger_type",
        "trigger_metadata",
        "_actions",
        "exempt_role_ids",
        "exempt_channel_ids",
    )

    def __init__(self, *, data: AutoModRulePayload, guild: Guild):
        self.guild: Guild = guild

        self.id: int = int(data["id"])
        self.name: str = data["name"]
        self.enabled: bool = data["enabled"]
        self.creator_id: int = int(data["creator_id"])
        self.event_type: AutoModEventType = try_enum(AutoModEventType, data["event_type"])
        self.trigger_type: AutoModTriggerType = try_enum(AutoModTriggerType, data["trigger_type"])
        self._actions: List[AutoModAction] = [
            _automod_action_factory(action) for action in data["actions"]
        ]
        self.trigger_metadata: AutoModTriggerMetadata = AutoModTriggerMetadata._from_dict(
            data.get("trigger_metadata", {})
        )
        self.exempt_role_ids: FrozenSet[int] = (
            frozenset(map(int, exempt_roles))
            if (exempt_roles := data.get("exempt_roles"))
            else frozenset()
        )
        self.exempt_channel_ids: FrozenSet[int] = (
            frozenset(map(int, exempt_channels))
            if (exempt_channels := data.get("exempt_channels"))
            else frozenset()
        )

    @property
    def actions(self) -> List[AutoModAction]:
        """List[Union[:class:`AutoModBlockMessageAction`, :class:`AutoModSendAlertAction`, :class:`AutoModTimeoutAction`, :class:`AutoModAction`]]:
        The list of actions that will execute if a matching event triggered this rule."""
        return list(self._actions)  # return a copy

    @property
    def creator(self) -> Optional[Member]:
        """Optional[:class:`Member`]: The guild member that created this rule.
        May be ``None`` if the member cannot be found. See also :attr:`.creator_id`.
        """
        return self.guild.get_member(self.creator_id)

    @property
    def exempt_roles(self) -> List[Role]:
        """List[:class:`Role`]: The list of roles that are exempt from this rule."""
        return list(filter(None, map(self.guild.get_role, self.exempt_role_ids)))

    @property
    def exempt_channels(self) -> List[GuildChannel]:
        """List[:class:`abc.GuildChannel`]: The list of channels that are exempt from this rule."""
        return list(filter(None, map(self.guild.get_channel, self.exempt_channel_ids)))

    def __repr__(self) -> str:
        return (
            f"<AutoModRule id={self.id!r} name={self.name!r} enabled={self.enabled!r}"
            f" creator={self.creator!r} event_type={self.event_type!r} trigger_type={self.trigger_type!r}"
            f" actions={self._actions!r} exempt_roles={self.exempt_role_ids!r} exempt_channels={self.exempt_channel_ids!r}"
            f" trigger_metadata={self.trigger_metadata!r}>"
        )

    async def edit(
        self,
        *,
        name: str = MISSING,
        event_type: AutoModEventType = MISSING,
        trigger_metadata: AutoModTriggerMetadata = MISSING,
        actions: Sequence[AutoModAction] = MISSING,
        enabled: bool = MISSING,
        exempt_roles: Optional[Iterable[Snowflake]] = MISSING,
        exempt_channels: Optional[Iterable[Snowflake]] = MISSING,
        reason: Optional[str] = None,
    ) -> AutoModRule:
        """|coro|

        Edits the auto moderation rule.

        You must have :attr:`.Permissions.manage_guild` permission to do this.

        All fields are optional.

        Parameters
        ----------
        name: :class:`str`
            The rule's new name.
        event_type: :class:`AutoModEventType`
            The rule's new event type.
        trigger_metadata: :class:`AutoModTriggerMetadata`
            The rule's new associated trigger metadata.
        actions: Sequence[:class:`AutoModAction`]
            The rule's new actions.
        enabled: :class:`bool`
            Whether to enable the rule.
        exempt_roles: Optional[Iterable[:class:`abc.Snowflake`]]
            The rule's new exempt roles, up to 20. If ``[]`` or ``None`` is
            passed then all role exemptions are removed.
        exempt_channels: Optional[Iterable[:class:`abc.Snowflake`]]
            The rule's new exempt channels, up to 50.
            Can also include categories, in which case all channels inside that category will be exempt.
            If ``[]`` or ``None`` is passed then all channel exemptions are removed.
        reason: Optional[:class:`str`]
            The reason for editing the rule. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You do not have proper permissions to edit the rule.
        NotFound
            The rule does not exist.
        HTTPException
            Editing the rule failed.

        Returns
        -------
        :class:`AutoModRule`
            The newly updated auto moderation rule.
        """

        payload: EditAutoModRulePayload = {}

        if name is not MISSING:
            payload["name"] = name
        if event_type is not MISSING:
            payload["event_type"] = try_enum_to_int(event_type)
        if trigger_metadata is not MISSING:
            payload["trigger_metadata"] = trigger_metadata.to_dict()
        if actions is not MISSING:
            payload["actions"] = [a.to_dict() for a in actions]
        if enabled is not MISSING:
            payload["enabled"] = enabled
        if exempt_roles is not MISSING:
            payload["exempt_roles"] = (
                [e.id for e in exempt_roles] if exempt_roles is not None else []
            )
        if exempt_channels is not MISSING:
            payload["exempt_channels"] = (
                [e.id for e in exempt_channels] if exempt_channels is not None else []
            )

        data = await self.guild._state.http.edit_auto_moderation_rule(
            self.guild.id, self.id, reason=reason, **payload
        )
        return AutoModRule(data=data, guild=self.guild)

    async def delete(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Deletes the auto moderation rule.

        You must have :attr:`.Permissions.manage_guild` permission to do this.

        Parameters
        ----------
        reason: Optional[:class:`str`]
            The reason for deleting this rule. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You do not have proper permissions to delete the rule.
        NotFound
            The rule does not exist.
        HTTPException
            Deleting the rule failed.
        """
        await self.guild._state.http.delete_auto_moderation_rule(
            self.guild.id, self.id, reason=reason
        )


class AutoModActionExecution:
    """Represents the data for an :func:`on_auto_moderation_action_execution` event.

    .. versionadded:: 2.6

    Attributes
    ----------
    action: Union[:class:`AutoModBlockMessageAction`, :class:`AutoModSendAlertAction`, :class:`AutoModTimeoutAction`, :class:`AutoModAction`]
        The action that was executed.
    guild: :class:`Guild`
        The guild this action was executed in.
    rule_id: :class:`int`
        The ID of the rule that matched.
    rule_trigger_type: :class:`AutoModTriggerType`
        The trigger type of the rule that matched.
    user_id: :class:`int`
        The ID of the user that triggered this action.
        See also :attr:`.user`.
    channel_id: Optional[:class:`int`]
        The channel or thread ID in which the event occurred, if any.
        See also :attr:`.channel`.
    message_id: Optional[:class:`int`]
        The ID of the message that matched. ``None`` if the message was blocked,
        or if the content was not part of a message.
        See also :attr:`.message`.
    alert_message_id: Optional[:class:`int`]
        The ID of the alert message sent as a result of this action, if any.
        See also :attr:`.alert_message`.
    content: :class:`str`
        The content that matched.

        Requires :attr:`Intents.message_content` to be enabled,
        otherwise this field will be empty.

    matched_keyword: Optional[:class:`str`]
        The keyword that matched.
    matched_content: Optional[:class:`str`]
        The substring of :attr:`.content` that matched the rule/keyword.

        Requires :attr:`Intents.message_content` to be enabled,
        otherwise this field will be empty.
    """

    __slots__ = (
        "action",
        "guild",
        "rule_id",
        "rule_trigger_type",
        "user_id",
        "channel_id",
        "message_id",
        "alert_message_id",
        "content",
        "matched_keyword",
        "matched_content",
    )

    def __init__(self, *, data: AutoModActionExecutionEventPayload, guild: Guild) -> None:
        self.guild: Guild = guild
        self.action: AutoModAction = _automod_action_factory(data["action"])
        self.rule_id: int = int(data["rule_id"])
        self.rule_trigger_type: AutoModTriggerType = try_enum(
            AutoModTriggerType, data["rule_trigger_type"]
        )
        self.user_id: int = int(data["user_id"])
        self.channel_id: Optional[int] = _get_as_snowflake(data, "channel_id")
        self.message_id: Optional[int] = _get_as_snowflake(data, "message_id")
        self.alert_message_id: Optional[int] = _get_as_snowflake(data, "alert_system_message_id")
        self.content: str = data["content"]
        self.matched_keyword: Optional[str] = data.get("matched_keyword")
        self.matched_content: Optional[str] = data.get("matched_content")

    def __repr__(self) -> str:
        return (
            f"<{type(self).__name__} guild={self.guild!r} action={self.action!r}"
            f" rule_id={self.rule_id!r} rule_trigger_type={self.rule_trigger_type!r}"
            f" channel={self.channel!r} user_id={self.user_id!r} message_id={self.message_id!r}"
            f" alert_message_id={self.alert_message_id!r} content={self.content!r}"
            f" matched_keyword={self.matched_keyword!r} matched_content={self.matched_content!r}>"
        )

    @property
    def user(self) -> Optional[Member]:
        """Optional[:class:`Member`]: The guild member that triggered this action.
        May be ``None`` if the member cannot be found. See also :attr:`.user_id`.
        """
        return self.guild.get_member(self.user_id)

    @property
    def channel(self) -> Optional[Union[GuildChannel, Thread]]:
        """Optional[Union[:class:`abc.GuildChannel`, :class:`Thread`]]:
        The channel or thread in which the event occurred, if any.
        """
        return self.guild._resolve_channel(self.channel_id)

    @property
    def message(self) -> Optional[Message]:
        """Optional[:class:`Message`]: The message that matched, if any.
        Not available if the message was blocked, if the content was not part of a message,
        or if the message was not found in the message cache."""
        return self.guild._state._get_message(self.message_id)

    @property
    def alert_message(self) -> Optional[Message]:
        """Optional[:class:`Message`]: The alert message sent as a result of this action, if any.
        Only available if :attr:`action.type <AutoModAction.type>` is :attr:`~AutoModActionType.send_alert_message`
        and the message was found in the message cache."""
        return self.guild._state._get_message(self.alert_message_id)
