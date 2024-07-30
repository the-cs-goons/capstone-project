import { createCookieSessionStorage, Session } from "@remix-run/node";

type SessionData = {
  token: string;
};

type SessionFlashData = {
  error: string;
};

const { getSession, commitSession, destroySession } =
  createCookieSessionStorage<SessionData, SessionFlashData>({
    // Basic cookie to wrap around python backend session token
    cookie: {
      name: "_session",
      httpOnly: true,
      secure: true,
      maxAge: 3600, // Effectively a timeout on the user.
    },
  });

const getSessionFromRequest = async (request: Request) => {
  return await getSession(request.headers.get("Cookie"));
};

const authHeaders = (session: Session<SessionData, SessionFlashData>) => {
  const token = session.get("token");
  return { Authorization: `Bearer ${token}` };
};

export { getSession, getSessionFromRequest, commitSession, destroySession, authHeaders };
