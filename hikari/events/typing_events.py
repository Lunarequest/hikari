# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Events fired when users begin typing in channels."""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "TypingEvent",
    "GuildTypingEvent",
    "PrivateTypingEvent",
]

import abc
import typing

import attr

from hikari import channels
from hikari import intents
from hikari import users
from hikari.api import special_endpoints
from hikari.events import base_events
from hikari.events import shard_events
from hikari.utilities import attr_extensions

if typing.TYPE_CHECKING:
    import datetime

    from hikari import guilds
    from hikari import snowflakes
    from hikari import traits
    from hikari.api import shard as gateway_shard


@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_TYPING, intents.Intents.PRIVATE_MESSAGE_TYPING)
class TypingEvent(shard_events.ShardEvent, abc.ABC):
    """Base event fired when a user begins typing in a channel."""

    @property
    @abc.abstractmethod
    def channel_id(self) -> snowflakes.Snowflake:
        """ID of the channel that this event concerns.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the channel that this event concerns.
        """

    @property
    @abc.abstractmethod
    def user_id(self) -> snowflakes.Snowflake:
        """ID of the user who triggered this typing event.

        Returns
        -------
        hikari.snowflakes.Snowflake
            ID of the user who is typing.
        """

    @property
    @abc.abstractmethod
    def timestamp(self) -> datetime.datetime:
        """Timestamp of when this typing event started.

        Returns
        -------
        datetime.datetime
            UTC timestamp of when the user started typing.
        """

    @property
    @abc.abstractmethod
    def channel(self) -> typing.Optional[channels.TextChannel]:
        """Get the cached channel, if known.

        Returns
        -------
        typing.Optional[hikari.channels.TextChannel]
            The channel, if known.
        """

    @property
    @abc.abstractmethod
    def user(self) -> typing.Optional[users.User]:
        """Get the cached user that is typing, if known.

        Returns
        -------
        typing.Optional[hikari.users.User]
            The user, if known.
        """

    @abc.abstractmethod
    async def fetch_channel(self) -> channels.TextChannel:
        """Perform an API call to fetch an up-to-date image of this channel.

        Returns
        -------
        hikari.channels.TextChannel
            The channel.
        """

    @abc.abstractmethod
    async def fetch_user(self) -> users.User:
        """Perform an API call to fetch an up-to-date image of this user.

        Returns
        -------
        hikari.users.User
            The user.
        """

    def trigger_typing(self) -> special_endpoints.TypingIndicator:
        """Return a typing indicator for this channel that can be awaited.

        Returns
        -------
        hikari.api.special_endpoints.TypingIndicator
            A typing indicator context manager and awaitable to trigger typing
            in a channel with.
        """
        return self.app.rest.trigger_typing(self.channel_id)


@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_TYPING)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class GuildTypingEvent(TypingEvent):
    """Event fired when a user starts typing in a guild channel."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflakes.Snowflake = attr.ib()
    # <<inherited docstring from TypingEvent>>.

    timestamp: datetime.datetime = attr.ib(repr=False)
    # <<inherited docstring from TypingEvent>>.

    guild_id: snowflakes.Snowflake = attr.ib()
    """ID of the guild that this event relates to.

    Returns
    -------
    hikari.snowflakes.Snowflake
        The ID of the guild that relates to this event.
    """

    user: guilds.Member = attr.ib(repr=False)
    """Member object of the user who triggered this typing event.

    Unlike on `PrivateTypingEvent` instances, Discord will always send
    this field in any payload.

    Returns
    -------
    hikari.guilds.Member
        Member of the user who triggered this typing event.
    """

    @property
    def channel(self) -> typing.Union[channels.GuildTextChannel, channels.GuildNewsChannel]:
        """Get the cached channel object this typing event occurred in.

        Returns
        -------
        typing.Union[hikari.channels.GuildTextChannel, hikari.channels.GuildNewsChannel]
            The channel.
        """
        channel = self.app.cache.get_guild_channel(self.channel_id)
        assert isinstance(
            channel, (channels.GuildTextChannel, channels.GuildNewsChannel)
        ), f"expected GuildTextChannel or GuildNewsChannel from cache, got {channel}"
        return channel

    @property
    def guild(self) -> typing.Optional[guilds.GatewayGuild]:
        """Get the cached object of the guild this typing event occurred in.

        If the guild is not found then this will return `builtins.None`.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The object of the gateway guild if found else `builtins.None`.
        """
        return self.app.cache.get_available_guild(self.guild_id) or self.app.cache.get_unavailable_guild(self.guild_id)

    @property
    def user_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from TypingEvent>>.
        return self.user.id

    async def fetch_channel(self) -> typing.Union[channels.GuildTextChannel, channels.GuildNewsChannel]:
        """Perform an API call to fetch an up-to-date image of this channel.

        Returns
        -------
        typing.Union[hikari.channels.GuildTextChannel, hikari.channels.GuildNewsChannel]
            The channel.
        """
        channel = await self.app.rest.fetch_channel(self.channel_id)
        assert isinstance(
            channel, (channels.GuildTextChannel, channels.GuildNewsChannel)
        ), f"expected GuildTextChannel or GuildNewsChannel from API, got {channel}"
        return channel

    async def fetch_guild(self) -> guilds.Guild:
        """Perform an API call to fetch an up-to-date image of this guild.

        Returns
        -------
        hikari.guilds.Guild
            The guild.
        """
        return await self.app.rest.fetch_guild(self.guild_id)

    async def fetch_guild_preview(self) -> guilds.GuildPreview:
        """Perform an API call to fetch an up-to-date preview of this guild.

        Returns
        -------
        hikari.guilds.GuildPreview
            The guild.
        """
        return await self.app.rest.fetch_guild_preview(self.guild_id)

    async def fetch_user(self) -> guilds.Member:
        """Perform an API call to fetch an up-to-date image of this member.

        Returns
        -------
        hikari.guilds.Member
            The member.
        """
        return await self.app.rest.fetch_member(self.guild_id, self.user_id)


@base_events.requires_intents(intents.Intents.PRIVATE_MESSAGES)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class PrivateTypingEvent(TypingEvent):
    """Event fired when a user starts typing in a guild channel."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflakes.Snowflake = attr.ib()
    # <<inherited docstring from TypingEvent>>.

    user_id: snowflakes.Snowflake = attr.ib(repr=True)
    # <<inherited docstring from TypingEvent>>.

    timestamp: datetime.datetime = attr.ib(repr=False)
    # <<inherited docstring from TypingEvent>>.

    @property
    def channel(self) -> typing.Optional[channels.DMChannel]:
        """Get the cached channel, if known.

        Returns
        -------
        typing.Optional[hikari.channels.DMChannel]
            The channel, if known.
        """
        return self.app.cache.get_dm(self.user_id)

    @property
    def user(self) -> typing.Optional[users.User]:
        # <<inherited docstring from TypingEvent>>.
        return self.app.cache.get_user(self.user_id)

    async def fetch_channel(self) -> channels.DMChannel:
        """Perform an API call to fetch an up-to-date image of this channel.

        Returns
        -------
        hikari.channels.DMChannel
            The channel.
        """
        channel = await self.app.rest.fetch_channel(self.channel_id)
        assert isinstance(channel, channels.DMChannel), f"expected DMChannel from API, got {channel}"
        return channel

    async def fetch_user(self) -> users.User:
        """Perform an API call to fetch an up-to-date image of the user.

        Returns
        -------
        hikari.users.User
            The user.
        """
        return await self.app.rest.fetch_user(self.user_id)
