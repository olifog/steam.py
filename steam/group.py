# -*- coding: utf-8 -*-

"""
MIT License

Copyright (c) 2020 James

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from datetime import datetime
from typing import List, TYPE_CHECKING
from xml.etree import ElementTree

from bs4 import BeautifulSoup

from .errors import HTTPException
from .iterators import CommentsIterator
from .models import URL

if TYPE_CHECKING:
    from .user import SteamID, User


class Group:
    """Represents a Steam group.

    .. container:: operations

        .. describe:: len(x)

            Returns the amount of members in the group.

    Attributes
    ------------
    name: :class:`str`
        The name of the group.
    id64: :class:`int`
        The 64-bit ID of the group.
    url: :class:`str`
        The url of the group.
    steam_id: :class:`~steam.SteamID`
        The SteamID instance attached to the group.
    icon_url: :class:`str`
        The icon url of the group. Uses the large (184x184 px) image url.
    description: :class:`str`
        The description of the group.
    headline: :class:`str`
        The headline of the group.
    count: :class:`int`
        The amount of users in the group.
    online_count: :class:`int`
        The amount of users currently online.
    in_chat_count: :class:`int`
        The amount of currently users in the group's chat room.
    in_game_count: :class:`int`
        The amount of user's currently in game.
    """
    __slots__ = ('id64', 'url', 'name', 'count', 'steam_id', 'icon_url',
                 'headline', 'description', 'online_count', 'in_chat_count',
                 'in_game_count', '_pages', '_state')

    def __init__(self, state, id):
        self.url = f'{URL.COMMUNITY}/gid/{id}'
        self._state = state

    async def __ainit__(self):
        data = await self._state.request('GET', f'{self.url}/memberslistxml')
        try:
            tree = ElementTree.fromstring(data)
        except ElementTree.ParseError:
            return
        for elem in tree:
            if elem.tag == 'totalPages':
                self._pages = int(elem.text)
            elif elem.tag == 'groupID64':
                from .user import SteamID

                self.id64 = int(elem.text)
                self.steam_id = SteamID(self.id64)
            elif elem.tag == 'groupDetails':
                for sub in elem:
                    if sub.tag == 'groupName':
                        self.name = sub.text
                    elif sub.tag == 'headline':
                        self.headline = sub.text
                    elif sub.tag == 'summary':
                        self.description = BeautifulSoup(sub.text, 'html.parser').get_text('\n')
                    elif sub.tag == 'avatarFull':
                        self.icon_url = sub.text
                    elif sub.tag == 'memberCount':
                        self.count = int(sub.text)
                    elif sub.tag == 'membersInChat':
                        self.in_chat_count = int(sub.text)
                    elif sub.tag == 'membersInGame':
                        self.in_game_count = int(sub.text)
                    elif sub.tag == 'membersOnline':
                        self.online_count = int(sub.text)

    def __repr__(self):
        attrs = (
            'name', 'steam_id'
        )
        resolved = [f'{attr}={repr(getattr(self, attr))}' for attr in attrs]
        return f"<Group {' '.join(resolved)}>"

    def __len__(self):
        return self.count

    async def fetch_members(self) -> List['SteamID']:
        """|coro|
        Fetches a groups member list.

        .. note::
            This one of the things that can return a 429 status code.
            This function will return as much of the list as it can. (~1500 or so).

        Returns
        --------
        List[:class:`~steam.SteamID`]
            A basic list of the groups members.
            This will only contain the first ~1500 members of the group.
            The rate-limits on this prevent getting more.
        """
        from .user import SteamID

        ret = []
        for i in range(self._pages):
            try:
                data = await self._state.request('GET', f'{self.url}/memberslistxml?p={i + 1}')
            except HTTPException:  # we got 429'ed no point waiting, the wait times are ridiculously long
                return ret  # return as much as we can
            else:
                tree = ElementTree.fromstring(data)
                for elem in tree:
                    if elem.tag == 'members':
                        for sub in elem:
                            if sub.tag == 'steamID64':
                                ret.append(SteamID(sub.text))
        ret: List[SteamID]  # circular imports suck
        return ret

    async def join(self) -> None:
        """|coro|
        Joins the :class:`Group`.
        """
        await self._state.http.join_group(self.id64)

    async def leave(self) -> None:
        """|coro|
        Leaves the :class:`Group`.
        """
        await self._state.http.leave_group(self.id64)

    async def invite(self, user: 'User'):
        """|coro|
        Invites a :class:`~steam.User` to the :class:`Group`.

        Parameters
        -----------
        user: :class:`~steam.User`
            The user to invite to the group.
        """
        await self._state.http.invite_user_to_group(user_id64=user.id64, group_id=self.id64)

    def comments(self, limit=None, before: datetime = None, after: datetime = None) -> CommentsIterator:
        """An iterator for accessing a :class:`~steam.Group`'s :class:`~steam.Comment` objects.

        Examples
        -----------

        Usage::

            async for comment in group.comments(limit=10):
                print('Author:', comment.author, 'Said:', comment.content)

        Flattening into a list::

            comments = await group.comments(limit=50).flatten()
            # comments is now a list of Comment

        All parameters are optional.

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The maximum number of comments to search through.
            Default is ``None`` which will fetch the group's entire comments section.
        before: Optional[:class:`datetime.datetime`]
            A time to search for comments before.
        after: Optional[:class:`datetime.datetime`]
            A time to search for comments after.

        Yields
        ---------
        :class:`~steam.Comment`
            The comment with the comment information parsed.
        """
        return CommentsIterator(state=self._state, id=self.id64, limit=limit, before=before, after=after,
                                comment_type='Clan')