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
        Creates a new local storage provider.

        ### Parameters:
        - storage_dir_path(`str | None`): Optionally, a path to a directory to create
        or expect the directory containing wallet data. If provided, this MUST be
        a directory. If not provided, will default to `Path.home()`
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
        # in this file. There are password hashes, but they are salted. All you can
        # achieve by attempting to overwrite these hashes is prevent someone from
        # being able to login.
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

    def get_active_user_name(self) -> str | None:
        """
        Gets the username of the active user, if there is one

        ### Returns
        - `str | None`: `None` if there is no active user, otherwise,
        the active user's username.
        """
        if self.active_user:
            return self.active_user.username
        return None

    def get_db_conn(self) -> Connection:
        """
        Gets the sqlite3 Connection tied to the in-memory database.

        ### Returns
        - `Connection`: a `sqlite3.Connection` tied to an in-memory SQLite database
        """
        if not self.active_user:
            raise Exception("No current user.")
        return self.active_user.db

    def register(self, username: str, password: str):
        """
        Performs the necessary operations associated with 'registering' a new
        wallet/user for this storage implementation:
        - Checks the username is not taken
        - Adds an entry to the configuration file
        - Initialises persistent storage for the new user at a generated path
        - Opens an in-memory database

        ### Parameters:
        - username(`str`): The username being registered
        - password(`str`): The password associated with the registration
        """
        store = uuid4().hex
        config = connect(str(self.config_db_path))
        config.row_factory = Row

        u_secret = password.encode()

        # Storing a hash isn't actually necessary for how this storage mechanism
        # works, but it makes error handling on a bad login attempt easier.
        hash = self._pwd_hasher.hash(u_secret)

        new_user = {
            "username": username,
            "pwd": hash,
            "store": store
            }

        # Add an entry to config.db
        cursor = config.execute(
            """
            INSERT INTO users VALUES (:username, :pwd, :store)
            RETURNING username, user_store
            """,
            new_user)
        u = cursor.fetchone()
        cursor.close()

        # Make sure all steps succeed before comitting new user
        try:
            user_store_path = self.storage_dir_path.joinpath(u["user_store"])

            # An in-memory SQLite database that can be regularly serialised
            u_con = connect(":memory:")
            u_con.row_factory = dict_factory

            # Create tables
            cursor = u_con.executescript(self.LOCAL_CREDENTIAL_SCHEMA)
            cursor.close()

            # Commit
            u_con.commit()

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
        except Exception:
            config.rollback()
            raise Exception("Registration failed")
        finally:
            config.close()

        self.active_user = self.ActiveUser(
            u["username"],
            u_secret,
            user_store_path,
            u_con
            )

    def login(self, username: str, password: str):
        """
        Performs the necessary operations associated with 'logging in' to a
        wallet as a user for this storage implementation:
        - Checks the argon2 hash of the given password in config.db
        - If verified, attempts to use the given password to decrypt from
        storage.

        ### Parameters:
        - username(`str`): The username being logged into
        - password(`str`): The password used to try log in
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
        Performs the necessary operations associated with 'logging out' a
        user and locking their wallet for this storage implementation:
        - Saves the in-memory SQLite database to disk in a ZIP archive
        - Closes & destroys the in-memory database
        - Clears the active user
        """
        self.save(close_after=True)
        del self.active_user
        self.active_user = None

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
        with self.get_db_conn().execute(check_exists, {"c_id": cred_id}) as cursor:
            c = cursor.fetchone()
            if not c:
                raise Exception(f"Credential {cred_id} not found.")
            if c["deferred"]:
                return self._get_deferred_cred(cred_id)
            return self._get_received_cred(cred_id)

    def _get_received_cred(self, cred_id: str) -> Credential:
        query = self.CREDENTIAL_QUERY + "WHERE c_info.id = :cred_id"
        cursor: Cursor
        with self.get_db_conn().execute(query, {"cred_id": cred_id}) as cursor:
            c = cursor.fetchone()
            return Credential.model_validate(c)

    def _get_deferred_cred(self, cred_id: str) -> DeferredCredential:
        query = self.DEFERRED_QUERY + "WHERE c_info.id = :cred_id"
        cursor: Cursor
        with self.get_db_conn().execute(query, {"cred_id": cred_id}) as cursor:
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
        with self.get_db_conn().execute(query) as cursor:
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
        with self.get_db_conn().execute(query) as cursor:
            creds = cursor.fetchall()
            return [DeferredCredential.model_validate(c) for c in creds]

    def all_credentials(self) -> list[Credential | DeferredCredential]:
        """
        Retrieves all credentials, deferred or otherwise

        ### Returns
        - (`List[DeferredCredential | Credential]`): A list of the user's credentials
        """
        return self.get_received_credentials().extend(self.get_deferred_credentials())

    def add_credential(
            self,
            cred: Credential | DeferredCredential,
            *,
            save_after=True
            ):
        """
        Adds a credential to storage

        ### Parameters
        - cred(`Credential | DeferredCredential`): The credential to add
        - save_after(`bool = True`): If True (default), will call `save()` on finish.
        """
        self._check_active_user()
        params = cred.model_dump()
        try:
            cursor = self.get_db_conn().execute(
                """
                INSERT INTO credential_info (id, issuer_name, issuer_url, config_id,
                config_name, type, deferred)
                VALUES (:id, :issuer_name, :issuer_url, :credential_configuration_id,
                :credential_configuration_name, :is_deferred, :c_type)
                """,
                params
            )
            if isinstance(cred, Credential):
                cursor.execute(
                """
                INSERT INTO credentials (credential_id, raw_vc, received_at)
                VALUES (:id, :raw_sdjwtvc, :received_at)
                """,
                params
                )
            else:
                cursor.execute(
                """
                INSERT INTO deferred_credentials (credential_id, tx_id,
                deferred_endpoint, last_request, access_token)
                VALUES (:id, :transaction_id, :deferred_credential_endpoint,
                :last_request, :access_token)
                """,
                params
                )
        except Exception as e:
            self.get_db_conn().rollback()
            raise Exception(f"Credential could not be added: {e}")
        finally:
            cursor.close()
        if save_after:
            self.save()

    def delete_credential(
            self,
            cred_id: str,
            *,
            save_after=True
            ):
        """
        Deletes a credential from storage

        ### Parameters
        - cred_id(`str`): The ID of the credential to delete.
        - save_after(`bool = True`): If True (default), will call `save()` on finish.
        """
        self._check_active_user()
        # Other tables will be handled thanks to CASCADE
        cursor = self.get_db_conn().execute(
            "DELETE FROM credential_info WHERE credential_id = :cred_id",
            {"cred_id": cred_id}
            )
        cursor.close()
        if save_after:
            self.save()

    def update_credential(
            self,
            cred: Credential | DeferredCredential,
            *,
            save_after=True
            ):
        """
        Updates a credential already in storage.
        Handles updating a previously deferred credential, the credential
        passed MUST not have an altered ID.

        ### Parameters
        - cred(`Credential | DeferredCredential`): The credential to update.
        - save_after(`bool = True`): If True (default), will call `save()` on finish.
        """
        self._check_active_user()
        params = cred.model_dump()

        check_prev = """
        SELECT id, deferred FROM credential_info
        WHERE id = :id
        """
        cursor = self.get_db_conn().execute(check_prev, {"c_id": params})
        was_deferred = cursor.fetchone()["deferred"]

        # This is a complex-ish set of operations, so if one fails, we can
        # roll back the changes made.
        try:
            # Because of foreign key constraints, the credential/deferred
            # tables need to be updated first.
            if was_deferred:
                # Before calling update, this credential was deferred
                if cred.is_deferred:
                    # This credential is still deferred.
                    # The transaction ID wouldn't change. Last request
                    # definitely will, the other two might in a real-world
                    # scenario.
                    cursor.execute(
                    """
                    UPDATE deferred_credentials
                    SET deferred_endpoint = :deferred_credential_endpoint
                        last_request = :last_request,
                        access_token = :access_token
                    WHERE credential_id = :id
                    """,
                    params
                    )
                else:
                    # This credential was deferred but has just been received.
                    # Delete the deferred credential records for this credential
                    cursor.execute(
                    "DELETE FROM deferred_credentials WHERE credential_id = :cred_id",
                    {"cred_id": cred.id}
                    )
                    # Populate the recieved credential table
                    cursor.execute(
                    """
                    INSERT INTO credentials (credential_id, raw_vc, received_at)
                    VALUES (:id, :raw_sdjwtvc, :received_at)
                    """,
                    params
                    )
            else:
                # The credential was received previously.
                # In our implementation as is, the VC should not change, but
                # in THEORY an issuer might support refreshing or renewing
                # credentials.
                cursor.execute(
                    """
                    UPDATE credentials
                    SET raw_vc = :raw_sdjwtvc,
                        received_at = :received_at
                    WHERE credential_id = :id
                    """,
                    params
                    )

            # Perform rest of the update.
            cursor.execute(
                """
                UPDATE credential_info
                SET issuer_name = :issuer_name,
                    issuer_url = :issuer_url,
                    config_id = :credential_configuration_id,
                    config_name = :credential_configuration_name
                    deferred = :is_deferred
                    type = :c_type
                WHERE id = :id
                """,
                params
            )
        except Exception as e:
            # Roll back if something went awry along the way.
            self.get_db_conn().rollback()
            raise Exception(f"Credential {cred.id} could not be updated: {e}")
        cursor.close()
        if save_after:
            self.save()

    def upsert_credential(
            self,
            cred: Credential | DeferredCredential,
            *,
            save_after=True
            ):
        """
        Updates OR adds a credential, depending on if it is already in storage
        or not.

        ### Parameters
        - cred(`Credential | DeferredCredential`): The credential to add or update
        - save_after(`bool = True`): If True (default), will call `save()` on finish.
        """
        self._check_active_user()

        check_exists = """
        SELECT id, deferred FROM credential_info
        WHERE id = :c_id
        """
        cursor: Cursor
        with self.get_db_conn().execute(check_exists, {"c_id": cred.id}) as cursor:
            exists = cursor.fetchone()
            if not exists:
                self.add_credential(cred, save_after)
            else:
                self.update_credential(cred, save_after)

    # Most of these 'many' methods could be optomised if we have time.
    # They're being provided like this so that file I/O operations
    # can be reduced.

    def add_many(
            self,
            creds: list[Credential | DeferredCredential],
            *,
            save_after=True
            ):
        """
        Adds many credentials to storage

        ### Parameters
        - creds(`list[Credential | DeferredCredential]`): The credentials to add
        - save_after(`bool = True`): If True (default), will call `save()` on finish.
        """
        try:
            [self.add_credential(c, save_after=False) for c in creds]
        except Exception as e:
            self.get_db_conn().rollback()
            raise e
        if save_after:
            self.save()

    def delete_many(
            self,
            cred_ids: list[str],
            *,
            save_after=True
            ):
        """
        Deletes selected credentials from storage, by IDs

        ### Parameters
        - cred_ids(`List[str]`): The IDs of the credentials to delete.
        - save_after(`bool = True`): If True (default), will call `save()` on finish.
        """
        try:
            self.get_db_conn().executemany(
            "DELETE FROM credential_info WHERE credential_id = :cred_id",
            tuple([(c_id,) for c_id in cred_ids])
            )
        except Exception as e:
            self.get_db_conn().rollback()
            raise Exception(f"Problem when deleting credentials: {e}")

        if save_after:
            self.save()

    def update_many(
            self,
            creds: list[Credential | DeferredCredential],
            *,
            save_after=True
            ):
        """
        Update many credentials.

        ### Parameters
        - creds(`list[Credential | DeferredCredential]`): The credentials to add
        - save_after(`bool = True`): If True (default), will call `save()` on finish.
        """
        try:
            [self.update_credential(c, save_after=False) for c in creds]
        except Exception as e:
            self.get_db_conn().rollback()
            raise e
        if save_after:
            self.save()

    def upsert_many(
            self,
            creds: list[Credential | DeferredCredential],
            *,
            save_after=True
            ):
        """
        Update or add many credentials to storage

        ### Parameters
        - creds(`list[Credential | DeferredCredential]`): Credentials to add or update
        - save_after(`bool = True`): If True (default), will call `save()` on finish.
        """
        try:
            [self.upsert_credential(c, save_after=False) for c in creds]
        except Exception as e:
            self.get_db_conn().rollback()
            raise e
        if save_after:
            self.save()

    def save(self, *, to_disk=True, close_after=False):
        """
        Performs operations to push data to persistent storage (e.g. flushing to a
        database).
        Implementation specific.
        """
        self.active_user.db.commit()
        if to_disk:
            self._save_db_to_zip()
        if close_after:
            self.active_user.db.close()


