# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2020 Rapptz
Copyright (c) 2015 Rossen Georgiev <rossen@rgp.io>

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

EnumMeta and Enum from https://github.com/Rapptz/discord.py/blob/master/discord/enums.py
Enums from https://github.com/ValvePython/steam/blob/master/steam/enums/common.py
"""

import types
from collections import namedtuple
from typing import Any, Union, Iterable

__all__ = (
    'Enum',
    'IntEnum',
    'EType',
    'EResult',
    'ETypeChar',
    'EUniverse',
    'ECurrencyCode',
    'EInstanceFlag',
    'EPersonaState',
    'EChatEntryType',
    'EPersonaStateFlag',
    'ETradeOfferState',
    'EFriendRelationship',
    'EMarketListingState',
    'EChatRoomEnterResponse',
    'ECommunityVisibilityState',
)


def _create_value_cls(name) -> namedtuple:
    cls = namedtuple(f'_EnumValue_{name}', 'name value')
    cls.__repr__ = lambda self: f'<{name}.{self.name}: {repr(self.value)}>'
    cls.__str__ = lambda self: f'{name}.{self.name}'
    return cls


def _is_descriptor(obj) -> bool:
    return hasattr(obj, '__get__') or hasattr(obj, '__set__') or hasattr(obj, '__delete__')


def _IntEnum__eq__(self, other) -> bool:
    if type(other) is int:
        return self.value == other
    return Enum.__eq__(self, other)


def _IntEnum__lt__(self, x) -> bool:
    if isinstance(x, self.__class__):
        return self.value < x.value
    if type(x) is int:
        return self.value < x
    return False


def _IntEnum__le__(self, x) -> bool:
    return self < x or self == x


def _IntEnum__gt__(self, x) -> bool:
    if isinstance(x, self.__class__):
        return self.value > x.value
    if type(x) is int:
        return self.value > x
    return False


def _IntEnum__ge__(self, x) -> bool:
    return self > x or self == x


def _IntEnum__int__(self) -> int:
    return self.value


class EnumMeta(type):
    def __new__(mcs, name, bases, attrs):
        value_mapping = {}
        member_mapping = {}
        member_names = []

        value_cls = _create_value_cls(name)
        for key, value in list(attrs.items()):
            is_descriptor = _is_descriptor(value)
            if key[0] == '_' and not is_descriptor:
                continue

            # special case for classmethods to pass through
            if isinstance(value, classmethod):
                continue

            if is_descriptor:
                setattr(value_cls, key, value)
                del attrs[key]
                continue

            try:
                new_value = value_mapping[value]
            except KeyError:
                new_value = value_cls(name=key, value=value)
                value_mapping[value] = new_value
                member_names.append(key)

            member_mapping[key] = new_value
            attrs[key] = new_value

        attrs['_enum_value_map_'] = value_mapping
        attrs['_enum_member_map_'] = member_mapping
        attrs['_enum_member_names_'] = member_names
        del attrs['__qualname__']
        value_cls._actual_enum_cls_ = super().__new__(mcs, name, bases, attrs)
        try:
            if IntEnum in bases:
                # monkey patch the operators in
                value_cls.__eq__ = _IntEnum__eq__
                value_cls.__lt__ = _IntEnum__lt__
                value_cls.__le__ = _IntEnum__le__
                value_cls.__gt__ = _IntEnum__gt__
                value_cls.__ge__ = _IntEnum__ge__
                value_cls.__int__ = _IntEnum__int__
        except NameError:
            pass
        return value_cls._actual_enum_cls_

    def __iter__(cls) -> Iterable['Enum']:
        return (cls._enum_member_map_[name] for name in cls._enum_member_names_)

    def __reversed__(cls) -> Iterable['Enum']:
        return (cls._enum_member_map_[name] for name in reversed(cls._enum_member_names_))

    def __len__(cls):
        return len(cls._enum_member_names_)

    def __repr__(cls):
        return f'<enum {repr(cls.__name__)}>'

    @property
    def __members__(cls) -> types.MappingProxyType:
        return types.MappingProxyType(cls._enum_member_map_)

    def __call__(cls, value: Any) -> 'Enum':
        try:
            return cls._enum_value_map_[value]
        except (KeyError, TypeError):
            raise ValueError(f"{repr(value)} is not a valid {cls.__name__}")

    def __getitem__(cls, key: Any) -> 'Enum':
        return cls._enum_member_map_[key]

    def __setattr__(cls, name, value) -> None:
        raise TypeError('Enums are immutable.')

    def __delattr__(cls, attr) -> None:
        raise TypeError('Enums are immutable')

    def __instancecheck__(self, instance: Any):
        # isinstance(x, Y)
        # -> __instancecheck__(Y, x)
        try:
            cls = instance._actual_enum_cls_
            return cls is self or issubclass(cls, self)
        except AttributeError:
            return False


class Enum(metaclass=EnumMeta):
    """A general enumeration, emulates enum.Enum"""

    @classmethod
    def try_value(cls, value: Any) -> Union['Enum', Any]:
        try:
            return cls._enum_value_map_[value]
        except (KeyError, TypeError):
            return value

    # linting helpers

    @property
    def name(self) -> str:
        return self.name

    @property
    def value(self) -> Any:
        return self.value


class IntEnum(int, Enum):
    """An enumeration where all the values are integers, emulates enum.IntEnum"""
    pass


class EResult(IntEnum):
    Invalid = 0
    OK = 1  #: Success
    Fail = 2  #: Generic failure
    NoConnection = 3  #: No/failed network connection
    InvalidPassword = 5  #: Password/ticket is invalid
    LoggedInElsewhere = 6  #: Same user logged in elsewhere
    InvalidProtocolVersion = 7
    InvalidParameter = 8
    FileNotFound = 9
    Busy = 10  #: Called method busy - action not taken
    InvalidState = 11  #: Called object was in an invalid state
    InvalidName = 12
    InvalidEmail = 13
    DuplicateName = 14
    AccessDenied = 15
    Timeout = 16
    Banned = 17  #: VAC2 banned
    AccountNotFound = 18
    InvalidSteamID = 19
    ServiceUnavailable = 20  #: The requested service is currently unavailable
    NotLoggedOn = 21
    Pending = 22  #: Request is pending (may be in process, or waiting on third party)
    EncryptionFailure = 23
    InsufficientPrivilege = 24
    LimitExceeded = 25  #: Too much of a good thing
    Revoked = 26  #: Access has been revoked (used for revoked guest passes)
    Expired = 27  #: License/Guest pass the user is trying to access is expired
    AlreadyRedeemed = 28  #: Guest pass has already been redeemed by account, cannot be acked again
    DuplicateRequest = 29
    AlreadyOwned = 30  #: All the games in guest pass redemption request are already owned by the user
    IPNotFound = 31
    PersistFailed = 32  #: Failed to write change to the data store
    LockingFailed = 33  #: Failed to acquire access lock for this operation
    LogonSessionReplaced = 34
    ConnectFailed = 35
    HandshakeFailed = 36
    IOFailure = 37
    RemoteDisconnect = 38
    ShoppingCartNotFound = 39
    Blocked = 40
    Ignored = 41
    NoMatch = 42
    AccountDisabled = 43
    ServiceReadOnly = 44
    AccountNotFeatured = 45  #: Account doesn't have value, so this feature isn't available
    AdministratorOK = 46  #: Allowed to take this action, but only because requester is admin
    ContentVersion = 47  #: A Version mismatch in content transmitted within the Steam protocol
    TryAnotherCM = 48  #: The current CM can't service the user making a request, should try another
    PasswordRequiredToKickSession = 49  #: You are already logged in elsewhere, this cached credential login has failed
    AlreadyLoggedInElsewhere = 50  #: You are already logged in elsewhere, you must wait
    Suspended = 51  #: Long running operation (content download) suspended/paused
    Cancelled = 52  #: Operation canceled (typically by user content download)
    DataCorruption = 53  #: Operation canceled because data is ill formed or unrecoverable
    DiskFull = 54  #: Operation canceled - not enough disk space.
    RemoteCallFailed = 55  #: An remote call or IPC call failed
    ExternalAccountUnlinked = 57  #: External account (PSN, Facebook...) is not linked to a Steam account
    PSNTicketInvalid = 58  #: PSN ticket was invalid
    ExternalAccountAlreadyLinked = 59  #: External account (PSN, Facebook...) is already linked to some other account
    RemoteFileConflict = 60  #: The sync cannot resume due to a conflict between the local and remote files
    IllegalPassword = 61  #: The requested new password is not legal
    SameAsPreviousValue = 62  #: New value is the same as the old one (secret question and answer)
    AccountLogonDenied = 63  #: Account login denied due to 2nd factor authentication failure
    CannotUseOldPassword = 64  #: The requested new password is not legal
    InvalidLoginAuthCode = 65  #: Account login denied due to auth code invalid
    HardwareNotCapableOfIPT = 67
    IPTInitError = 68
    ParentalControlRestricted = 69  #: Operation failed due to parental control restrictions for current user
    FacebookQueryError = 70
    ExpiredLoginAuthCode = 71  #: Account login denied due to auth code expired
    IPLoginRestrictionFailed = 72
    VerifiedEmailRequired = 74
    NoMatchingURL = 75
    BadResponse = 76  #: Parse failure, missing field, etc.
    RequirePasswordReEntry = 77  #: The user cannot complete the action until they re-enter their password
    ValueOutOfRange = 78  #: The value entered is outside the acceptable range
    UnexpectedError = 79  #: Something happened that we didn't expect to ever happen
    Disabled = 80  #: The requested service has been configured to be unavailable
    InvalidCEGSubmission = 81  #: The set of files submitted to the CEG server are not valid!
    RestrictedDevice = 82  #: The device being used is not allowed to perform this action
    RegionLocked = 83  #: The action could not be complete because it is region restricted
    RateLimitExceeded = 84  #: Temporary rate limit exceeded. different from k_EResultLimitExceeded
    LoginDeniedNeedTwoFactor = 85  #: Need two-factor code to login
    ItemDeleted = 86  #: The thing we're trying to access has been deleted
    AccountLoginDeniedThrottle = 87  #: Login attempt failed, try to throttle response to possible attacker
    TwoFactorCodeMismatch = 88  #: Two factor code mismatch
    TwoFactorActivationCodeMismatch = 89  #: Activation code for two-factor didn't match
    NotModified = 91  #: Data not modified
    TimeNotSynced = 93  #: The time presented is out of range or tolerance
    SMSCodeFailed = 94  #: SMS code failure (no match, none pending, etc.)
    AccountActivityLimitExceeded = 96  #: Too many changes to this account
    PhoneActivityLimitExceeded = 97  #: Too many changes to this phone
    RefundToWallet = 98  #: Cannot refund to payment method, must use wallet
    EmailSendFailure = 99  #: Cannot send an email
    NotSettled = 100  #: Can't perform operation till payment has settled
    NeedCaptcha = 101  #: Needs to provide a valid captcha
    GSLTDenied = 102  #: A game server login token owned by this token's owner has been banned
    GSOwnerDenied = 103  #: Game server owner is denied for other reason
    InvalidItemType = 104  #: The type of thing we were requested to act on is invalid
    IPBanned = 105  #: The ip address has been banned from taking this action
    GSLTExpired = 106  #: This token has expired from disuse; can be reset for use
    InsufficientFunds = 107  #: User doesn't have enough wallet funds to complete the action
    TooManyPending = 108  #: There are too many of this thing pending already
    NoSiteLicensesFound = 109  #: No site licenses found
    WGNetworkSendExceeded = 110  #: The WG couldn't send a response because we exceeded max network send size
    AccountNotFriends = 111
    LimitedUserAccount = 112
    CantRemoveItem = 113


class EUniverse(IntEnum):
    Invalid = 0
    Public = 1
    Beta = 2
    Internal = 3
    Dev = 4
    Max = 6

    def __str__(self):
        return self.name


class EType(IntEnum):
    Invalid = 0
    Individual = 1  #: Single user account
    Multiseat = 2  #: Multiseat (e.g. cybercafe) account
    GameServer = 3  #: Game server account
    AnonGameServer = 4  #: Anonymous game server account
    Pending = 5
    ContentServer = 6  #: Content server
    Clan = 7
    Chat = 8
    ConsoleUser = 9  #: Fake SteamID for local PSN account on PS3 or Live account on 360, etc.
    AnonUser = 10
    Max = 11

    def __str__(self):
        return self.name


class ETypeChar(IntEnum):
    I = EType.Invalid
    U = EType.Individual
    M = EType.Multiseat
    G = EType.GameServer
    A = EType.AnonGameServer
    P = EType.Pending
    C = EType.ContentServer
    g = EType.Clan
    T = EType.Chat
    L = EType.Chat  # lobby chat, 'c' for clan chat
    c = EType.Chat  # clan chat
    a = EType.AnonUser

    def __str__(self):
        return self.name


class EInstanceFlag(IntEnum):
    MMSLobby = 0x20000
    Lobby = 0x40000
    Clan = 0x80000


class EFriendRelationship(IntEnum):
    NONE = 0
    Blocked = 1
    RequestRecipient = 2
    Friend = 3
    RequestInitiator = 4
    Ignored = 5
    IgnoredFriend = 6
    SuggestedFriend = 7
    Max = 8


class EPersonaState(IntEnum):
    Offline = 0
    Online = 1
    Busy = 2
    Away = 3
    Snooze = 4
    LookingToTrade = 5
    LookingToPlay = 6
    Max = 7

    def __str__(self):
        return self.name


class EPersonaStateFlag(IntEnum):
    NONE = 0
    HasRichPresence = 1
    InJoinableGame = 2
    Golden = 4
    RemotePlayTogether = 8
    ClientTypeWeb = 256
    ClientTypeMobile = 512
    ClientTypeTenfoot = 1024
    ClientTypeVR = 2048
    NoClue = 3072  # TODO figure out what this is
    LaunchTypeGamepad = 4096
    LaunchTypeCompatTool = 8192

    def __str__(self):
        return self.name


class ECommunityVisibilityState(IntEnum):
    NONE = 0
    Private = 1
    FriendsOnly = 2
    Public = 3


class EChatRoomEnterResponse(IntEnum):
    Success = 1  #: Success
    DoesntExist = 2  #: Chat doesn't exist (probably closed)
    NotAllowed = 3  #: General Denied - You don't have the permissions needed to join the chat
    Full = 4  #: Chat room has reached its maximum size
    Error = 5  #: Unexpected Error
    Banned = 6  #: You are banned from this chat room and may not join
    Limited = 7  #: Joining this chat is not allowed because you are a limited user (no value on account)
    ClanDisabled = 8  #: Attempt to join a clan chat when the clan is locked or disabled
    CommunityBan = 9  #: Attempt to join a chat when the user has a community lock on their account
    MemberBlockedYou = 10  #: Join failed - some member in the chat has blocked you from joining
    YouBlockedMember = 11  #: Join failed - you have blocked some member already in the chat
    RatelimitExceeded = 15  #: Join failed - to many join attempts in a very short period of time


class ECurrencyCode(IntEnum):
    Invalid = 0
    USD = 1
    GBP = 2
    EUR = 3
    CHF = 4
    RUB = 5
    PLN = 6
    BRL = 7
    JPY = 8
    NOK = 9
    IDR = 10
    MYR = 11
    PHP = 12
    SGD = 13
    THB = 14
    TRY = 17
    UAH = 18
    MXN = 19
    CAD = 20
    AUD = 21
    NZD = 22
    CNY = 23
    INR = 24
    PEN = 26
    ZAR = 28
    HKD = 29
    TWD = 30
    SAR = 31
    AED = 32
    SEK = 33
    ARS = 34
    ILS = 35
    BYN = 36
    KZT = 37
    KWD = 38
    QAR = 39
    UYU = 41
    Max = 42


class ETradeOfferState(IntEnum):
    Invalid = 1
    Active = 2
    Accepted = 3
    Countered = 4
    Expired = 5
    Canceled = 6
    Declined = 7
    InvalidItems = 8
    ConfirmationNeed = 9
    CanceledBySecondaryFactor = 10
    StateInEscrow = 11


class EChatEntryType(IntEnum):
    Invalid = 0
    ChatMsg = 1  #: Normal text message from another user
    Typing = 2  #: Another user is typing (not used in multi-user chat)
    InviteGame = 3  #: Invite from other user into that users current game
    LobbyGameStart = 5  #: lobby game is starting (dead - listen for LobbyGameCreated_t callback instead)
    LeftConversation = 6  #: user has left the conversation ( closed chat window )
    Entered = 7  #: User has entered the conversation (used in multi-user chat and group chat)
    WasKicked = 8  #: user was kicked (data: 64-bit steamid of actor performing the kick)
    WasBanned = 9  #: user was banned (data: 64-bit steamid of actor performing the ban)
    Disconnected = 10  #: user disconnected
    HistoricalChat = 11  #: a chat message from user's chat history or offline message
    LinkBlocked = 14  #: a link was removed by the chat filter.


class EMarketListingState(IntEnum):  # TODO figure out what the rest of these are
    ConfirmationNeeded = 0
    Active = 2
    Bought = 4
    Cancelled = 8
