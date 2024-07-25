from dataclasses import dataclass
from sqlite3 import connect, Connection, Row
from typing import List, Optional
from pathlib import Path
from shutil import copy
from uuid import uuid4

from argon2 import PasswordHasher
from pyzipper import AESZipFile, ZIP_LZMA, WZ_AES

from .abstract_storage_provider import AbstractStorageProvider
from vclib.owner.src.models.credentials import Credential, DeferredCredential


DEFAULT_WALLET_DIRECTORY = ".vclib_wallet_data"
CONFIG_FILE = "vclib_wallet_config.db"

CONFIG_SCHEMA = """
CREATE TABLE users (
    username TEXT PRIMARY KEY NOT NULL,
    secret_hash TEXT NOT NULL,
    user_store TEXT UNIQUE NOT NULL
);
"""

CREDENTIAL_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE credential_info (
    id TEXT PRIMARY KEY NOT NULL,
    issuer_name TEXT,
    issuer_url TEXT NOT NULL,
    config_id TEXT NOT NULL,
    config_name TEXT,
    type TEXT NOT NULL,
    deferred BOOLEAN NOT NULL
);

CREATE TABLE credentials (
    credential_id TEXT NOT NULL,
    raw_vc TEXT NOT NULL,
    received_at DATETIME NOT NULL,

	FOREIGN KEY (credential_id) 
    REFERENCES credential_info (id) 
            ON DELETE CASCADE 
            ON UPDATE CASCADE
);

CREATE TABLE deferred_credentials (
    credential_id TEXT NOT NULL,
    tx_id TEXT NOT NULL,
    deferred_endpoint TEXT NOT NULL,
    last_request DATETIME NOT NULL,
    access_token TEXT NOT NULL,

    FOREIGN KEY (credential_id) 
    REFERENCES credential_info (id) 
            ON DELETE CASCADE 
            ON UPDATE CASCADE
);
"""

class LocalStorageProvider(AbstractStorageProvider):

    # Default values pertaining to filenames. These could be overwitten by a subclass.
    LOCAL_DEFAULT_WALLET_DIRECTORY = DEFAULT_WALLET_DIRECTORY
    LOCAL_CONFIG_FILE = CONFIG_FILE

    LOCAL_CONFIG_SCHEMA = CONFIG_SCHEMA
    LOCAL_CREDENTIAL_SCHEMA = CREDENTIAL_SCHEMA

    @dataclass
    class ActiveUser:
        """
        A helper class, to keep track of information about the "active user". 
        
        This is specific to this particular storage implementation, so it's defined
        here.
        """
        username: str
        secret: str
        store: Path
        zip_object: AESZipFile
        conn: Connection

    storage_dir_path: Path
    config_db_path: Path
    active_user: Optional[ActiveUser]
    _pwd_hasher = PasswordHasher()

    def __init__(self, 
                 *args, 
                 storage_dir_path: str = None, 
                 **kwargs
                 ):
        
        # Resolve storage path
        if storage_dir_path:
            # If a different path is specified, it's up to the developer to ensure 
            # they're doing the right thing with any relative paths
            self.storage_dir_path = Path(storage_dir_path).resolve()
        else:
            # If a path isn't given, the directory will be named 
            # DEFAULT_WALLET_DIRECTORY and located under the user's home path.
            self.storage_dir_path = Path.home().joinpath(DEFAULT_WALLET_DIRECTORY)
        
        if self.storage_dir_path.exists():
            if not self.storage_dir_path.is_dir():
                raise Exception(
                    f"Invalid file path: {self.storage_dir_path} is not a directory"
                    )
            self._check_storage_directory()
        else:
            self._initialise_storage_directory()

    def __enter__(self):
        pass

    def __exit__(self):
        pass

    def active_user_name(self) -> str | None:
        if self.active_user:
            return self.active_user.username
        return None

    def _initialise_storage_directory(self):
        # Create directory
        self.storage_dir_path.mkdir(mode=0o770)

        self.config_db_path = self.storage_dir_path.joinpath(self.LOCAL_CONFIG_FILE)
        con = connect(str(self.config_db_path))
        con.executescript(CONFIG_SCHEMA)
        con.close()

    def _check_storage_directory(self):
        # Check directory structure
        config_path = self.storage_dir_path.joinpath(self.LOCAL_CONFIG_FILE)
        
        if not config_path.exists():
            raise Exception(
                f"Wallet data missing {config_path} file."
            )

    def register(self, username: str, password: str, *args, **kwargs):
        """
        Performs the necessary operations associated with 'registering' a new
        wallet/user for this storage implementation.
        - Adds entry to config.db
        - Creates a new ZIP archive corresponding to the entry in LOCAL_CONFIG_FILE
            - Creates a new sqlite db to the ZIP archvie
        - Sets the active user, with references to in-memory objects
        """
        store = uuid4().hex
        con = connect(str(self.config_db_path))
        con.row_factory = Row

        # Storing a hash isn't actually necessary for how this storage mechanism
        # works, but it makes error handling on a bad login attempt easier.
        hash = self._pwd_hasher.hash(password)

        new_user = {
            "username": username,
            "pwd": hash,
            "store": store
            }
        cursor = con.execute(
            """
            INSERT INTO users VALUES (:username, :pwd, :store)
            RETURNING username, user_store
            """, 
            new_user)
        u = cursor.fetchone()
        user_store_path = self.storage_dir_path.joinpath(u["user_store"])

        # NOTE: AESZipFile is an extension of zipfile.ZipFile, from Python 3.7.
        # It's compatible with Python 3.12, but not everything in zipfile.Zipfile 
        # from Python 3.12. If working with this class, check the 3.7 docs:
        # https://docs.python.org/3.7/library/zipfile.html

        u_zip = AESZipFile(
            str(user_store_path),
            mode="x", # NOT execute, x creates a new file
            compression=ZIP_LZMA,
            encryption=WZ_AES
            )
        u_zip.setpassword(password)
        # An in-memory SQLite database that can be regularly written to the above
        u_con = connect(f"file:{u['user_store']}?mode=memory")

        # Create tables
        u_con.executescript(self.LOCAL_CREDENTIAL_SCHEMA)

        self.active_user = self.ActiveUser(
            u["username"],
            password,
            user_store_path,
            u_zip,
            u_con
            )

    def login(self, username: str, password: str, *args, **kwargs):
        """
        Performs operations needed to access some form of storage.
        Implementation specific.
        """
        # Check config for user
        pass

    def logout(self, *args, **kwargs):
        """
        Performs operations needed to remove access to some form of storage.
        Implementation specific.
        """
        self.save(close=True)
        del self.active_user
        self.active_user = None
        pass

    def get_credential(self, cred_id: str, *args, **kwargs) -> Credential | DeferredCredential:
        """
        Retrieves corresponding credential
        """
        pass

    def get_credentials(self, *args, **kwargs) -> List[Credential | DeferredCredential]:
        """
        Retrieves all credentials
        """
        pass

    def get_deferred_credentials(self, *args, **kwargs) -> List[DeferredCredential]:
        """
        Retrieves all deferred credentials
        """
        pass

    def add_credential(self, cred: Credential | DeferredCredential, *args, **kwargs):
        """
        Adds a credential to storage
        """
        pass

    def update_credential(self, cred: Credential | DeferredCredential, *args, **kwargsl):
        """
        Updates a credential already in storage.
        """
        pass

    def upsert_credential(self, cred: Credential | DeferredCredential, *args, **kwargs):
        """
        Updates a credential already in storage if it exists, otherwise, adds it.
        """
        pass

    def save(self, *args, close=False, **kwargs):
        """
        Performs operations to push data to persistent storage (e.g. flushing to a 
        database).
        Implementation specific.
        """

        # Writes the sqlite dump into the AESZipFile Object
        self.active_user.zip_object.writestr(
            "wallet.db", 
            self.active_user.conn.serialize()
            )
        
        # TODO: Close & re-open the AESZipFile
        self.active_user.zip_object.close()
        # If 
        if close:
            return

        # Closing a zip file writes some extra records. 
        # So copy it to a backup, juuuuuuuust in case.
        u_path = self.active_user.store
        backup_path = str(self.active_user.store) + ".backup"
        copy(u_path, backup_path)

        self.active_user.zip_object = AESZipFile(
            str(self.active_user.store),
            mode="a", # NOT execute, x creates a new file
            compression=ZIP_LZMA,
            encryption=WZ_AES
            )
        self.active_user.zip_object.setpassword(self.active_user.secret)

        
