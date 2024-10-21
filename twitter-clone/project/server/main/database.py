import logging
import os
import random
from typing import Any, Dict

import aiofiles
from faker import Faker
from fastapi import HTTPException, UploadFile
from sqlalchemy import (
    ARRAY,
    Column,
    Date,
    ForeignKey,
    Integer,
    Row,
    Sequence,
    String,
    and_,
    delete,
    desc,
    func,
    select,
    update,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship

from .config import Settings, get_settings
from .error_handler import AppException, ObjectNotFoundException, SQLAlchemyException

# from typing_extensions import cast


# Initialize logging
logger_db = logging.getLogger("logger_db")
logging.basicConfig(level=logging.DEBUG)

# setting environment
settings: Settings = get_settings()
# TODO Delete info
logger_db.info("!!! ", settings.database_url)

engine = create_async_engine(str(settings.database_url), echo=True)
# expire_on_commit=False will prevent attributes from being expired after commit
async_session = async_sessionmaker(bind=engine, expire_on_commit=False)
session = async_session()
# Base = declarative_base()


class Base(DeclarativeBase):
    pass


async def insert_data(
    _async_session,
) -> None:
    fake = Faker()
    users = [
        User(api_key="u1", name=fake.name()),
        User(api_key="u2", name=fake.name()),
        User(api_key="u3", name=fake.name()),
        User(api_key="test", name=fake.name()),
    ]

    tweets_total = 12  # 3 per user
    # users_total = 4

    for i in range(len(users)):
        users[i].tweets_of_user.extend(
            [
                Tweet(
                    content=fake.text(20),
                    attachments=[],
                    author=i + 1,
                ),
                Tweet(
                    content=fake.text(20),
                    attachments=[],
                    author=i + 1,
                ),
                Tweet(
                    content=fake.text(20),
                    attachments=[],
                    author=i + 1,
                ),
            ]
        )

        users[i].likes_of_user.extend(
            [
                Like(
                    follower_id=i + 1,
                    tweet_id=random.randint(1, tweets_total - 1),
                ),
                Like(
                    follower_id=i + 1,
                    tweet_id=random.randint(1, tweets_total - 1),
                ),
                Like(
                    follower_id=i + 1,
                    tweet_id=random.randint(1, tweets_total - 1),
                ),
            ]
        )

        if i == 0:
            users[i].following_to.extend(
                [
                    FollowRelation(
                        follower_id=i + 1,
                        following_id=2,
                        # following_id=random.choice(
                        #     list(set(range(1, len(users) + 1)) - {i + 1}),
                    ),
                    FollowRelation(follower_id=i + 1, following_id=3),
                    FollowRelation(follower_id=i + 1, following_id=4),
                ]
            )
        elif i == 1:
            users[i].following_to.extend(
                [
                    FollowRelation(
                        follower_id=i + 1,
                        following_id=1,
                        # following_id=random.choice(
                        #     list(set(range(1, len(users) + 1)) - {i + 1}),
                    ),
                    FollowRelation(follower_id=i + 1, following_id=3),
                ]
            )
        elif i == 3:
            users[i].following_to.extend(
                [
                    FollowRelation(
                        follower_id=i + 1,
                        following_id=1,
                        # following_id=random.choice(
                        #     list(set(range(1, len(users) + 1)) - {i + 1}),
                    ),
                    FollowRelation(follower_id=i + 1, following_id=3),
                ]
            )

    try:
        async with _async_session() as _session:
            async with _session.begin():
                _session.add_all(users)
    except SQLAlchemyError as exc:
        logger_db.info("Database not created.. SQLAlchemy Error!")
        raise SQLAlchemyException(error_type=str(type(exc)), error_message=str(exc))

        # TODO Make an alternative exception responses?
        # return JSONResponse(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         content={'message': str(e)}
        # )
        # else:
        # return JSONResponse(
        #         status_code=status.HTTP_200_OK,
        #         content={"result": 'result'}
        # )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=True, index=True)
    api_key = Column(String(50), unique=True, nullable=False)
    date_of_registration = Column(Date(), server_default=func.now())

    # TODO choose correct lazy method for all classes
    tweets_of_user = relationship(
        "Tweet",
        back_populates="user_of_tweet",
        cascade="all, delete-orphan",
        lazy="select",
    )

    likes_of_user = relationship(
        "Like",
        back_populates="user_of_like",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # (User Column 2) relationship for user, who follows to somebody
    following_to = relationship(
        "FollowRelation",
        back_populates="follower_user",
        foreign_keys="FollowRelation.follower_id",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # (User Column 3) relationship for user, whom somebody follows by
    following_by = relationship(
        "FollowRelation",
        back_populates="following_user",
        foreign_keys="FollowRelation.following_id",
    )

    @classmethod
    async def get_current_user(
        cls, _session: AsyncSession, api_key: str | None
    ) -> Row[tuple[int, str]]:
        try:
            user_query = await _session.execute(
                select(User.id, User.name).filter(User.api_key == api_key)
            )
            user = user_query.fetchone()
            if user is None:
                raise ObjectNotFoundException(error_message="User not found.")
            return user
        except SQLAlchemyError as exc:
            raise SQLAlchemyException(
                error_type=type(exc), error_message=exc._message()
            )

    @classmethod
    async def get_user_by_apikey(
        cls, _session: AsyncSession, api_key: str | None
    ) -> dict[str, Any]:
        user = await cls.get_current_user(_session, api_key)
        try:
            user_follows_to_query = await _session.execute(
                select(FollowRelation.following_id.label("id"), User.name)
                # .distinct()
                .join(User.following_by).filter(FollowRelation.follower_id == user.id)
            )

            user_follows_to = user_follows_to_query.all()

            user_following_by_query = await _session.execute(
                select(FollowRelation.follower_id.label("id"), User.name)
                # .distinct()
                .join(User.following_to).filter(FollowRelation.following_id == user.id)
            )

            user_following_by = user_following_by_query.all()

            user_data = user._asdict()
            user_data["followers"] = [
                i_user_following_by._asdict()
                for i_user_following_by in user_following_by
            ]
            user_data["following"] = [
                i_user_follows_to._asdict() for i_user_follows_to in user_follows_to
            ]

            return {"result": True, "user": user_data}
        except SQLAlchemyError as exc:
            raise SQLAlchemyException(
                error_type=type(exc), error_message=exc._message()
            )

    @classmethod
    async def get_user_by_id(cls, _session: AsyncSession, uid: int) -> dict[str, Any]:
        try:
            user = await _session.get(User, uid)
            if user is None:
                raise ObjectNotFoundException(error_message="User not found.")
            else:
                # Method 1 with requests:
                user_follows_to_query = await _session.execute(
                    select(FollowRelation.following_id.label("id"), User.name)
                    .distinct()
                    .join(User.following_by)
                    .filter(FollowRelation.follower_id == user.id)
                )

                user_follows_to = user_follows_to_query.all()

                user_following_by_query = await _session.execute(
                    select(FollowRelation.follower_id.label("id"), User.name)
                    .distinct()
                    .join(User.following_to)
                    .filter(FollowRelation.following_id == user.id)
                )

                user_following_by = user_following_by_query.all()

                # Alternative method 2 to get relationships:
                # user_follows_to = [
                #     {"id": i_user.following_id, "name": i_user.following_user.name}
                #     for i_user in user.following_to
                # ]
                #
                # user_following_by = [
                #     {"id": i_user.follower_id, "name": i_user.follower_user.name}
                #     for i_user in user.following_by.distinct_target_key
                # ]

                # Alternative method 3 to get relationships:
                # duplicate_id = list()
                #
                # user_follows_to = list()
                # for i_user in user.following_to:
                #     if i_user.following_id not in duplicate_id:
                #         user_follows_to.append(
                #             {"id": i_user.following_id, "name":
                #             i_user.following_user.name}
                #         )
                #         duplicate_id.append(i_user.following_id)
                # duplicate_id.clear()
                #

                user_data = user.to_json()
                user_data["followers"] = [
                    i_user_following_by._asdict()
                    for i_user_following_by in user_following_by
                ]
                user_data["following"] = [
                    i_user_follows_to._asdict() for i_user_follows_to in user_follows_to
                ]

                return {"result": True, "user": user_data}
        except SQLAlchemyError as exc:
            raise SQLAlchemyException(
                error_type=type(exc), error_message=exc._message()
            )

    def __repr__(self):
        return (
            f"Пользователь: имя - {self.name}, api_key - {self.api_key}. Дата "
            f"регистрации: {self.date_of_registration}"
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            c.name: getattr(self, c.name) for c in self.__table__.columns
        }  # type:ignore


class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True)
    content = Column(String(1000), nullable=False, index=True)
    attachments: Column[Sequence] = Column(ARRAY(Integer), index=True)
    author = Column(Integer, ForeignKey("users.id"))
    date_tweet = Column(Date, default=func.now())

    # Define back references for relationships
    user_of_tweet = relationship("User", back_populates="tweets_of_user")

    likes_of_tweet = relationship(
        "Like",
        back_populates="tweet_with_like",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @classmethod
    async def get_tweets(cls, _session: AsyncSession, api_key: str) -> dict[str, Any]:
        """
        Пользователь может получить ленту из твитов отсортированных в
        порядке убывания по популярности от пользователей, которых он фоловит.
        """
        user = await User.get_current_user(_session, api_key)
        try:
            # get followings:
            followings_subq = (
                select(
                    FollowRelation.following_id, User.name, FollowRelation.follower_id
                )
                .join(FollowRelation.following_user)
                .filter(FollowRelation.follower_id == user.id)
                .subquery()
            )

            # get sorted tweets:
            tweets_query = await _session.execute(
                select(
                    Tweet,
                    User.name.label("author_name"),
                    followings_subq.c.name.label("following_name"),
                    func.count(Like.id).label("likes_count"),
                )
                .join(Tweet.likes_of_tweet, isouter=True)
                .join(Tweet.user_of_tweet)
                .join(
                    followings_subq,
                    Tweet.author == followings_subq.c.following_id,
                    isouter=True,
                )
                .group_by(Tweet.id, "author_name", "following_name")
                .order_by("following_name", desc("likes_count"))
            )
            tweets = tweets_query.all()

            # get likes
            likes_query = await _session.execute(
                select(Like.tweet_id, Like.follower_id, User.name).join(
                    Like.user_of_like
                )
            )
            likes = likes_query.all()
            # get attachments: alternative option - get all attachments at once but not
            # in loop like further in code
            # attachments_query = await _session.execute(select(Media.host_path))
            # attachments = attachments_query.all()

            # compile result
            tweet_data = [i_tweet[0].to_json() for i_tweet in tweets]
            tweet_author = [i_tweet[1] for i_tweet in tweets]

            for i, i_tweet in enumerate(tweet_data):
                # author compilation
                i_tweet["author"] = {
                    "id": i_tweet["author"],
                    "name": tweet_author[i],
                }

                # attachments compilation
                if i_tweet["attachments"]:
                    i_attach_path_query = await _session.execute(
                        select(Media.host_path).filter(
                            Media.id.in_(i_tweet["attachments"])
                        )
                    )
                    i_attach_path = i_attach_path_query.scalars().all()
                    # replace attachment ids with paths to files
                    i_tweet["attachments"] = i_attach_path
                # likes compilation
                i_tweet["likes"] = list()
                for tweet_id, follower_id, name in likes:
                    if tweet_id == i_tweet["id"]:
                        i_tweet["likes"].append({"user_id": follower_id, "name": name})
            return {"result": True, "tweets": tweet_data}
        except SQLAlchemyError as exc:
            raise SQLAlchemyException(
                error_type=type(exc), error_message=exc._message()
            )

    @classmethod
    async def create_tweet(
        cls, _session: AsyncSession, api_key: str | None, data: dict
    ) -> Column[int]:
        user = await User.get_current_user(_session, api_key)
        try:
            new_tweet = Tweet(
                content=data["tweet_data"],
                attachments=data["tweet_media_ids"],
                author=user.id,
            )
            _session.add(new_tweet)
            await _session.commit()

            return new_tweet.id

        except SQLAlchemyError as exc:
            raise SQLAlchemyException(
                error_type=type(exc), error_message=exc._message()
            )

    @classmethod
    async def delete_tweet(
        cls, _session: AsyncSession, api_key: str, tweet_id: int
    ) -> bool:
        user = await User.get_current_user(_session, api_key)
        try:
            tweet_to_delete = await _session.get(Tweet, tweet_id)

            if tweet_to_delete is None:
                raise ObjectNotFoundException(error_message="Tweet not found")
            elif tweet_to_delete.author != user.id:
                raise ObjectNotFoundException(
                    error_message="User does not have a permission to remove the tweet"
                )
            if tweet_to_delete.attachments:
                attachment_to_delete_query = await _session.execute(
                    select(Media).filter(
                        Media.id.in_(tweet_to_delete.attachments)
                    )  # type:ignore
                )

                attachment_to_delete = attachment_to_delete_query.scalars()

                # delete files from server.
                for i_media in attachment_to_delete:
                    os.remove(i_media.local_path)  # type:ignore
                    await _session.delete(i_media)

            await _session.delete(tweet_to_delete)
            await _session.commit()
            return True
        except SQLAlchemyError as exc:
            raise SQLAlchemyException(
                error_type=type(exc), error_message=exc._message()
            )

    def __repr__(self):
        return (
            f"твит: '{self.content}', вложение {self.attachments}, автор: "
            f"{self.author}"
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            c.name: getattr(self, c.name) for c in self.__table__.columns
        }  # type:ignore


class FollowRelation(Base):
    __tablename__ = "follow_relations"
    # __table_args__ = (
    #     UniqueConstraint("id1", "id2", name="unique"),
    # )

    id = Column(Integer, primary_key=True)
    follower_id = Column(Integer, ForeignKey("users.id"), index=True)
    following_id = Column(Integer, ForeignKey("users.id"), index=True)
    date_follow = Column(Date, default=func.now())
    date_unfollow = Column(Date, default=None)

    # Define back references for relationships
    follower_user = relationship(
        "User",
        back_populates="following_to",
        foreign_keys="FollowRelation.follower_id",
    )
    following_user = relationship(
        "User",
        back_populates="following_by",
        foreign_keys="FollowRelation.following_id",
    )

    @classmethod
    async def create_follow(
        cls, _session: AsyncSession, api_key: str, user_id: int
    ) -> Any:
        user = await User.get_current_user(_session, api_key)
        try:
            new_follow = FollowRelation(
                follower_id=user.id,
                following_id=user_id,
            )
            _session.add(new_follow)
            await _session.commit()

            return True

        except SQLAlchemyError as exc:
            raise SQLAlchemyException(
                error_type=type(exc), error_message=exc._message()
            )

    @classmethod
    async def delete_follow(
        cls, _session: AsyncSession, api_key: str, user_id: int
    ) -> Any:
        user = await User.get_current_user(_session, api_key)
        try:
            follow_to_delete = await _session.execute(
                delete(FollowRelation).filter(
                    and_(
                        FollowRelation.follower_id == user.id,
                        FollowRelation.following_id == user_id,
                    )
                )
            )
            if follow_to_delete.rowcount == 0:
                raise ObjectNotFoundException(
                    error_message="User does not follow this user"
                )
            await _session.commit()
            return True

        except SQLAlchemyError as exc:
            raise SQLAlchemyException(error_type=exc, error_message=exc._message())

    def __repr__(self):
        return (
            f"Пользователь {self.follower_id} "
            f"подписался на пользователя {self.following_id}"
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            c.name: getattr(self, c.name) for c in self.__table__.columns
        }  # type:ignore


class Like(Base):
    __tablename__ = "likes"
    # __table_args__ = (
    #     UniqueConstraint("tweet_id", "follower_id", name="single_like"),
    # )
    id = Column(Integer, primary_key=True)
    tweet_id = Column(Integer, ForeignKey("tweets.id"), index=True)
    follower_id = Column(Integer, ForeignKey("users.id"), index=True)
    date_like = Column(Date, default=func.now())
    date_unlike = Column(Date, default=None)

    # Define back references for relationships
    user_of_like = relationship("User", back_populates="likes_of_user")
    tweet_with_like = relationship("Tweet", back_populates="likes_of_tweet")

    @classmethod
    async def create_like(
        cls, _session: AsyncSession, api_key: str, tweet_id: int
    ) -> Any:
        user = await User.get_current_user(_session, api_key)
        try:
            # check whether tweet owner is current user
            tweet_is_mine_query = await _session.execute(
                select(Tweet.author).filter(
                    and_(Tweet.id == tweet_id, Tweet.author == user.id)
                )
            )

            tweet_is_mine = tweet_is_mine_query.one_or_none()

            if tweet_is_mine:
                return False
            else:
                new_like = Like(
                    tweet_id=tweet_id,
                    follower_id=user.id,
                )
                _session.add(new_like)
                await _session.commit()
                return True

        except SQLAlchemyError as exc:
            raise SQLAlchemyException(
                error_type=type(exc), error_message=exc._message()
            )

    @classmethod
    async def delete_like(
        cls, _session: AsyncSession, api_key: str, tweet_id: int
    ) -> Any:
        user = await User.get_current_user(_session, api_key)
        try:
            like_to_delete = await _session.execute(
                delete(Like).filter(
                    and_(
                        Like.tweet_id == tweet_id,
                        Like.follower_id == user.id,
                    )
                )
            )
            if like_to_delete.rowcount == 0:
                raise ObjectNotFoundException(
                    error_message="User's like not found on this tweet"
                )
            await _session.commit()
            return True

        except SQLAlchemyError as exc:
            raise SQLAlchemyException(error_type=exc, error_message=exc._message())

    def __repr__(self):
        return f"Пользователь {self.follower_id} " f"отметил твит {self.tweet_id}"

    def to_json(self) -> Dict[str, Any]:
        return {
            c.name: getattr(self, c.name) for c in self.__table__.columns
        }  # type:ignore


class Media(Base):
    __tablename__ = "media_attachments"

    id = Column(Integer, primary_key=True)
    file_name = Column(String(100))
    local_path = Column(String(100))
    host_path = Column(String(50))

    @staticmethod
    async def check_file(_session: AsyncSession, file) -> bool:
        # Get the file size (in bytes)
        file.file.seek(0, 2)
        file_size = file.file.tell()

        # move the cursor back to the beginning
        await file.seek(0)

        if file_size > 2 * 1024 * 1024:
            # more than 2 MB
            raise HTTPException(status_code=400, detail="File is too large (over 2Mb)")

        # check the content type (MIME type)
        content_type = file.content_type
        if content_type not in ["image/jpeg", "image/png", "image/gif"]:
            raise HTTPException(status_code=400, detail="Invalid file type")
        return True

    @staticmethod
    async def process_file(
        api_key: str,
        _session: AsyncSession,
        media_path_host: str,
        media_path_local: str,
        file: UploadFile,
    ) -> Column[int]:
        # user = await User.get_current_user(_session, api_key)
        destination_local = ""
        media_data = dict()
        try:
            # getting an ID for new attachment record
            new_media = Media()
            _session.add(new_media)
            await _session.flush()
            if file.filename:
                reg_filename = "{file_id}_{api_key}_media.{extension}".format(
                    file_id=new_media.id,
                    api_key=api_key,
                    extension=file.filename.split(".")[-1:][0],
                )
                destination_local = os.path.join(media_path_local, reg_filename)
                destination_host = os.path.join(media_path_host, reg_filename)
                media_data = {
                    "file_name": reg_filename,
                    "local_path": destination_local,
                    "host_path": destination_host,
                }

            try:
                # copy the file contents
                file_content = await file.read()
                async with aiofiles.open(destination_local, "w+b") as new_file:
                    await new_file.write(file_content)
            except Exception:
                raise AppException(error_message="Error! File not saved.")

            # updating attachment record with data
            await _session.execute(
                update(Media).values(**media_data).where(Media.id == new_media.id)
            )
            await _session.commit()
            return new_media.id

        except SQLAlchemyError as exc:
            raise SQLAlchemyException(error_type=exc, error_message=exc._message())
