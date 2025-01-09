import logging
import os
import pathlib
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


# Initialize logging
logger_db = logging.getLogger("logger_db")
logging.basicConfig(level=logging.DEBUG)

# setting environment
settings: Settings = get_settings()

engine = create_async_engine(settings.database_url, echo=True)
# expire_on_commit=False will prevent attributes from being expired after commit
async_session = async_sessionmaker(bind=engine, expire_on_commit=False)
session = async_session()


class Base(DeclarativeBase):
    pass


# Dependency to create future sessions for us on demand
async def get_session() -> AsyncSession:  # type: ignore
    async with async_session() as _session:
        try:
            yield _session
        except Exception as exc:
            await _session.rollback()
            raise exc
        finally:
            await _session.close()


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
                    ),
                    FollowRelation(follower_id=i + 1, following_id=3),
                ]
            )

    try:
        async with _async_session() as _session:
            async with _session.begin():
                _session.add_all(users)
    except SQLAlchemyError as exc:
        logger_db.error("Database not created.. SQLAlchemy Error!")
        raise SQLAlchemyException(error_type=str(type(exc)), error_message=str(exc))


async def files_clean_up(_path: str) -> None:
    """
    Remove files from server related to user/tweets which has been deleted
    """
    try:
        os.remove(_path)
        logger_db.info("!!! Related media clean up complete!")
    except FileNotFoundError as exc:
        logger_db.error("!!! File not found when deleting!", exc)
        raise ObjectNotFoundException(error_message="File not found when deleting")
    except OSError as exc:
        logger_db.error(f"!!! Error when deleting a file: {exc.strerror}")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=True, index=True)
    api_key = Column(String(50), unique=True, nullable=False)
    date_of_registration = Column(Date(), server_default=func.now())

    tweets_of_user = relationship(
        "Tweet",
        back_populates="user_of_tweet",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    likes_of_user = relationship(
        "Like",
        back_populates="user_of_like",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    # (User Column 2) relationship for user, who follows to somebody
    following_to = relationship(
        "FollowRelation",
        back_populates="follower_user",
        foreign_keys="FollowRelation.follower_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    # (User Column 3) relationship for user, whom somebody follows by
    following_by = relationship(
        "FollowRelation",
        back_populates="following_user",
        foreign_keys="FollowRelation.following_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    @classmethod
    async def get_current_user(
        cls, _session: AsyncSession, api_key: str | None
    ) -> Row[tuple[int, str]]:
        user_query = await _session.execute(
            select(User.id, User.name).filter(User.api_key == api_key)
        )
        user = user_query.fetchone()
        if user is None:
            raise ObjectNotFoundException(error_message="User not found.")
        return user

    @classmethod
    async def get_user_by_apikey(
        cls, _session: AsyncSession, api_key: str | None
    ) -> dict[str, Any]:
        user = await cls.get_current_user(_session, api_key)
        try:
            user_follows_to_query = await _session.execute(
                select(FollowRelation.following_id.label("id"), User.name)
                .join(User.following_by)
                .filter(FollowRelation.follower_id == user.id)
            )

            user_follows_to = user_follows_to_query.all()

            user_following_by_query = await _session.execute(
                select(FollowRelation.follower_id.label("id"), User.name)
                .join(User.following_to)
                .filter(FollowRelation.following_id == user.id)
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
            logger_db.error("SQLAlchemy Error!..")
            raise SQLAlchemyException(error_type=type(exc), error_message=str(exc))

    @classmethod
    async def get_user_by_id(cls, _session: AsyncSession, uid: int) -> dict[str, Any]:
        user = await _session.get(User, uid)
        if user is None:
            raise ObjectNotFoundException(error_message="User not found.")
        # Method 1 with requests:
        try:
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
            logger_db.error("SQLAlchemy Error!..")
            raise SQLAlchemyException(error_type=type(exc), error_message=str(exc))

    def __repr__(self):
        return (
            f"Пользователь: имя - {self.name}, api_key - {self.api_key}. Дата "
            f"регистрации: {self.date_of_registration}"
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            c.name: getattr(self, c.name) for c in self.__table__.columns  # type:ignore
        }


class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True)
    content = Column(String(1000), nullable=False, index=True)
    attachments: Column[Sequence] = Column(ARRAY(Integer), index=True)
    author = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    date_tweet = Column(Date, default=func.now())

    # Define back references for relationships
    user_of_tweet = relationship("User", back_populates="tweets_of_user")

    likes_of_tweet = relationship(
        "Like",
        back_populates="tweet_with_like",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    media_of_tweet = relationship(
        "Media",
        back_populates="tweet_with_media",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    @classmethod
    async def get_tweets(cls, _session: AsyncSession, api_key: str) -> dict[str, Any]:
        """
        User may get feed of tweets sorted by descent popularity by users he follows
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
            logger_db.error("SQLAlchemy Error!..")
            raise SQLAlchemyException(error_type=type(exc), error_message=str(exc))

    @classmethod
    async def create_tweet(
        cls, _session: AsyncSession, api_key: str | None, data: dict
    ) -> int:
        user = await User.get_current_user(_session, api_key)
        try:
            new_tweet = Tweet(
                content=data["tweet_data"],
                attachments=data["tweet_media_ids"],
                author=user.id,
            )
            _session.add(new_tweet)

            # update row with tweet id in Media table
            if data["tweet_media_ids"]:
                await _session.flush()
                new_tweet_id = new_tweet.id
                await _session.execute(
                    update(Media)
                    .values(tweet_id=new_tweet_id)
                    .where(Media.id.in_(data["tweet_media_ids"]))
                )
            await _session.commit()

            return new_tweet.id

        except SQLAlchemyError as exc:
            logger_db.error("SQLAlchemy Error!..")
            raise SQLAlchemyException(error_type=type(exc), error_message=str(exc))

    @classmethod
    async def delete_tweet(
        cls, _session: AsyncSession, api_key: str, tweet_id: int
    ) -> bool:
        user = await User.get_current_user(_session, api_key)
        tweet_to_delete = await _session.get(Tweet, tweet_id)
        if tweet_to_delete is None:
            raise ObjectNotFoundException(error_message="Tweet not found")
        elif tweet_to_delete.author != user.id:
            raise ObjectNotFoundException(
                error_message="User does not have a permission to remove the tweet"
            )

        attachment_to_delete = None
        # get attachment locations for tweet to delete
        try:
            if tweet_to_delete.attachments:
                attachment_to_delete_query = await _session.execute(
                    select(Media).filter(
                        Media.id.in_(tweet_to_delete.attachments)  # type:ignore
                    )
                )
                attachment_to_delete = attachment_to_delete_query.scalars()

            await _session.delete(tweet_to_delete)
            await _session.commit()
        except SQLAlchemyError as exc:
            logger_db.error("SQLAlchemy Error!..")
            raise SQLAlchemyException(error_type=type(exc), error_message=str(exc))

        # delete attachments
        if attachment_to_delete is not None:
            for i_media in attachment_to_delete:
                # os.remove(i_media.local_path)  # type:ignore
                await files_clean_up(_path=i_media.local_path)

        return True

    def __repr__(self):
        return (
            f"твит: '{self.content}', вложение {self.attachments}, автор: "
            f"{self.author}"
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            c.name: getattr(self, c.name) for c in self.__table__.columns  # type:ignore
        }


class FollowRelation(Base):
    __tablename__ = "follow_relations"
    # __table_args__ = (
    #     UniqueConstraint("id1", "id2", name="unique"),
    # )

    id = Column(Integer, primary_key=True)
    follower_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    following_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
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

        user_requested = await _session.get(User, user_id)
        if user_requested is None:
            raise ObjectNotFoundException(error_message="User not found.")

        if user.id == user_id:
            logger_db.info("!!! You can't follow yourself!")
            return False

        new_follow = FollowRelation(
            follower_id=user.id,
            following_id=user_id,
        )
        try:
            _session.add(new_follow)
            await _session.commit()
            return True

        except SQLAlchemyError as exc:
            logger_db.error("SQLAlchemy Error!..")
            raise SQLAlchemyException(error_type=type(exc), error_message=str(exc))

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
            logger_db.error("SQLAlchemy Error!..")
            raise SQLAlchemyException(error_type=type(exc), error_message=str(exc))

    def __repr__(self):
        return (
            f"Пользователь {self.follower_id} "
            f"подписался на пользователя {self.following_id}"
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            c.name: getattr(self, c.name) for c in self.__table__.columns  # type:ignore
        }


class Like(Base):
    __tablename__ = "likes"
    # __table_args__ = (
    #     UniqueConstraint("tweet_id", "follower_id", name="single_like"),
    # )
    id = Column(Integer, primary_key=True)
    tweet_id = Column(Integer, ForeignKey("tweets.id", ondelete="CASCADE"), index=True)
    follower_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
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
            # check whether tweet exists
            tweet_exist_query = await _session.execute(
                select(Tweet.id).filter(Tweet.id == tweet_id)
            )

            tweet_exist = tweet_exist_query.one_or_none()
            if tweet_exist:
                # check whether tweet owner is current user
                tweet_is_mine_query = await _session.execute(
                    select(Tweet.author).filter(
                        and_(Tweet.id == tweet_id, Tweet.author == user.id)
                    )
                )
                tweet_is_mine = tweet_is_mine_query.one_or_none()

                if tweet_is_mine:
                    logger_db.info(
                        "Create like.. Fail! Like personal tweets is not allowed"
                    )
                    return False

                # check whether like by current user exists
                like_exist_query = await _session.execute(
                    select(Like.id).filter(
                        and_(Like.tweet_id == tweet_id, Like.follower_id == user.id)
                    )
                )
                like_exist = like_exist_query.one_or_none()

                if like_exist:
                    logger_db.info(
                        "Create like.. Like already exists! No record created"
                    )
                    return False

                new_like = Like(
                    tweet_id=tweet_id,
                    follower_id=user.id,
                )
                _session.add(new_like)
                await _session.commit()
                return True

            else:
                raise ObjectNotFoundException(error_message="Tweet not found")

        except SQLAlchemyError as exc:
            logger_db.error("SQLAlchemy Error!..")
            raise SQLAlchemyException(error_type=type(exc), error_message=str(exc))

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
            logger_db.error("SQLAlchemy Error!..")
            raise SQLAlchemyException(error_type=type(exc), error_message=str(exc))

    def __repr__(self):
        return f"Пользователь {self.follower_id} " f"отметил твит {self.tweet_id}"

    def to_json(self) -> Dict[str, Any]:
        return {
            c.name: getattr(self, c.name) for c in self.__table__.columns  # type:ignore
        }


class Media(Base):
    __tablename__ = "media_attachments"

    id = Column(Integer, primary_key=True)
    tweet_id = Column(Integer, ForeignKey("tweets.id", ondelete="CASCADE"), index=True)
    file_name = Column(String(1000))
    local_path = Column(String(1000))
    host_path = Column(String(500))

    tweet_with_media = relationship("Tweet", back_populates="media_of_tweet")

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
        media_path_host: pathlib.Path,
        media_path_local: pathlib.Path,
        file: UploadFile,
    ) -> int:
        destination_local = pathlib.Path("")
        media_data = dict()
        try:
            # getting an ID for new attachment record
            new_media = Media()
            _session.add(new_media)
            await _session.flush()
        except SQLAlchemyError as exc:
            logger_db.error("SQLAlchemy Error!..")
            raise SQLAlchemyException(error_type=type(exc), error_message=str(exc))

        if file.filename:
            reg_filename = "{file_id}_{api_key}_media.{extension}".format(
                file_id=new_media.id,
                api_key=api_key,
                extension=file.filename.split(".")[-1:][0],
            )
            destination_local = media_path_local / reg_filename
            destination_host = media_path_host / reg_filename
            media_data = {
                "file_name": reg_filename,
                "local_path": str(destination_local),
                "host_path": str(destination_host),
            }

        try:
            # copy the file contents
            file_content = await file.read()
            async with aiofiles.open(destination_local, "w+b") as new_file:
                await new_file.write(file_content)
        except Exception:
            raise AppException(error_message="Error! File not saved.")

        try:
            # updating attachment record with data
            await _session.execute(
                update(Media).values(**media_data).where(Media.id == new_media.id)
            )
            await _session.commit()
            return new_media.id

        except SQLAlchemyError as exc:
            logger_db.error("SQLAlchemy Error!..")
            raise SQLAlchemyException(error_type=type(exc), error_message=str(exc))
