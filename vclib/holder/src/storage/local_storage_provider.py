from dataclasses import dataclass
from pathlib import Path
from sqlite3 import (
    Connection,
    Cursor,
    Row,
    connect,
    register_adapter,
    register_converter,
)
from uuid import uuid4

from argon2 import PasswordHasher
from pyzipper import WZ_AES, ZIP_LZMA, AESZipFile

from vclib.holder.src.models.credentials import Credential, DeferredCredential

from .abstract_storage_provider import AbstractStorageProvider

DEFAULT_WALLET_DIRECTORY = ".vclib_wallet_data"
CONFIG_FILE = "vclib_wallet_config.db"
U_WALLET_FILENAME = "wallet.db"

CONFIG_SCHEMA = """
CREATE TABLE users (
    username TEXT PRIMARY KEY NOT NULL,
    secret_hash TEXT NOT NULL,
    user_store TEXT UNIQUE NOT NULL
);
"""

WALLET_SCHEMA = """
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

def dict_factory(cursor: Cursor, row: Row):
    # Ripped straight out of the sqlite3 row factory example, to make model
    # validation easier.
    # https://docs.python.org/3/library/sqlite3.html#sqlite3-howto-row-factory
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)} # noqa: C416

# SQLite uses booleans as an alias for int (0, 1)
register_adapter(bool, int)
register_converter("BOOLEAN", lambda v: bool(int(v)))

class LocalStorageProvider(AbstractStorageProvider):
    """
    Implementation of AbstractStorageProvider.

    ## NOTES ON DESIGN ##
    This implementation is designed for wallet implementations where the backend and
    the frontend run from the same device.

    Standard web authentication/authorization strategies become less useful in this
    use case, the goal of this storage provider is to write persistent data to disk
    in a safe-(r) manner. This is done by employing a singleton pattern for one
    active user at a time, and loading a transient SQLite database into memory
    containing the user's credentials. These are written to disk as an SQLite DB
    wrapped in a ZIP archive encrypted with AES, rather than standard ZIP encryption.
    This is because the encryption PKZIP supports has a couple of known weaknesses.

    If you want to unzip these files while developing, you will need to use 3rd party
    software such as 7-Zip, or simply opening up the Python3 interpreted and using
    the pyzipper module directly.

    A transient SQLite DB is being used rather than a file to minimise writes to disk
    of the unprotected credentials. This should, at minimum, prevent someone with
    access to the unlocked holder's device from simply finding the saved files in
    memory and extracting the credentials from within without needing to 'unlock' the
    wallet.
    """

    # Default values pertaining to filenames. These could be overwitten by a subclass.
    LOCAL_DEFAULT_WALLET_DIRECTORY = DEFAULT_WALLET_DIRECTORY
    LOCAL_CONFIG_FILE = CONFIG_FILE
    LOCAL_U_WALLET_FILENAME = U_WALLET_FILENAME

    LOCAL_CONFIG_SCHEMA = CONFIG_SCHEMA
    LOCAL_CREDENTIAL_SCHEMA = WALLET_SCHEMA

    # Aliases all columns so that they can be quickly converted
    # to a [Deferred]Credential object
    CREDENTIAL_QUERY = """
    SELECT c_info.id AS id,
    c_info.issuer_name AS issuer_name,
    c_info.issuer_url AS issuer_url,
    c_info.config_id AS credential_configuration_id,
    c_info.config_name AS credential_configuration_name,
    c_info.type AS c_type,
    c_info.deferred AS is_deferred,
    creds.raw_vc AS raw_sdjwtvc,
    creds.received_at AS received_at
    FROM credential_info AS c_info
    INNER JOIN credentials AS creds
    ON c_info.id = creds.credential_id
    """
    DEFERRED_QUERY = """
    SELECT c_info.id AS id,
    c_info.issuer_name AS issuer_name,
    c_info.issuer_url AS issuer_url,
    c_info.config_id AS credential_configuration_id,
    c_info.config_name AS credential_configuration_name,
    c_info.type AS c_type,
    c_info.deferred AS is_deferred,
    d_creds.tx_id AS transaction_id,
    d_creds.deferred_endpoint AS deferred_credential_endpoint,
    d_creds.last_request AS last_request,
    d_creds.access_token AS access_token
    FROM credential_info AS c_info
    INNER JOIN deferred_credentials AS d_creds
    ON c_info.id = d_creds.credential_id
    """

    @dataclass
    class ActiveUser:
        """
        A helper class, to keep track of information about the "active user".

        This is specific to this particular storage implementation, so it's defined
        here.
        """
        username: str
        secret: bytes
        store: Path
        db: Connection

    storage_dir_path: Path
    config_db_path: Path
    active_user: ActiveUser | None

    # Using argon2 for hashing.
    _pwd_hasher = PasswordHasher()

    def __init__(self,
                 *args,
                 storage_dir_path: str | None = None,
                 **kwargs
                 ):
        """
        TODO
        """

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

    def _initialise_storage_directory(self):
        # Create directory
        self.storage_dir_path.mkdir(mode=0o660)

        # Create the config file. This file is unprotected, nothing sensitive goes
        # in this file.
        self.config_db_path = self.storage_dir_path.joinpath(self.LOCAL_CONFIG_FILE)
        con = connect(str(self.config_db_path))
        con.executescript(self.LOCAL_CONFIG_SCHEMA)
        con.close()

    def _check_storage_directory(self):
        # Check directory structure
        config_path = self.storage_dir_path.joinpath(self.LOCAL_CONFIG_FILE)

        if not config_path.exists():
            raise Exception(
                f"Wallet data missing {config_path} file."
            )

    def _save_db_to_zip(self):
        # NOTE: AESZipFile is an extension of zipfile.ZipFile, from Python 3.7.
        # It's compatible with Python 3.12, but not everything in zipfile.Zipfile
        # from Python 3.12. If working with this class, check the 3.7 docs:
        # https://docs.python.org/3.7/library/zipfile.html

        if not self.active_user:
            return

        with AESZipFile(
            str(self.active_user.store),
            mode="a", # Append mode
            compression=ZIP_LZMA,
            encryption=WZ_AES
            ) as u_zip:
            u_zip.setpassword(self.active_user.secret)

            # Writes the sqlite dump into the AESZipFile Object
            u_zip.writestr(
                self.LOCAL_U_WALLET_FILENAME,
                self.active_user.db.serialize()
                )

    def _check_active_user(self):
        if not self.active_user:
            raise Exception("No current active user.")

    def active_user_name(self) -> str | None:
        """
        TODO
        """
        if self.active_user:
            return self.active_user.username
        return None

    def register(self, username: str, password: str):
        """
        Performs the necessary operations associated with 'registering' a new
        wallet/user for this storage implementation.
        - Adds entry to config.db
        - Creates a new ZIP archive corresponding to the entry in LOCAL_CONFIG_FILE
            - Creates a new sqlite db to the ZIP archvie
        - Sets the active user, with references to in-memory objects
        TODO
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

        # Add an entry to config.db
        cursor = con.execute(
            """
            INSERT INTO users VALUES (:username, :pwd, :store)
            RETURNING username, user_store
            """,
            new_user)
        u = cursor.fetchone()
        cursor.close()

        user_store_path = self.storage_dir_path.joinpath(u["user_store"])

        # An in-memory SQLite database that can be regularly serialised
        u_con = connect(":memory:")
        u_con.row_factory = dict_factory

        # Create tables
        cursor = u_con.executescript(self.LOCAL_CREDENTIAL_SCHEMA)
        cursor.close()

        # Commit
        u_con.commit()

        u_secret = password.encode()

        # Save empty DB to zip, creating in 'x' mode. this should happen once.
        # Use as context manager to ensure ZIP gets closed.
        with AESZipFile(
            str(user_store_path),
            mode="x", # NOT execute, x creates a new file
            compression=ZIP_LZMA,
            encryption=WZ_AES
            ) as u_zip:

            u_zip.setpassword(u_secret)
            u_zip.writestr(self.LOCAL_U_WALLET_FILENAME, u_con.serialize())

        self.active_user = self.ActiveUser(
            u["username"],
            u_secret,
            user_store_path,
            u_con
            )

    def login(self, username: str, password: str):
        """
        TODO
        """
        # Logout the current user if there is one.
        if self.active_user:
            self.logout()

        con = connect(str(self.config_db_path))
        con.row_factory = Row
        with con.execute(
            """
            SELECT username, secret_hash, user_store FROM users
            WHERE username = :uname
            """, {"uname": username}) as cursor:
            cursor: Cursor
            u = cursor.fetchone()
            if not u:
                raise Exception("Bad login attempt")

            p_hash: str = u["secret_hash"]
            try:
                self._pwd_hasher.verify(p_hash, password)
            except Exception:
                raise Exception("Bad login attempt")
        con.close()

        user_store_path = self.storage_dir_path.joinpath(u["user_store"])
        user_secret = password.encode()

        # An in-memory SQLite database that can be regularly serialised
        u_con = connect(":memory:")

        # Extract db dump from zip, then close
        with AESZipFile(
            str(user_store_path),
            mode="r", # Read only
            compression=ZIP_LZMA,
            encryption=WZ_AES
            ) as u_zip:
            u_zip.setpassword(user_secret)

            u_con.deserialize(u_zip.read(self.LOCAL_U_WALLET_FILENAME))

        self.active_user = self.ActiveUser(
            username,
            password.encode(),
            user_store_path,
            u_con
            )

    def logout(self):
        """
        TODO
        """
        self.save(close=True)

    def get_credential(self, cred_id: str) -> Credential | DeferredCredential:
        """
        Retrieves credential of given ID

        ### Parameters
        - cred_id(`str`): The ID of the requested credential
        ### Returns
        - (`Credential | DeferredCredential`): The credential, if it exists.
        """
        self._check_active_user()

        check_exists = """
        SELECT id, deferred FROM credential_info
        WHERE id = :c_id
        """
        cursor: Cursor
        with self.active_user.db.execute(check_exists, {"c_id": cred_id}) as cursor:
            c = cursor.fetchone()
            if not c:
                raise Exception(f"Credential {cred_id} not found.")
            if c["deferred"]:
                return self._get_deferred_cred(cred_id)
            return self._get_received_cred(cred_id)

    def _get_received_cred(self, cred_id: str) -> Credential:
        query = self.CREDENTIAL_QUERY + "WHERE c_info.id = :cred_id"
        cursor: Cursor
        with self.active_user.db.execute(query, {"cred_id": cred_id}) as cursor:
            c = cursor.fetchone()
            return Credential.model_validate(c)

    def _get_deferred_cred(self, cred_id: str) -> DeferredCredential:
        query = self.DEFERRED_QUERY + "WHERE c_info.id = :cred_id"
        cursor: Cursor
        with self.active_user.db.execute(query, {"cred_id": cred_id}) as cursor:
            c = cursor.fetchone()
            return DeferredCredential.model_validate(c)

    def get_received_credentials(self) -> list[Credential]:
        """
        Retrieves all non-deferred credentials

        ### Returns
        - (`List[Credentia]l`): A list of credentials
        """
        self._check_active_user()
        query = self.CREDENTIAL_QUERY
        cursor: Cursor
        with self.active_user.db.execute(query) as cursor:
            creds = cursor.fetchall()
            return [Credential.model_validate(c) for c in creds]

    def get_deferred_credentials(self) -> list[DeferredCredential]:
        """
        Retrieves all deferred credentials

        ### Returns
        - (`List[DeferredCredentia]l`): A list of deferred credentials
        """
        self._check_active_user()
        query = self.DEFERRED_QUERY
        cursor: Cursor
        with self.active_user.db.execute(query) as cursor:
            creds = cursor.fetchall()
            return [DeferredCredential.model_validate(c) for c in creds]

    def all_credentials(self) -> list[Credential | DeferredCredential]:
        """
        Retrieves all credentials, deferred or otherwise

        ### Returns
        - (`List[DeferredCredential | Credential]`): A list of the user's credentials
        """
        return self.get_received_credentials().extend(self.get_deferred_credentials())

    def add_credential(self, cred: Credential | DeferredCredential):
        """
        Adds a credential to storage
        """
        self._check_active_user()
        self.save()

    def delete_credential(self, cred: Credential | DeferredCredential):
        """
        Deletes a credential from storage
        """
        self._check_active_user()
        self.save()

    def update_credential(self, cred: Credential | DeferredCredential):
        """
        Updates a credential already in storage.
        """
        self._check_active_user()
        self.save()

    def upsert_credential(self, cred: Credential | DeferredCredential):
        """
        Updates a credential already in storage if it exists, otherwise, adds it.
        """
        self._check_active_user()
        self.save()

    def save(self, *, close=False):
        """
        Performs operations to push data to persistent storage (e.g. flushing to a
        database).
        Implementation specific.
        """
        self.active_user.db.commit()
        self._save_db_to_zip()
        if close:
            self.active_user.db.close()
            del self.active_user
            self.active_user = None


