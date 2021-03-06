"""Application models"""


from datetime import datetime
from typing import Any, Dict, Optional, Union

from dateutil.tz import tzutc

from bookie_server.blueprints.bookmark_manager.utils.datetime_utils import \
    parse_iso8601
from bookie_server.extensions import db
from .utils import string_utils
from .utils.utils import filter_dict


__all__ = ['Bookmark', 'Tag']


class BookieModel:
    def dump(self):
        raise NotImplementedError(
            f'dumps not implemented in subclass {self.__class__.__name__}'
            )


class Bookmark(db.Model, BookieModel):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=False)
    _modified = db.Column(db.TIMESTAMP(timezone=True), nullable=False)
    _created = db.Column(db.TIMESTAMP(timezone=True), nullable=False)
    tags = db.relationship(
        'Tag',
        secondary=lambda: bookmark_and_bookmark_tag_association_table,
        back_populates='bookmarks',
        lazy='joined'
    )

    def __init__(self,
                 title: str,
                 url: str,
                 notes: str = '',
                 modified: Optional[str] = datetime.now(tzutc()).isoformat(),
                 created: Union[str, None] = datetime.now(tzutc()).isoformat(),
                 tags: Optional = [],
                 **kwargs):
        '''
        :param title:
        :param url:
        :param notes:
        :param modified: If specified, the value is used, else defaults to
          current date and time
        :param created: None results in no value being set, else the value is
          set or defaults to current date and time
        :param kwargs:
        '''
        db.Model.__init__(self, **kwargs)

        self.title = title
        self.url = url
        self.notes = notes
        self.tags = tags  # SQLAlchemy backref
        self._modified = parse_iso8601(modified)
        self._created = parse_iso8601(created) if created is not None else None

    def __repr__(self):
        truncate_len = 10
        title = string_utils.truncate_str(self.title, truncate_len)
        url = string_utils.truncate_str(self.url, truncate_len)
        return (f'<title="{title}", '
                f'url="{url}", '
                f'modified=({self.modified}), '
                f'created=({self.created}), '
                f'tags=({len(self.tags)} tags)>')

    @property
    def created(self) -> datetime:
        return self._created.astimezone(tzutc())

    @created.setter
    def created(self, iso8601_timestamp: datetime):
        self._created = parse_iso8601(iso8601_timestamp)

    @property
    def modified(self) -> datetime:
        return self._modified.astimezone(tzutc())

    @modified.setter
    def modified(self, iso8601_timestamp: datetime):
        self._modified = parse_iso8601(iso8601_timestamp)

    def dump(self) -> Dict[str, Any]:
        return filter_dict(
            {'id': self.id,
             'title': self.title,
             'url': self.url,
             'notes': self.notes,
             'modified':
                 self.modified.astimezone(tzutc()).isoformat() if self.modified
                                                               else None,
             'created':
                 self._created.astimezone(tzutc()).isoformat() if self._created
                                                               else None,
             'tags': [tag.dump() for tag in self.tags]},
            'tags',
            'notes'
        )


class Tag(db.Model, BookieModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False, unique=True)
    bookmarks = db.relationship(
        'Bookmark',
        secondary=lambda: bookmark_and_bookmark_tag_association_table,
        back_populates='tags',
        lazy='noload'
    )

    def __init__(self, name: str, **kwargs):
        db.Model.__init__(self, **kwargs)

        self.name = name
        self.tags = []  # SQLAlchemy backref

    def __repr__(self):
        return (f'<name="{self.name}", '
                f'bookmarks=({len(self.bookmarks)} bookmarks)>')

    def dump(self) -> Dict[str, Any]:
        return filter_dict({'id': self.id,
                            'name': self.name,
                            'bookmarks': self.bookmarks})


bookmark_and_bookmark_tag_association_table = db.Table(
    'bookmark_and_bookmark_tag_association',
    db.Column('bookmark_id', db.Integer, db.ForeignKey('bookmark.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)
