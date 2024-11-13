import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict


class UserBaseModel(BaseModel):
    """
    User (Base) - id, name only
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    id: int
    """ User id """
    name: str
    """ User name """


class UserBaseForLikesOnlyModel(BaseModel):
    """
    User (Base for Likes) - user_id, name only
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    user_id: int
    """ User id """
    name: str
    """ User name """


class UserExtendBaseModel(BaseModel):
    """
    User (Extend Base) - id, name, followers, following only
    """

    model_config = ConfigDict(use_attribute_docstrings=True)

    id: int
    """ User id """
    name: str
    """ User name """

    followers: List[UserBaseModel]
    """ User followed by other users """
    following: List[UserBaseModel]
    """ User follows to other users """


class UserModel(BaseModel):
    """
    User personal information
    """

    model_config = ConfigDict(use_attribute_docstrings=True)
    id: int
    """ User id """
    name: str
    """ User name """
    api_key: str
    """ User Api Key"""
    date_of_registration: datetime.date = datetime.datetime.now()
    """ Registration date"""


class UserExtendModel(BaseModel):
    """
    User info - followers, followings only
    """

    model_config = ConfigDict(use_attribute_docstrings=True)
    followers: List[UserBaseModel]
    """ User followed by other users """
    following: List[UserBaseModel]
    """ User follows to other users """


class UserResponseModel(BaseModel):
    """
    User response model
    """

    model_config = ConfigDict(use_attribute_docstrings=True)
    result: bool = True
    """ Result success/fail """
    user: UserExtendBaseModel
    """ id, name, followers, following only """


class TweetModel(BaseModel):
    """
    Tweet info
    """

    model_config = ConfigDict(use_attribute_docstrings=True)
    id: int
    """ Tweet id"""
    content: str
    """ Tweet message/content """
    attachments: Optional[List[int]] = None
    """ Tweet attachments/files/images """
    author: int
    """ Tweet's autor id """
    date_tweet: datetime.date = datetime.datetime.now()
    """ Tweet's creation date"""


class TweetBaseModel(BaseModel):
    """
    Tweet Base - tweet info with author as dict + likes
    """

    model_config = ConfigDict(use_attribute_docstrings=True)
    id: int
    """ Tweet id"""
    content: str
    """ Tweet message/content """
    attachments: Optional[List[int]] = None
    """ Tweet attachments/files/images """
    author: UserBaseModel
    """ Tweet's autor id and name """
    likes: List[UserBaseForLikesOnlyModel] = []
    """Users who likes the tweet"""


class TweetBaseWithPathsModel(BaseModel):
    """
    Tweet Base - tweet info with author as dict + likes
    """

    model_config = ConfigDict(use_attribute_docstrings=True)
    id: int
    """ Tweet id"""
    content: str
    """ Tweet message/content """
    attachments: Optional[List[str]] = None
    """ Tweet attachments/files/images """
    author: UserBaseModel
    """ Tweet's autor id and name """
    likes: List[UserBaseForLikesOnlyModel] = []
    """Users who likes the tweet"""


class TweetResponseModel(BaseModel):
    """
    Tweet response model
    """

    model_config = ConfigDict(use_attribute_docstrings=True)
    result: bool = True
    """ Result success/fail """
    tweets: List[TweetBaseWithPathsModel]
    """ Tweet info + authors +  ent paths + likes """


class TweetCreateResponseModel(BaseModel):
    """
    Tweet create response model
    """

    model_config = ConfigDict(use_attribute_docstrings=True)
    result: bool
    """ Result success/fail """
    tweet_id: int
    """ Tweet id created """


class FollowRelationModel(BaseModel):
    """
    Follow relation model
    """

    model_config = ConfigDict(use_attribute_docstrings=True)
    id: int
    """ Record id """
    follower_id: int
    """ Follower user id (who follows to other users) """
    following_id: int
    """ Following User id (which other user follows to) """


class LikeModel(BaseModel):
    """
    Like info
    """

    model_config = ConfigDict(use_attribute_docstrings=True)
    id: int
    """ Like id """
    follower_id: int
    """ Follower user id (who follows to other users) """
    tweet_id: int
    """ Tweet id """
    date_like: datetime.date = datetime.datetime.now  # type: ignore
    """ Date of like """
    date_unlike: Optional[datetime.date] = None
    """ Date of unlike """


class ErrorModel(BaseModel):
    """
    Error model
    """

    model_config = ConfigDict(use_attribute_docstrings=True)
    result: bool = False
    """ Result success/fail """
    error_type: str
    """ Error type """
    error_message: str
    """ Error message """


responses: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorModel, "description": "Object not found"},
    500: {"model": ErrorModel, "description": "Server error"},
}
